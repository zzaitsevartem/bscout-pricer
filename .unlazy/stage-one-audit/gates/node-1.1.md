# Gates: audit integration

Scope: reconcile both child results into the stage-one verdict.

- [x] N1: The code/test audit and evidence audit are independently reviewed and combined into a five-item verdict.
  EVIDENCE: Reconciled Terra's `.unlazy/stage-one-audit/gates/leaf-terra.md` with Luna's `leaf-luna.md`. Current concrete defect: validation 422 reflects sensitive input. Unverified requirement: fresh full live-source pipeline after matching changes. Other items have same-day implementation evidence, with the limitations recorded in root `GATES.md`.
