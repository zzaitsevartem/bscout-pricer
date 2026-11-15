# Gates: independent recheck

- [x] G1: Reconcile all formerly unverified claims with fresh evidence or concrete limits.
  EVIDENCE: luna-recheck.md and terra-recheck.md: HTTP422 echo, npm30/4critical, isolated restore and webhook race; actual deployment/catalog provenance and live parser end-to-end remain unknown, explicitly handed off.
- [x] G2: Independently inspect agents findings and enumerate errors in previous answer.
  EVIDENCE: Root disabled dotenv before imports; requirements SQLAlchemy2.0.35 and isolated lock SQLAlchemy2.0.51 both import main/configure_mappers; registry has four instances; bcrypt short verifies; independent HTTP422 echo=True; parsed audit JSON30/4critical; reviewed race script and reports. One erroneous causal conclusion: outdated/already fixed; four earlier verification gaps resolved, not technical reversals.
