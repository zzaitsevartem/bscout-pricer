import asyncio,json
from collections import Counter
from sqlalchemy import text,select
import src.db_metadata
from src.database import async_session_factory,engine
from src.modules.catalog.service.dictionaries import load_dictionaries
from src.modules.catalog.service.extractor import extract
from src.modules.products.model.product import StoreOffer,Product,Cluster,MatchCandidate

async def main():
 async with async_session_factory() as db:
  await db.execute(text('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY'))
  dictionaries=await load_dictionaries(db)
  counts=Counter(); issues=[]; pending=[]
  rows=(await db.execute(select(StoreOffer,Product,Cluster).outerjoin(Product,Product.id==StoreOffer.product_id).outerjoin(Cluster,Cluster.id==Product.cluster_id).where(StoreOffer.is_active.is_(True)).order_by(StoreOffer.id))).all()
  for offer,product,cluster in rows:
   counts['status_'+offer.match_status]+=1
   if product is None: continue
   counts['linked']+=1
   attrs=extract(offer.title,dictionaries)
   reasons=[]
   if cluster is None: reasons.append('no_cluster')
   else:
    for field,current,expected in [('device',attrs.device_id,cluster.device_id),('part_type',attrs.part_type_id,cluster.part_type_id)]:
     if current is None:
      counts[field+'_unresolved']+=1
      reasons.append(field+'_unresolved')
     elif current!=expected: reasons.append(field+'_different')
   if reasons:
    counts['flagged']+=1
    for reason in reasons: counts[reason]+=1
    issues.append(dict(offer_id=offer.id,status=offer.match_status,title=offer.title,url=offer.url,product_id=product.id,canonical_name=product.canonical_name,reasons=reasons,linked_device=dictionaries.device_model_key.get(cluster.device_id) if cluster else None,extracted_device=dictionaries.device_model_key.get(attrs.device_id),matched=attrs.matched))
  candidates=(await db.execute(select(MatchCandidate,StoreOffer,Cluster).join(StoreOffer,StoreOffer.id==MatchCandidate.offer_id).join(Product,Product.id==MatchCandidate.product_id).outerjoin(Cluster,Cluster.id==Product.cluster_id).where(MatchCandidate.status=='pending'))).all()
  for candidate,offer,cluster in candidates:
   attrs=extract(offer.title,dictionaries)
   if cluster and attrs.device_id!=cluster.device_id:
    pending.append(dict(candidate_id=candidate.id,offer_id=offer.id,title=offer.title,product_id=candidate.product_id,linked_device=dictionaries.device_model_key.get(cluster.device_id),extracted_device=dictionaries.device_model_key.get(attrs.device_id),features=candidate.features,active=offer.is_active))
  print(json.dumps(dict(counts=counts,issues=issues,pending_total=len(candidates),pending_device_different_or_unresolved=pending),ensure_ascii=False,default=str))
  await db.rollback()
 await engine.dispose()
asyncio.run(main())
