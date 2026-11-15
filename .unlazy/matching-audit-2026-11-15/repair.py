import asyncio
import json
import sys

import src.db_metadata  # noqa: F401
from sqlalchemy import select, text

from src.database import async_session_factory, engine
from src.modules.catalog.service.dictionaries import load_dictionaries
from src.modules.catalog.service.extractor import extract
from src.modules.parser.service.parser_service import CATALOG_WRITE_LOCK_ID
from src.modules.products.model.product import MatchCandidate, StoreOffer
from src.modules.products.service.matching_service import MatchingService


def offer_state(offer):
    return {
        key: getattr(offer, key)
        for key in (
            "id",
            "title",
            "url",
            "product_id",
            "match_status",
            "match_confidence",
            "is_active",
        )
    }


def candidate_state(candidate):
    return {
        key: getattr(candidate, key)
        for key in (
            "id",
            "offer_id",
            "product_id",
            "status",
            "score",
            "features",
            "decided_by",
            "decided_at",
        )
    }


async def main(manifest):
    expected = {row["offer_id"]: row for row in manifest["issues"]}
    assert len(expected) == 31
    async with async_session_factory() as db:
        await db.execute(text("SET LOCAL lock_timeout = '30s'"))
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": CATALOG_WRITE_LOCK_ID}
        )
        offers = list(
            (
                await db.execute(
                    select(StoreOffer)
                    .where(StoreOffer.id.in_(expected))
                    .order_by(StoreOffer.id)
                    .with_for_update()
                )
            ).scalars()
        )
        assert len(offers) == len(expected)
        dictionaries = await load_dictionaries(db)
        for offer in offers:
            prior = expected[offer.id]
            assert offer.match_status == prior["status"] == "auto", offer.id
            assert offer.product_id == prior["product_id"], offer.id
            assert offer.title == prior["title"] and offer.url == prior["url"], offer.id
            assert offer.is_active, offer.id
            attrs = extract(offer.title, dictionaries)
            assert attrs.device_id is None and attrs.part_type_id is not None, offer.id
        candidates = list(
            (
                await db.execute(
                    select(MatchCandidate)
                    .where(MatchCandidate.offer_id.in_(expected))
                    .order_by(MatchCandidate.id)
                )
            ).scalars()
        )
        before_candidates = [candidate_state(row) for row in candidates]
        before = [offer_state(offer) for offer in offers]
        print(
            "BEFORE:"
            + json.dumps(
                {"offers": before, "candidates": before_candidates},
                default=str,
                ensure_ascii=False,
            ),
            flush=True,
        )
        for offer in offers:
            await MatchingService.match_offer(db, offer, dictionaries)
            assert offer.product_id is None and offer.match_status == "review", offer.id
        await MatchingService.recalc_cluster_aggregates(db)
        after = [offer_state(offer) for offer in offers]
        assert [candidate_state(row) for row in candidates] == before_candidates
        await db.commit()
        print(
            "AFTER:"
            + json.dumps(
                {"offers": after, "candidates": before_candidates},
                default=str,
                ensure_ascii=False,
            ),
            flush=True,
        )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(json.load(open(sys.argv[1]))))
