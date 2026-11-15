import asyncio
import json
import sys
from decimal import Decimal

import src.db_metadata  # noqa: F401
from sqlalchemy import select, text

from src.database import async_session_factory, engine
from src.modules.parser.service.parser_service import CATALOG_WRITE_LOCK_ID
from src.modules.products.model.product import MatchCandidate, Product, StoreOffer


async def main(snapshot, apply):
    before = {r["candidate_id"]: r for r in snapshot["before"]}
    after = {r["candidate_id"]: r for r in snapshot["after"]}
    assert before.keys() == after.keys() and len(before) == 113
    async with async_session_factory() as db:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": CATALOG_WRITE_LOCK_ID}
        )
        rows = (
            await db.execute(
                select(MatchCandidate, StoreOffer, Product)
                .join(StoreOffer, StoreOffer.id == MatchCandidate.offer_id)
                .join(Product, Product.id == StoreOffer.product_id)
                .where(MatchCandidate.id.in_(before))
                .with_for_update()
            )
        ).all()
        assert len(rows) == len(before)
        for candidate, offer, product in rows:
            ref = before[candidate.id]
            updated = after[candidate.id]
            assert (
                candidate.status == "superseded"
                and candidate.decided_by is None
                and candidate.decided_at is None
            )
            assert candidate.product_id == ref["candidate_product_id"]
            assert (
                offer.id == ref["offer_id"]
                and offer.product_id == updated["product_id"]
            )
            assert offer.match_status == "review" and offer.match_confidence is None
            assert offer.title == ref["title"] and offer.url == ref["url"]
            assert product.canonical_key == f"review-offer|{offer.id}"
        if apply:
            for candidate, offer, _ in rows:
                ref = before[candidate.id]
                candidate.status = "pending"
                offer.product_id = ref["product_id"]
                offer.match_status = ref["status"]
                offer.match_confidence = (
                    Decimal(ref["confidence"])
                    if ref["confidence"] is not None
                    else None
                )
            await db.commit()
        else:
            await db.rollback()
        print("restored" if apply else "rollback guards passed", len(rows))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(json.load(open(sys.argv[1])), "--apply" in sys.argv[2:]))
