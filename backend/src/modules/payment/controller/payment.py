import json
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db
from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.auth.service.email_verification_service import require_verified_email
from src.modules.payment.model.payment import Payment
from src.modules.payment.schema.payment import (
    PaymentCreateRequest,
    PaymentQuote,
    PaymentResponse,
    PlanResponse,
    SubscriptionCancelResponse,
    WebhookAck,
    WebhookEvent,
)
from src.modules.payment.service import yookassa
from src.modules.payment.service.payment_service import (
    CANCELED,
    FAILED,
    PENDING,
    SUCCEEDED,
    PaymentService,
)
from src.modules.payment.service.plans import PLANS, price_for
from src.modules.payment.service.yookassa import YooKassaError, YooKassaPaymentRejected
from src.modules.shared import get_current_user
from src.modules.shared.deps import get_current_admin

router = APIRouter(prefix="/api/payment", tags=["payment"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans():
    return [
        PlanResponse(
            plan=definition.plan,
            name_ru=definition.name_ru,
            price=definition.price,
            first_payment_price=price_for(definition.plan, first_payment=True),
            duration_days=definition.duration_days,
            tracked_products=definition.tracked_products,
            stores=definition.stores,
            fuzzy_search=definition.fuzzy_search,
            price_alerts=definition.price_alerts,
            device_tracking=definition.device_tracking,
            export_reports=definition.export_reports,
            support_ru=definition.support_ru,
            featured=definition.featured,
            sort_order=definition.sort_order,
        )
        for definition in sorted(PLANS.values(), key=lambda item: item.sort_order)
    ]


def require_paid_plan(plan: PlanEnum) -> None:
    if plan == PlanEnum.trial:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пробный тариф бесплатный и не оплачивается через этот эндпоинт",
        )


@router.get("/quote", response_model=PaymentQuote)
async def quote_payment(
    plan: PlanEnum,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_paid_plan(plan)
    quote, _ = await PaymentService.quote(db, current_user.id, plan)
    return quote


@router.post(
    "/subscribe",
    dependencies=[Depends(require_verified_email)],
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe(
    body: PaymentCreateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_paid_plan(body.plan)
    await PaymentService.lock_user(db, current_user.id)
    idempotence_key = PaymentService.build_idempotence_key(
        current_user.id, body.plan, body.idempotence_key
    )
    payment = await PaymentService.get_payment_by_key(db, current_user.id, idempotence_key)
    if payment is None:
        payment = await PaymentService.pending_payment(db, current_user.id)
    created = payment is None
    if payment is None:
        quote, upgrade_days = await PaymentService.quote(db, current_user.id, body.plan)
        if body.expected_amount is not None and body.expected_amount != quote.amount:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Сумма изменилась. Получите актуальный расчёт и подтвердите его.",
            )
        payment = await PaymentService.create_pending_payment(
            db,
            user_id=current_user.id,
            plan=body.plan,
            idempotence_key=idempotence_key,
            amount=quote.amount,
            upgrade_days=upgrade_days,
        )
    if payment.plan != body.plan or (
        body.expected_amount is not None and body.expected_amount != payment.amount
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="У вас уже есть платёж с другими условиями. Проверьте историю платежей.",
        )

    payment_id = payment.id
    await db.commit()
    if payment.status == PENDING and yookassa.is_configured():
        payment = await PaymentService.lock_payment(db, payment_id)
        if payment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        try:
            await PaymentService.attach_provider_payment(
                db,
                payment,
                idempotence_key=payment.idempotence_key,
                return_url=f"{settings.frontend_base_url}/subscription",
            )
        except YooKassaError as exc:
            if isinstance(exc, YooKassaPaymentRejected):
                await PaymentService.mark_status(db, payment, FAILED)
                await db.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Платёжный провайдер недоступен, попробуйте позже",
            ) from None
        await db.commit()
    if not created:
        response.status_code = status.HTTP_200_OK
    return payment


@router.get("/history", response_model=list[PaymentResponse])
async def payment_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await PaymentService.list_payments(db, current_user.id)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    payment = await db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    await PaymentService.lock_user(db, payment.user_id)
    payment = await PaymentService.lock_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.status != PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Платёж уже обработан: status={payment.status}",
        )

    await PaymentService.mark_paid(db, payment)
    await db.commit()
    return payment


@router.post("/webhook", response_model=WebhookAck)
async def provider_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not yookassa.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Проверка уведомлений не настроена: задайте реквизиты мерчанта",
        )

    raw_body = await request.body()
    try:
        payload = json.loads(raw_body or b"{}")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed webhook payload"
        ) from None
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed webhook payload"
        )

    event = WebhookEvent.model_validate(payload)
    obj = event.object or {}
    metadata = obj.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    provider_payment_id = obj.get("id")
    idempotence_key = metadata.get("idempotence_key") or payload.get("idempotence_key")

    payment = await PaymentService.find_payment_by_reference(
        db,
        provider_payment_id=str(provider_payment_id) if provider_payment_id else None,
        idempotence_key=str(idempotence_key) if idempotence_key else None,
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    provider_reference = payment.provider_payment_id or provider_payment_id
    if not isinstance(provider_reference, str) or not re.fullmatch(
        r"[a-zA-Z0-9_-]{1,255}", provider_reference
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    try:
        remote = await yookassa.get_payment(provider_reference)
    except YooKassaError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Платёжный провайдер недоступен, попробуйте позже",
        ) from None

    if str(remote.get("id")) != provider_reference:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Provider object mismatch")
    if not payment.provider_payment_id:
        remote_metadata = remote.get("metadata")
        if (
            not isinstance(remote_metadata, dict)
            or remote_metadata.get("idempotence_key") != payment.idempotence_key
            or remote_metadata.get("payment_id") != str(payment.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Provider metadata mismatch"
            )
    remote_amount = remote.get("amount") if isinstance(remote.get("amount"), dict) else {}
    if (
        remote_amount.get("value") != f"{payment.amount:.2f}"
        or remote_amount.get("currency") != payment.currency
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Provider amount mismatch")

    remote_status = str(remote.get("status") or "").lower()
    if remote_status not in (SUCCEEDED, CANCELED, FAILED):
        return WebhookAck(detail="ignored", payment_id=payment.id, status=payment.status)

    await PaymentService.lock_user(db, payment.user_id)
    payment = await PaymentService.lock_payment(db, payment.id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    if payment.provider_payment_id not in (None, provider_reference):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Provider object mismatch")
    if payment.status != PENDING:
        return WebhookAck(detail="already applied", payment_id=payment.id, status=payment.status)
    payment.provider = yookassa.YOOKASSA_PROVIDER
    payment.provider_payment_id = provider_reference
    if remote_status == SUCCEEDED:
        await PaymentService.mark_paid(db, payment, raw=payload)
    else:
        await PaymentService.mark_status(db, payment, remote_status, raw=payload)
    await db.commit()
    return WebhookAck(detail="applied", payment_id=payment.id, status=payment.status)


@router.post("/cancel", response_model=SubscriptionCancelResponse)
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await PaymentService.lock_user(db, current_user.id)
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.is_active.is_(True),
            Subscription.start_date <= func.statement_timestamp(),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    await PaymentService.cancel_subscription(db, subscription)

    return SubscriptionCancelResponse(
        detail="Доступ сохраняется до конца оплаченного периода",
        subscription_id=subscription.id,
        plan=subscription.plan,
        is_active=subscription.is_active,
        auto_renew=subscription.auto_renew,
        end_date=subscription.end_date,
        access_until=subscription.end_date,
    )
