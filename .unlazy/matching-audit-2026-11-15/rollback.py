import asyncio
import json
import sys
from decimal import Decimal

import src.db_metadata  # noqa: F401
from sqlalchemy import select, text

from src.database import async_session_factory, engine
from src.modules.parser.service.parser_service import CATALOG_WRITE_LOCK_ID
from src.modules.products.model.product import StoreOffer
from src.modules.products.service.matching_service import MatchingService


async def main(snapshot, apply=False):
    before = {row["id"]: row for row in snapshot["before"]["offers"]}
    expected = {row["id"]: row for row in snapshot["after"]["offers"]}
    assert before.keys() == expected.keys() and len(before) == 31
    async with async_session_factory() as db:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": CATALOG_WRITE_LOCK_ID}
        )
        offers = list(
            (
                await db.execute(
                    select(StoreOffer)
                    .where(StoreOffer.id.in_(before))
                    .with_for_update()
                )
            ).scalars()
        )
        assert len(offers) == len(before)
        for offer in offers:
            for key, value in expected[offer.id].items():
                current = getattr(offer, key)
                if key == "match_confidence" and current is not None and value is not None:
                    current, value = Decimal(str(current)), Decimal(str(value))
                assert current == value, (offer.id, key, "changed since repair")
        if apply:
            for offer in offers:
                original = before[offer.id]
                offer.product_id = original["product_id"]
                offer.match_status = original["match_status"]
                confidence = original["match_confidence"]
                offer.match_confidence = (
                    Decimal(confidence) if confidence is not None else None
                )
            await db.flush()
            await MatchingService.recalc_cluster_aggregates(db)
            await db.commit()
        else:
            await db.rollback()
        print("restored" if apply else "rollback guards passed", len(offers))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(json.load(open(sys.argv[1])), "--apply" in sys.argv[2:]))
