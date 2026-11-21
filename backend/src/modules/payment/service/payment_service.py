import hashlib
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from math import ceil
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.model.user import PlanEnum, Subscription, User
from src.modules.payment.model.payment import Payment
from src.modules.payment.schema.payment import PaymentQuote
from src.modules.payment.service import yookassa
from src.modules.payment.service.plans import PLANS, get_plan, price_for

PENDING = "pending"
SUCCEEDED = "succeeded"
CANCELED = "canceled"
FAILED = "failed"
REFUNDED = "refunded"

DEFAULT_CURRENCY = "RUB"
DEFAULT_PROVIDER = "manual"


class PaymentService:
    PLAN_PRICES: dict[PlanEnum, Decimal] = {
        plan: definition.price for plan, definition in PLANS.items()
    }

    @staticmethod
    def build_idempotence_key(user_id: int, plan: PlanEnum, raw_key: str | None = None) -> str:
        normalized = (raw_key or "").strip()
        if normalized:
            seed = f"user:{user_id}:key:{normalized}"
        else:
            seed = f"user:{user_id}:plan:{plan.value}:attempt:{uuid4()}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    @staticmethod
    def describe(plan: PlanEnum, upgrade_days: int | None = None) -> str:
        definition = get_plan(plan)
        if upgrade_days is not None:
            return f"Переход на тариф BScout «{definition.name_ru}» до конца оплаченного периода"
        return f"Подписка BScout «{definition.name_ru}» на {definition.duration_days} дн."

    @staticmethod
    async def lock_user(db: AsyncSession, user_id: int) -> None:
        await db.execute(select(User.id).where(User.id == user_id).with_for_update(key_share=True))

    @staticmethod
    async def lock_payment(db: AsyncSession, payment_id: int) -> Payment | None:
        return await db.get(Payment, payment_id, with_for_update=True, populate_existing=True)

    @staticmethod
    async def has_successful_payment(db: AsyncSession, user_id: int) -> bool:
        result = await db.execute(
            select(func.count())
            .select_from(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.status == SUCCEEDED,
                Payment.amount > 0,
            )
        )
        return (result.scalar() or 0) > 0

    @staticmethod
    async def quote(
        db: AsyncSession, user_id: int, plan: PlanEnum
    ) -> tuple[PaymentQuote, int | None]:
        now = datetime.now(timezone.utc)
        periods = await PaymentService.paid_periods(db, user_id, now)
        current = periods[0] if periods and periods[0].start_date <= now else None
        if current and current.plan == PlanEnum.basic and plan == PlanEnum.advanced:
            basic, advanced = get_plan(PlanEnum.basic), get_plan(PlanEnum.advanced)
            days = ceil((current.end_date - now) / timedelta(days=1))
            amount = ((advanced.price - basic.price) * days / basic.duration_days).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            return PaymentQuote(amount=amount, ends_at=current.end_date), days

        starts_at = periods[-1].end_date if periods else None
        ends_at = starts_at + timedelta(days=get_plan(plan).duration_days) if starts_at else None
        first_payment = not await PaymentService.has_successful_payment(db, user_id)
        return PaymentQuote(
            amount=price_for(plan, first_payment=first_payment),
            starts_at=starts_at,
            ends_at=ends_at,
        ), None

    @staticmethod
    async def paid_periods(db: AsyncSession, user_id: int, now: datetime) -> list[Subscription]:
        result = await db.scalars(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.plan != PlanEnum.trial,
                Subscription.is_active.is_(True),
                Subscription.end_date > now,
            )
            .order_by(Subscription.start_date, Subscription.id)
            .execution_options(populate_existing=True)
        )
        return list(result)

    @staticmethod
    async def get_payment_by_key(
        db: AsyncSession, user_id: int, idempotence_key: str
    ) -> Payment | None:
        result = await db.execute(
            select(Payment).where(
                Payment.user_id == user_id,
                Payment.idempotence_key == idempotence_key,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_payment_by_reference(
        db: AsyncSession,
        provider_payment_id: str | None = None,
        idempotence_key: str | None = None,
    ) -> Payment | None:
        if provider_payment_id:
            payment = await db.scalar(
                select(Payment).where(Payment.provider_payment_id == provider_payment_id)
            )
            if payment is not None:
                return payment
        if idempotence_key:
            payment = await db.scalar(
                select(Payment).where(Payment.idempotence_key == idempotence_key)
            )
            if not provider_payment_id or (payment and not payment.provider_payment_id):
                return payment
        return None

    @staticmethod
    async def pending_payment(db: AsyncSession, user_id: int) -> Payment | None:
        return await db.scalar(
            select(Payment)
            .where(Payment.user_id == user_id, Payment.status == PENDING)
            .order_by(Payment.id.desc())
            .limit(1)
        )

    @staticmethod
    async def create_pending_payment(
        db: AsyncSession,
        user_id: int,
        plan: PlanEnum,
        idempotence_key: str,
        amount: Decimal,
        provider: str = DEFAULT_PROVIDER,
        confirmation_url: str | None = None,
        upgrade_days: int | None = None,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            plan=plan,
            amount=amount,
            currency=DEFAULT_CURRENCY,
            status=PENDING,
            provider=provider,
            idempotence_key=idempotence_key,
            description=PaymentService.describe(plan, upgrade_days),
            confirmation_url=confirmation_url,
            upgrade_days=upgrade_days,
        )
        db.add(payment)
        await db.flush()
        return payment

    @staticmethod
    async def attach_provider_payment(
        db: AsyncSession,
        payment: Payment,
        idempotence_key: str,
        return_url: str,
    ) -> Payment:
        if payment.status != PENDING:
            return payment
        if payment.provider != DEFAULT_PROVIDER or payment.confirmation_url:
            return payment
        if not yookassa.is_configured():
            return payment
        if datetime.now(timezone.utc) - payment.created_at >= yookassa.IDEMPOTENCE_WINDOW:
            return payment
        provider_id, confirmation_url = await yookassa.create_payment(
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description or PaymentService.describe(payment.plan),
            return_url=return_url,
            idempotence_key=idempotence_key,
            metadata={"payment_id": str(payment.id), "idempotence_key": idempotence_key},
        )
        payment.provider = yookassa.YOOKASSA_PROVIDER
        payment.provider_payment_id = provider_id
        payment.confirmation_url = confirmation_url
        await db.flush()
        return payment

    @staticmethod
    async def mark_paid(
        db: AsyncSession,
        payment: Payment,
        raw: dict | None = None,
    ) -> Payment:
        if payment.status != PENDING:
            return payment

        payment.status = SUCCEEDED
        payment.paid_at = datetime.now(timezone.utc)
        if raw is not None:
            payment.raw = raw

        subscription = await PaymentService.apply_paid_period(db, payment)
        payment.subscription_id = subscription.id
        await db.flush()
        return payment

    @staticmethod
    async def mark_status(
        db: AsyncSession,
        payment: Payment,
        new_status: str,
        raw: dict | None = None,
    ) -> Payment:
        payment.status = new_status
        if raw is not None:
            payment.raw = raw
        await db.flush()
        return payment

    @staticmethod
    async def list_payments(db: AsyncSession, user_id: int) -> list[Payment]:
        result = await db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def apply_paid_period(db: AsyncSession, payment: Payment) -> Subscription:
        now = datetime.now(timezone.utc)
        periods = await PaymentService.paid_periods(db, payment.user_id, now)
        current = periods[0] if periods and periods[0].start_date <= now else None
        if payment.upgrade_days is not None and current and current.plan == PlanEnum.basic:
            current.is_active = False
            return await PaymentService.store_period(
                db, payment.user_id, payment.plan, now, current.end_date
            )

        days = payment.upgrade_days or get_plan(payment.plan).duration_days
        if not periods:
            return await PaymentService.create_subscription(db, payment.user_id, payment.plan, days)
        last = periods[-1]
        end = last.end_date + timedelta(days=days)
        if last.plan == payment.plan:
            last.end_date = end
            return last
        return await PaymentService.store_period(
            db, payment.user_id, payment.plan, last.end_date, end
        )

    @staticmethod
    async def create_subscription(
        db: AsyncSession, user_id: int, plan: PlanEnum, days: int | None = None
    ) -> Subscription:
        now = datetime.now(timezone.utc)
        duration_days = days if days is not None else get_plan(plan).duration_days

        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
        )
        for existing in result.scalars().all():
            existing.is_active = False

        return await PaymentService.store_period(
            db, user_id, plan, now, now + timedelta(days=duration_days)
        )

    @staticmethod
    async def store_period(
        db: AsyncSession, user_id: int, plan: PlanEnum, start: datetime, end: datetime
    ) -> Subscription:
        subscription = Subscription(
            user_id=user_id,
            plan=plan,
            start_date=start,
            end_date=end,
            is_active=True,
            auto_renew=False,
        )
        db.add(subscription)
        await db.flush()
        return subscription

    @staticmethod
    async def cancel_subscription(db: AsyncSession, subscription: Subscription) -> Subscription:
        subscription.auto_renew = False
        end_date = subscription.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        if end_date <= datetime.now(timezone.utc):
            subscription.is_active = False
        await db.flush()
        return subscription
