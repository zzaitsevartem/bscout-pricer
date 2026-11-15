import asyncio
import json
import sys

import src.db_metadata  # noqa: F401
from sqlalchemy import select, text

from src.database import async_session_factory, engine
from src.modules.parser.service.parser_service import CATALOG_WRITE_LOCK_ID
from src.modules.products.model.product import MatchCandidate, Product, StoreOffer
from src.modules.products.service.matching_service import MatchingService


async def main(reviewed):
    expected = {r["candidate_id"]: r for r in reviewed}
    assert len(expected) == 113
    async with async_session_factory() as db:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": CATALOG_WRITE_LOCK_ID}
        )
        rows = (
            await db.execute(
                select(MatchCandidate, StoreOffer)
                .join(StoreOffer, StoreOffer.id == MatchCandidate.offer_id)
                .where(MatchCandidate.id.in_(expected))
                .order_by(MatchCandidate.id)
                .with_for_update()
            )
        ).all()
        assert len(rows) == len(expected)
        before = []
        for candidate, offer in rows:
            ref = expected[candidate.id]
            assert (
                candidate.status == "pending"
                and candidate.decided_by is None
                and candidate.decided_at is None
            )
            assert (
                candidate.product_id == ref["product_id"]
                and offer.id == ref["offer_id"]
            )
            assert (
                offer.title == ref["title"]
                and offer.url == ref["url"]
                and offer.is_active
            )
            assert offer.product_id is None and offer.match_status not in (
                "manual",
                "rejected",
            )
            assert not (
                await db.execute(
                    select(Product.id).where(
                        Product.canonical_key == f"review-offer|{offer.id}"
                    )
                )
            ).first()
            before.append(
                {
                    "candidate_id": candidate.id,
                    "candidate_product_id": candidate.product_id,
                    "offer_id": offer.id,
                    "product_id": offer.product_id,
                    "status": offer.match_status,
                    "confidence": str(offer.match_confidence)
                    if offer.match_confidence is not None
                    else None,
                    "title": offer.title,
                    "url": offer.url,
                }
            )
        print("BEFORE:" + json.dumps(before, ensure_ascii=False), flush=True)
        after = []
        for candidate, offer in rows:
            product = Product(
                canonical_key=f"review-offer|{offer.id}",
                canonical_name=offer.title,
                key_attrs={"review_offer_id": offer.id},
            )
            db.add(product)
            await db.flush()
            offer.product_id = product.id
            offer.match_status = "review"
            offer.match_confidence = None
            candidate.status = "superseded"
            after.append(
                {
                    "candidate_id": candidate.id,
                    "offer_id": offer.id,
                    "product_id": product.id,
                }
            )
        await db.flush()
        await MatchingService.recalc_cluster_aggregates(db)
        await db.commit()
        print("AFTER:" + json.dumps(after, ensure_ascii=False), flush=True)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(json.load(open(sys.argv[1]))))
