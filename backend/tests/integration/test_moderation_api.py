from decimal import Decimal

import pytest
from sqlalchemy import select

from src.modules.auth.model.user import User
from src.modules.auth.service.auth import create_access_token, hash_password
from src.modules.catalog.model.catalog import Brand, Device, PartType
from src.modules.parser.service.utils import normalize_name
from src.modules.products.model.product import Cluster, MatchCandidate, Product, StoreOffer
from src.modules.stores.model.store import Store
from tests.integration.test_comparison_api import _auth as _search_auth
from tests.integration.test_comparison_api import _make_user as _make_search_user

pytestmark = pytest.mark.integration

QUEUE_URL = "/api/admin/match-candidates"


@pytest.mark.parametrize("action", ["approve", "reject"])
async def test_bulk_decision_covers_all_pages_and_preserves_decided(client, db_session, action):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    product = await _make_product(db_session, "bulk-product", "Товар")
    candidates = []
    for index in range(23):
        offer = await _make_offer(db_session, store, sku=f"bulk-{index}")
        candidates.append(await _make_candidate(db_session, offer, product))
    decided_offer = await _make_offer(db_session, store, sku="decided")
    decided = await _make_candidate(db_session, decided_offer, product, status="approved")

    response = await client.post(
        f"{QUEUE_URL}/bulk-decision", json={"action": action}, headers=headers
    )

    assert response.status_code == 200
    assert response.json() == {
        "approved": 23 if action == "approve" else 0,
        "rejected": 23 if action == "reject" else 0,
    }
    for candidate in candidates:
        await db_session.refresh(candidate)
        assert candidate.status == ("approved" if action == "approve" else "rejected")
        assert candidate.decided_by is not None
        assert candidate.decided_at is not None
        offer = await db_session.get(StoreOffer, candidate.offer_id)
        assert offer.product_id == (product.id if action == "approve" else None)
    await db_session.refresh(decided)
    assert decided.status == "approved"
    assert decided.decided_at is None
    repeated = await client.post(
        f"{QUEUE_URL}/bulk-decision", json={"action": action}, headers=headers
    )
    assert repeated.json() == {"approved": 0, "rejected": 0}


async def test_bulk_approve_selects_strongest_candidate_for_each_offer(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    weak = await _make_product(db_session, "weak", "Слабый кандидат")
    strong = await _make_product(db_session, "strong", "Сильный кандидат")
    weak_candidate = await _make_candidate(db_session, offer, weak, score="0.5")
    strong_candidate = await _make_candidate(db_session, offer, strong, score="0.79")

    response = await client.post(
        f"{QUEUE_URL}/bulk-decision", json={"action": "approve"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json() == {"approved": 1, "rejected": 1}
    await db_session.refresh(offer)
    await db_session.refresh(weak_candidate)
    await db_session.refresh(strong_candidate)
    assert offer.product_id == strong.id
    assert offer.match_status == "manual"
    assert weak_candidate.status == "rejected"
    assert strong_candidate.status == "approved"


async def test_bulk_decision_requires_admin(client, db_session):
    user = await _make_user(db_session, "bulk-user@example.com", is_admin=False)
    response = await client.post(
        f"{QUEUE_URL}/bulk-decision",
        json={"action": "reject"},
        headers=_auth(create_access_token(user.id)),
    )
    assert response.status_code == 403


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _make_store(db, slug: str = "tgsm", name: str = "ТГСМ") -> Store:
    store = Store(name=name, slug=slug, website_url="https://taggsm.ru", is_active=True)
    db.add(store)
    await db.flush()
    return store


async def _make_user(db, email: str, *, is_admin: bool) -> User:
    user = User(
        email=email,
        password_hash=hash_password("s3cret-pass"),
        full_name="Moderation User",
        is_active=True,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()
    return user


async def _admin(db, email: str = "moderation-admin@example.com") -> User:
    return await _make_user(db, email, is_admin=True)


async def _admin_headers(db, email: str = "moderation-admin@example.com") -> dict[str, str]:
    admin = await _admin(db, email)
    return _auth(create_access_token(admin.id))


async def _make_offer(
    db,
    store: Store,
    *,
    sku: str = "TG-1",
    title: str = "Дисплей iPhone 13 (оригинал)",
    price: str = "4500.00",
    match_status: str = "unmatched",
    product_id: int | None = None,
) -> StoreOffer:
    offer = StoreOffer(
        store_id=store.id,
        source_sku=sku,
        title=title,
        normalized_title=title.lower(),
        price_retail=Decimal(price),
        price_opt=Decimal("3900.00"),
        currency="RUB",
        stock_status="in_stock",
        url=f"https://taggsm.ru/p/{sku}",
        is_active=True,
        match_status=match_status,
        product_id=product_id,
    )
    db.add(offer)
    await db.flush()
    return offer


async def _make_product(db, key: str, name: str) -> Product:
    product = Product(canonical_key=key, canonical_name=name)
    db.add(product)
    await db.flush()
    return product


async def _make_candidate(
    db,
    offer: StoreOffer,
    product: Product,
    *,
    score: str = "0.7000",
    status: str = "pending",
    features: dict | None = None,
) -> MatchCandidate:
    candidate = MatchCandidate(
        offer_id=offer.id,
        product_id=product.id,
        score=Decimal(score),
        features=features if features is not None else {"device": 1.0, "part_type": 1.0},
        status=status,
    )
    db.add(candidate)
    await db.flush()
    return candidate


async def _candidate_by_id(db, candidate_id: int) -> MatchCandidate:
    return (
        await db.execute(select(MatchCandidate).where(MatchCandidate.id == candidate_id))
    ).scalar_one()


async def test_queue_returns_pending_sorted_by_score_with_full_context(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    weak = await _make_product(db_session, "iphone13|display|copy|-", "Дисплей iPhone 13 (копия)")
    strong = await _make_product(
        db_session, "iphone13|display|orig|-", "Дисплей iPhone 13 (оригинал)"
    )
    await _make_candidate(db_session, offer, weak, score="0.5500")
    await _make_candidate(
        db_session, offer, strong, score="0.7900", features={"device": 1.0, "tier": 0.6}
    )

    resp = await client.get(QUEUE_URL, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["per_page"] == 20
    assert [item["score"] for item in body["results"]] == ["0.7900", "0.5500"]

    top = body["results"][0]
    assert top["status"] == "pending"
    assert top["product_id"] == strong.id
    assert top["features"] == {"device": 1.0, "tier": 0.6}
    assert top["decided_by"] is None
    assert top["decided_at"] is None
    assert top["offer"]["id"] == offer.id
    assert top["offer"]["title"] == "Дисплей iPhone 13 (оригинал)"
    assert top["offer"]["price_retail"] == "4500.00"
    assert top["offer"]["price_opt"] == "3900.00"
    assert top["offer"]["match_status"] == "unmatched"
    assert top["offer"]["store"] == {"id": store.id, "name": "ТГСМ", "slug": "tgsm"}
    assert top["product"]["canonical_name"] == "Дисплей iPhone 13 (оригинал)"
    assert top["product"]["canonical_key"] == "iphone13|display|orig|-"


async def test_queue_hides_decided_candidates_by_default(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    product_a = await _make_product(db_session, "key-a", "Товар A")
    product_b = await _make_product(db_session, "key-b", "Товар B")
    await _make_candidate(db_session, offer, product_a, status="approved")
    pending = await _make_candidate(db_session, offer, product_b, status="pending")

    resp = await client.get(QUEUE_URL, headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert [item["id"] for item in body["results"]] == [pending.id]


async def test_queue_filters_by_status_offer_and_product(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer_one = await _make_offer(db_session, store, sku="TG-1")
    offer_two = await _make_offer(db_session, store, sku="TG-2", title="Аккумулятор iPhone 12")
    product_a = await _make_product(db_session, "key-a", "Товар A")
    product_b = await _make_product(db_session, "key-b", "Товар B")
    first = await _make_candidate(db_session, offer_one, product_a, score="0.6000")
    second = await _make_candidate(db_session, offer_two, product_a, score="0.8000")
    third = await _make_candidate(
        db_session, offer_two, product_b, score="0.9000", status="rejected"
    )

    by_offer = await client.get(QUEUE_URL, params={"offer_id": offer_one.id}, headers=headers)
    by_product = await client.get(QUEUE_URL, params={"product_id": product_a.id}, headers=headers)
    rejected = await client.get(QUEUE_URL, params={"status": "rejected"}, headers=headers)
    everything = await client.get(QUEUE_URL, params={"status": "all"}, headers=headers)

    assert [item["id"] for item in by_offer.json()["results"]] == [first.id]
    assert [item["id"] for item in by_product.json()["results"]] == [second.id, first.id]
    assert [item["id"] for item in rejected.json()["results"]] == [third.id]
    assert everything.json()["total"] == 3


async def test_queue_paginates(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    candidates = []
    for index, score in enumerate(["0.9000", "0.8000", "0.7000"]):
        product = await _make_product(db_session, f"key-{index}", f"Товар {index}")
        candidates.append(await _make_candidate(db_session, offer, product, score=score))

    page_one = await client.get(QUEUE_URL, params={"per_page": 2}, headers=headers)
    page_two = await client.get(QUEUE_URL, params={"per_page": 2, "page": 2}, headers=headers)

    assert page_one.json()["total"] == 3
    assert [item["id"] for item in page_one.json()["results"]] == [
        candidates[0].id,
        candidates[1].id,
    ]
    assert page_two.json()["page"] == 2
    assert [item["id"] for item in page_two.json()["results"]] == [candidates[2].id]


async def test_queue_rejects_unknown_status_filter(client, db_session):
    headers = await _admin_headers(db_session)

    resp = await client.get(QUEUE_URL, params={"status": "whatever"}, headers=headers)

    assert resp.status_code == 422


async def test_approve_links_offer_and_closes_competitors(client, db_session):
    store = await _make_store(db_session)
    admin = await _admin(db_session)
    headers = _auth(create_access_token(admin.id))
    offer = await _make_offer(db_session, store)
    winner = await _make_product(db_session, "key-win", "Дисплей iPhone 13 (оригинал)")
    loser = await _make_product(db_session, "key-lose", "Дисплей iPhone 13 (копия)")
    other_offer = await _make_offer(db_session, store, sku="TG-9", title="Другой оффер")
    chosen = await _make_candidate(db_session, offer, winner, score="0.7600")
    rival = await _make_candidate(db_session, offer, loser, score="0.5100")
    untouched = await _make_candidate(db_session, other_offer, loser, score="0.6000")

    resp = await client.post(f"{QUEUE_URL}/{chosen.id}/approve", headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["candidate"]["status"] == "approved"
    assert body["candidate"]["decided_by"] == admin.id
    assert body["candidate"]["decided_at"] is not None
    assert body["offer"] == {
        "id": offer.id,
        "product_id": winner.id,
        "match_status": "manual",
        "match_confidence": "0.7600",
    }
    assert body["rejected_candidate_ids"] == [rival.id]

    assert offer.product_id == winner.id
    assert offer.match_status == "manual"
    assert offer.match_confidence == Decimal("0.7600")
    assert (await _candidate_by_id(db_session, chosen.id)).status == "approved"

    closed = await _candidate_by_id(db_session, rival.id)
    assert closed.status == "rejected"
    assert closed.decided_by == admin.id
    assert closed.decided_at is not None

    assert (await _candidate_by_id(db_session, untouched.id)).status == "pending"
    assert other_offer.match_status == "unmatched"


async def test_admin_can_approve_fuzzy_candidate_when_device_is_not_recognized(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    brand = Brand(name="Fixture", slug="fixture")
    db_session.add(brand)
    await db_session.flush()
    device = Device(brand_id=brand.id, name="Orion A10", model_key="orion-a10")
    part = PartType(code="display", name_ru="Дисплей")
    db_session.add_all([device, part])
    await db_session.flush()
    cluster = Cluster(device_id=device.id, part_type_id=part.id, offers_count=0)
    db_session.add(cluster)
    await db_session.flush()
    product = await _make_product(db_session, "orion-display", "Дисплей Orion A10")
    product.cluster_id = cluster.id
    offer = await _make_offer(
        db_session, store, title="Дисплей для Vega X987", match_status="review"
    )
    candidate = await _make_candidate(db_session, offer, product, features={"fuzzy": "device"})

    queue = await client.get(QUEUE_URL, headers=headers)
    assert queue.status_code == 200, queue.text
    warning = queue.json()["results"][0]["validation_warning"]
    assert warning and "не подтверждает" in warning
    await db_session.refresh(candidate)
    assert candidate.status == "pending" and candidate.decided_by is None
    assert candidate.decided_at is None

    response = await client.post(f"{QUEUE_URL}/{candidate.id}/approve", headers=headers)
    assert response.status_code == 200, response.text
    await db_session.refresh(offer)
    await db_session.refresh(candidate)
    assert offer.product_id == product.id and offer.match_status == "manual"
    assert candidate.status == "approved"


@pytest.mark.parametrize(
    ("title", "canonical", "device_name", "part_code", "part_name"),
    [
        (
            "Дисплей для Orion A10 Q1234 (черный)",
            "Дисплей Orion A10",
            "Orion A10",
            "display",
            "Дисплей",
        ),
        (
            "Аккумулятор для Vega B20 R5678 (белый)",
            "Аккумулятор Vega B20",
            "Vega B20",
            "battery",
            "Аккумулятор",
        ),
    ],
)
async def test_approved_offer_is_found_in_catalog_by_supplier_title(
    client, db_session, title, canonical, device_name, part_code, part_name
):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    _, token = await _make_search_user(db_session)
    brand = Brand(name="Fixture brand", slug="fixture-brand")
    db_session.add(brand)
    await db_session.flush()
    device = Device(brand_id=brand.id, name=device_name, model_key="fixture-device")
    part = PartType(code=part_code, name_ru=part_name)
    db_session.add_all([device, part])
    await db_session.flush()
    cluster = Cluster(device_id=device.id, part_type_id=part.id, offers_count=0)
    db_session.add(cluster)
    await db_session.flush()
    product = await _make_product(db_session, "test-key", canonical)
    product.cluster_id = cluster.id
    device_id, part_id = device.id, part.id
    offer = await _make_offer(db_session, store, title=title, match_status="review")
    offer.normalized_title = normalize_name(title)
    assert offer.normalized_title != title.lower()
    candidate = await _make_candidate(db_session, offer, product)
    product_id, offer_id, candidate_id = product.id, offer.id, candidate.id

    pending = await client.get(QUEUE_URL, headers=headers)
    assert pending.status_code == 200, pending.text
    assert pending.json()["results"][0]["validation_warning"] is None

    response = await client.post(f"{QUEUE_URL}/{candidate_id}/approve", headers=headers)
    assert response.status_code == 200, response.text
    db_session.expire_all()
    assert (await db_session.get(MatchCandidate, candidate_id)).status == "approved"
    assert (await db_session.get(StoreOffer, offer_id)).product_id == product_id
    queue = await client.get(QUEUE_URL, headers=headers)
    assert queue.status_code == 200 and queue.json()["total"] == 0
    for query in (title, canonical):
        result = await client.get(
            "/api/products/catalog", params={"q": query}, headers=_search_auth(token)
        )
        assert result.status_code == 200, result.text
        assert [item["id"] for item in result.json()["results"]] == [product_id]
        assert result.json()["results"][0]["source"]["offer_id"] == offer_id
        assert result.json()["results"][0]["source"]["url"] == offer.url
        facets = await client.get(
            "/api/products/catalog/facets", params={"q": query}, headers=_search_auth(token)
        )
        assert facets.status_code == 200, facets.text
        assert facets.json()["total"] == 1
        assert [item["id"] for item in facets.json()["devices"]] == [device_id]
        assert [item["id"] for item in facets.json()["part_types"]] == [part_id]


async def test_catalog_title_search_uses_only_eligible_linked_offers(client, db_session):
    store_a = await _make_store(db_session, slug="store-a", name="A")
    store_b = await _make_store(db_session, slug="store-b", name="B")
    _, token = await _make_search_user(db_session)
    product = await _make_product(db_session, "product-one", "Дисплей Orion A10")
    other_product = await _make_product(db_session, "product-two", "Аккумулятор Vega B20")
    await _make_offer(
        db_session, store_a, sku="a", title="Дисплей Orion A10", product_id=product.id
    )
    matching = await _make_offer(
        db_session,
        store_b,
        sku="b",
        title="Дисплей для Orion A10 Q1234 (черный)",
        product_id=product.id,
    )
    matching.stock_status = "out"
    inactive = await _make_offer(
        db_session,
        store_a,
        sku="c",
        title="Дисплей для Orion A10 Q9999",
        product_id=product.id,
    )
    inactive.is_active = False
    await _make_offer(db_session, store_a, sku="d", title="Дисплей для Orion A10 Q8888")
    await _make_offer(
        db_session,
        store_a,
        sku="e",
        title="Аккумулятор Vega B20 Q7777",
        product_id=other_product.id,
    )
    await db_session.flush()

    for params in (
        {"q": "Q1234", "store": "store-a"},
        {"q": "Q1234", "in_stock": "true"},
        {"q": "Q1234", "max_price": 1000},
        {"q": "Q9999"},
        {"q": "Q8888"},
    ):
        response = await client.get(
            "/api/products/catalog", params=params, headers=_search_auth(token)
        )
        assert response.status_code == 200, response.text
        assert response.json()["results"] == []
        facets = await client.get(
            "/api/products/catalog/facets", params=params, headers=_search_auth(token)
        )
        assert facets.status_code == 200, facets.text
        assert facets.json()["total"] == 0
    for query, expected_id in (("Q1234", product.id), ("Q7777", other_product.id)):
        response = await client.get(
            "/api/products/catalog", params={"q": query}, headers=_search_auth(token)
        )
        assert response.status_code == 200, response.text
        assert [item["id"] for item in response.json()["results"]] == [expected_id]


async def test_reject_marks_candidate_and_leaves_offer_untouched(client, db_session):
    store = await _make_store(db_session)
    admin = await _admin(db_session)
    headers = _auth(create_access_token(admin.id))
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    other = await _make_product(db_session, "key-b", "Товар B")
    candidate = await _make_candidate(db_session, offer, product, score="0.6100")
    sibling = await _make_candidate(db_session, offer, other, score="0.5200")

    resp = await client.post(f"{QUEUE_URL}/{candidate.id}/reject", headers=headers)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["candidate"]["status"] == "rejected"
    assert body["candidate"]["decided_by"] == admin.id
    assert body["rejected_candidate_ids"] == []
    assert body["offer"] == {
        "id": offer.id,
        "product_id": None,
        "match_status": "unmatched",
        "match_confidence": None,
    }

    assert offer.product_id is None
    assert offer.match_status == "unmatched"
    assert (await _candidate_by_id(db_session, sibling.id)).status == "pending"


@pytest.mark.parametrize("decision", ["approve", "reject"])
async def test_second_decision_on_same_candidate_returns_409(client, db_session, decision):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    candidate = await _make_candidate(db_session, offer, product)

    first = await client.post(f"{QUEUE_URL}/{candidate.id}/{decision}", headers=headers)
    second = await client.post(f"{QUEUE_URL}/{candidate.id}/approve", headers=headers)
    third = await client.post(f"{QUEUE_URL}/{candidate.id}/reject", headers=headers)

    assert first.status_code == 200, first.text
    assert second.status_code == 409
    assert third.status_code == 409
    assert "already" in second.json()["detail"]


async def test_approve_rejected_competitor_returns_409(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)
    winner = await _make_product(db_session, "key-win", "Товар win")
    loser = await _make_product(db_session, "key-lose", "Товар lose")
    chosen = await _make_candidate(db_session, offer, winner, score="0.8100")
    rival = await _make_candidate(db_session, offer, loser, score="0.5300")

    await client.post(f"{QUEUE_URL}/{chosen.id}/approve", headers=headers)
    resp = await client.post(f"{QUEUE_URL}/{rival.id}/approve", headers=headers)

    assert resp.status_code == 409
    assert offer.product_id == winner.id


@pytest.mark.parametrize("decision", ["approve", "reject"])
async def test_unknown_candidate_returns_404(client, db_session, decision):
    headers = await _admin_headers(db_session)

    resp = await client.post(f"{QUEUE_URL}/424242/{decision}", headers=headers)

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Match candidate not found"


async def test_link_offer_to_product_manually(client, db_session):
    store = await _make_store(db_session)
    admin = await _admin(db_session)
    headers = _auth(create_access_token(admin.id))
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    other = await _make_product(db_session, "key-b", "Товар B")
    pending = await _make_candidate(db_session, offer, other, score="0.6000")

    resp = await client.post(
        f"/api/admin/offers/{offer.id}/link", json={"product_id": product.id}, headers=headers
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["offer"] == {
        "id": offer.id,
        "product_id": product.id,
        "match_status": "manual",
        "match_confidence": "1.0000",
    }
    assert body["rejected_candidate_ids"] == [pending.id]

    assert offer.product_id == product.id
    assert offer.match_status == "manual"
    assert (await _candidate_by_id(db_session, pending.id)).status == "rejected"


async def test_unlink_offer_marks_it_rejected(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    product = await _make_product(db_session, "key-a", "Товар A")
    offer = await _make_offer(db_session, store, match_status="auto", product_id=product.id)
    offer.match_confidence = Decimal("0.9100")
    await db_session.flush()

    resp = await client.post(f"/api/admin/offers/{offer.id}/unlink", headers=headers)

    assert resp.status_code == 200, resp.text
    assert resp.json()["offer"] == {
        "id": offer.id,
        "product_id": None,
        "match_status": "rejected",
        "match_confidence": None,
    }

    assert offer.product_id is None
    assert offer.match_status == "rejected"
    assert offer.match_confidence is None


async def test_link_with_unknown_product_returns_404(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    offer = await _make_offer(db_session, store)

    resp = await client.post(
        f"/api/admin/offers/{offer.id}/link", json={"product_id": 999999}, headers=headers
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Product not found"
    assert offer.product_id is None
    assert offer.match_status == "unmatched"


async def test_link_and_unlink_unknown_offer_return_404(client, db_session):
    headers = await _admin_headers(db_session)
    product = await _make_product(db_session, "key-a", "Товар A")

    link = await client.post(
        "/api/admin/offers/777777/link", json={"product_id": product.id}, headers=headers
    )
    unlink = await client.post("/api/admin/offers/777777/unlink", headers=headers)

    assert link.status_code == 404
    assert link.json()["detail"] == "Offer not found"
    assert unlink.status_code == 404
    assert unlink.json()["detail"] == "Offer not found"


async def test_regular_user_is_forbidden_everywhere(client, db_session):
    store = await _make_store(db_session)
    user = await _make_user(db_session, "plain@example.com", is_admin=False)
    headers = _auth(create_access_token(user.id))
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "key-a", "Товар A")
    candidate = await _make_candidate(db_session, offer, product)

    responses = [
        await client.get(QUEUE_URL, headers=headers),
        await client.post(f"{QUEUE_URL}/{candidate.id}/approve", headers=headers),
        await client.post(f"{QUEUE_URL}/{candidate.id}/reject", headers=headers),
        await client.post(
            f"/api/admin/offers/{offer.id}/link", json={"product_id": product.id}, headers=headers
        ),
        await client.post(f"/api/admin/offers/{offer.id}/unlink", headers=headers),
    ]

    assert [resp.status_code for resp in responses] == [403, 403, 403, 403, 403]
    assert all(resp.json()["detail"] == "Admin access required" for resp in responses)
    assert (await _candidate_by_id(db_session, candidate.id)).status == "pending"
    assert offer.product_id is None
    assert offer.match_status == "unmatched"


async def test_anonymous_requests_are_rejected(client, db_session):
    store = await _make_store(db_session)
    offer = await _make_offer(db_session, store)

    queue = await client.get(QUEUE_URL)
    unlink = await client.post(f"/api/admin/offers/{offer.id}/unlink")

    assert queue.status_code == 403
    assert unlink.status_code == 403
    assert offer.match_status == "unmatched"


async def test_review_offers_endpoint_lists_only_review_status(client, db_session):
    store = await _make_store(db_session)
    headers = await _admin_headers(db_session)
    review = await _make_offer(
        db_session, store, sku="RV-1", title="Дисплей Blackberry Passport", match_status="review"
    )
    await _make_offer(db_session, store, sku="AU-1", match_status="auto")

    resp = await client.get("/api/admin/review-offers", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["results"]) == 1
    item = body["results"][0]
    assert item["id"] == review.id
    assert item["match_status"] == "review"
    assert item["store"]["slug"] == store.slug


async def test_review_offers_endpoint_requires_admin(client, db_session):
    resp = await client.get("/api/admin/review-offers")
    assert resp.status_code == 403


async def test_review_offer_remains_searchable_after_rematch(client, db_session):
    from src.modules.catalog.service.dictionaries import load_dictionaries
    from src.modules.products.service.matching_service import MatchingService

    store = await _make_store(db_session)
    _, token = await _make_search_user(db_session)
    title = "Аккумулятор Vega K40 F8321 (чёрный)"
    offer = await _make_offer(db_session, store, title=title, match_status="review")
    product = await _make_product(db_session, f"review-offer|{offer.id}", title)
    offer.product_id = product.id
    await db_session.flush()
    outcome = await MatchingService.match_offer(
        db_session, offer, await load_dictionaries(db_session)
    )
    assert outcome.status == "review" and offer.product_id == product.id
    response = await client.get(
        "/api/products/catalog", params={"q": title}, headers=_search_auth(token)
    )
    assert response.status_code == 200, response.text
    result = response.json()["results"][0]
    assert result["id"] == product.id and result["source"]["offer_id"] == offer.id
    assert result["source"]["url"] == offer.url
    detail = await client.get(f"/api/products/catalog/{product.id}", headers=_search_auth(token))
    assert detail.status_code == 200, detail.text
    assert [(row["id"], row["url"]) for row in detail.json()["offers"]] == [(offer.id, offer.url)]
    offer.product_id = None
    await db_session.flush()
    response = await client.get(
        "/api/products/catalog", params={"q": title}, headers=_search_auth(token)
    )
    assert response.json()["results"] == []


async def test_rematching_supersedes_obsolete_pending_without_admin_decision(db_session):
    from src.modules.catalog.service.dictionaries import load_dictionaries
    from src.modules.products.service.matching_service import MatchingService

    store = await _make_store(db_session)
    offer = await _make_offer(db_session, store, title="Деталь Vega F8321")
    product = await _make_product(db_session, "obsolete-model", "Другая модель")
    candidate = await _make_candidate(db_session, offer, product)
    await MatchingService.match_offer(db_session, offer, await load_dictionaries(db_session))
    await db_session.refresh(candidate)
    assert candidate.status == "superseded"
    assert candidate.decided_by is None and candidate.decided_at is None
    assert candidate.product_id == product.id


@pytest.mark.parametrize(
    ("status", "expected"), [("superseded", "pending"), ("rejected", "rejected")]
)
async def test_regeneration_preserves_human_rejection(client, db_session, status, expected):
    from src.modules.catalog.service.dictionaries import load_dictionaries
    from src.modules.catalog.service.extractor import extract
    from src.modules.products.service.matching_service import MatchingService

    store = await _make_store(db_session)
    offer = await _make_offer(db_session, store)
    product = await _make_product(db_session, "fixture-product", "Fixture product")
    candidate = await _make_candidate(db_session, offer, product, status=status)
    attrs = extract(offer.title, await load_dictionaries(db_session))
    await MatchingService._ensure_candidate(db_session, offer, product, 0.75, attrs)
    await db_session.refresh(candidate)
    assert candidate.status == expected


async def test_delete_offer_is_admin_only_and_parser_does_not_restore_it(client, db_session):
    from src.modules.parser.service.base import ParseResult, ParserManager
    from src.modules.parser.service.parser_service import ParserService

    store = await _make_store(db_session)
    brand = Brand(name="Delete fixture", slug="delete-fixture")
    db_session.add(brand)
    await db_session.flush()
    device = Device(brand_id=brand.id, name="Fixture", model_key="delete-fixture")
    part = PartType(code="display", name_ru="Дисплей")
    db_session.add_all([device, part])
    await db_session.flush()
    cluster = Cluster(
        device_id=device.id, part_type_id=part.id, offers_count=2, min_price_retail=Decimal("4500")
    )
    db_session.add(cluster)
    await db_session.flush()
    product = await _make_product(db_session, "delete-product", "Товар")
    product.cluster_id = cluster.id
    offer = await _make_offer(db_session, store, match_status="auto", product_id=product.id)
    other = await _make_offer(
        db_session, store, sku="other", price="6000", match_status="manual", product_id=product.id
    )
    user = await _make_user(db_session, "delete-user@example.com", is_admin=False)
    url = f"/api/admin/offers/{offer.id}"
    assert (await client.delete(url)).status_code in (401, 403)
    assert (
        await client.delete(url, headers=_auth(create_access_token(user.id)))
    ).status_code == 403
    response = await client.delete(url, headers=await _admin_headers(db_session))
    assert response.status_code == 200
    await db_session.refresh(offer)
    await db_session.refresh(other)
    await db_session.refresh(cluster)
    assert (cluster.offers_count, cluster.min_price_retail) == (1, Decimal("6000"))
    assert (offer.is_active, offer.match_status, offer.product_id) == (False, "rejected", None)
    assert (other.is_active, other.match_status, other.product_id) == (True, "manual", product.id)
    await ParserService(ParserManager()).upsert_offer(
        db_session,
        store.id,
        ParseResult(
            source_sku=offer.source_sku,
            title=offer.title,
            price_retail=Decimal("123"),
            url=offer.url,
        ),
    )
    await db_session.refresh(offer)
    assert (offer.is_active, offer.match_status, offer.product_id) == (False, "rejected", None)
