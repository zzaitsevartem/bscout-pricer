import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sql(query):
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            "bscout-postgres",
            "psql",
            "-U",
            "bscout",
            "-d",
            "bscout",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
        ],
        input=query,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
parser.add_argument("--restore", type=Path)
args = parser.parse_args()
if args.restore:
    snapshot = json.loads(args.restore.read_text())
    offers_json = json.dumps(snapshot["offers"]).replace("'", "''")
    candidates_json = json.dumps(snapshot["candidates"]).replace("'", "''")
    print(
        sql(f"""BEGIN;
SELECT pg_advisory_xact_lock(72925378991444);
CREATE TEMP TABLE restored_ids ON COMMIT DROP AS
SELECT o.id FROM store_offers o JOIN json_populate_recordset(NULL::store_offers, '{offers_json}') b ON o.id=b.id
WHERE o.product_id IS NULL AND o.match_status='review' AND o.title=b.title;
UPDATE store_offers o SET product_id=b.product_id,match_status=b.match_status,match_confidence=b.match_confidence
FROM json_populate_recordset(NULL::store_offers, '{offers_json}') b WHERE o.id=b.id AND o.id IN (SELECT id FROM restored_ids);
UPDATE match_candidates m SET status=b.status FROM json_populate_recordset(NULL::match_candidates, '{candidates_json}') b
WHERE m.id=b.id AND m.offer_id IN (SELECT id FROM restored_ids) AND m.status='superseded';
UPDATE clusters SET offers_count=0,min_price_retail=NULL,min_price_opt=NULL;
UPDATE clusters c SET offers_count=a.n,min_price_retail=a.retail,min_price_opt=a.opt FROM
(SELECT p.cluster_id,count(*) n,min(o.price_retail) retail,min(o.price_opt) opt FROM store_offers o JOIN products p ON p.id=o.product_id WHERE o.is_active AND p.cluster_id IS NOT NULL GROUP BY p.cluster_id) a WHERE c.id=a.cluster_id;
SELECT count(*) FROM restored_ids;
COMMIT;""")
    )
    raise SystemExit(0)
query = r"""
SELECT coalesce(json_agg(row_to_json(o)), '[]') FROM store_offers o
JOIN products p ON p.id=o.product_id JOIN clusters c ON c.id=p.cluster_id
JOIN part_types t ON t.id=c.part_type_id
WHERE o.match_status='auto' AND (
(t.code='camera' AND o.title ~* '^Стекло[[:space:](]') OR
(t.code IN ('display','battery','back_cover') AND o.title ~* '^(Скотч|Проклейка|Клей|Уплотнитель|Tape|Adhesive|Gasket)[[:space:](]'));
"""
offers = json.loads(sql("BEGIN READ ONLY; " + query + " ROLLBACK;"))
print(json.dumps({"candidates": len(offers), "ids": [o["id"] for o in offers]}))
if args.apply and offers:
    ids = ",".join(str(o["id"]) for o in offers)
    candidates = json.loads(
        sql(
            f"SELECT coalesce(json_agg(row_to_json(m)), '[]') FROM match_candidates m WHERE offer_id IN ({ids});"
        )
    )
    target = Path(".unlazy/contextual-offers")
    target.mkdir(parents=True, exist_ok=True)
    path = target / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    path.write_text(
        json.dumps(
            {"offers": offers, "candidates": candidates}, ensure_ascii=False, indent=2
        )
    )
    conditions = " OR ".join(
        f"(id={o['id']} AND product_id={o['product_id']} AND match_status='auto')"
        for o in offers
    )
    result = sql(f"""BEGIN;
SELECT pg_advisory_xact_lock(72925378991444);
CREATE TEMP TABLE quarantine_ids ON COMMIT DROP AS SELECT id FROM store_offers WHERE {conditions};
UPDATE store_offers SET product_id=NULL,match_status='review',match_confidence=NULL WHERE id IN (SELECT id FROM quarantine_ids);
UPDATE match_candidates SET status='superseded' WHERE offer_id IN (SELECT id FROM quarantine_ids) AND status IN ('pending','approved');
UPDATE clusters SET offers_count=0,min_price_retail=NULL,min_price_opt=NULL;
UPDATE clusters c SET offers_count=a.n,min_price_retail=a.retail,min_price_opt=a.opt FROM
(SELECT p.cluster_id,count(*) n,min(o.price_retail) retail,min(o.price_opt) opt FROM store_offers o JOIN products p ON p.id=o.product_id WHERE o.is_active AND p.cluster_id IS NOT NULL GROUP BY p.cluster_id) a WHERE c.id=a.cluster_id;
SELECT count(*) FROM quarantine_ids;
COMMIT;""")
    print(json.dumps({"snapshot": str(path), "result": result}))
