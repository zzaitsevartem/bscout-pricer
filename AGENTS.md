# BScout Repository Rules

## Source of Truth

Run all commands from this Git repository, not the parent `bscount/` directory.
Trust code and current configuration over older prose. Read `DESIGN.md` before
UI work and `docs/technical-specification.md` before feature implementation.
Backend and frontend rules are refined by their nested `AGENTS.md` files.

`docs/plan/MASTERPLAN.md` is the only live task plan. At session start run:

```bash
bash scripts/plan/plan_status.sh
git log --oneline -10
git status --short
```

Do not create parallel TODO/plan documents. Closed details belong in
`docs/plan/archive/`; `docs/plan/INDEX.md` is the append-only block ledger.

Session results and handoff context live in `gptaudits/1.md`, `2.md`, etc.
At session start read the latest numbered audit; save the next session's results
in the next numbered file. Keep the live task plan in `docs/plan/MASTERPLAN.md`.

## Graphify (codebase graph)

- Use the Graphify project graph as the first lookup for code structure: ask a
  focused question, then use its symbol, dependency, caller, and linked-test
  results to scope work. This avoids broad repository reads when the graph has
  current coverage.
- Check the graph result's `commitSha` against `git rev-parse HEAD`. If they
  match and coverage is complete, use the graph answer without reopening those
  unchanged files. Read current source for files changed since that commit,
  empty/partial results, and whenever implementation details need confirmation.
- Treat graph relationships and linked tests as navigation aids, not proof of
  runtime behavior or complete test coverage. Verify behavior proportionally
  to risk and follow the existing test and nested-agent instructions.
- If the repository has no promoted graph or Graphify is unavailable, continue
  with targeted `rg`/file reads; don't assume the graph was built or current.
- Keep this rule brief; do not copy generated graph inventories into this file.

## Architecture

- `backend/src/`: FastAPI, async SQLAlchemy, Redis, and module-based MVC.
- `backend/tests/{unit,integration}/`: Pytest suites.
- `frontend/src/`: Next.js App Router organized into `app/`, `models/`,
  `widgets/`, and `shared/`.
- `docs/`: specifications, audits, plans, and manual verification.
- `docker-compose.yml`, `docker-compose.prod.yml`, `deploy/nginx/`:
  local and production infrastructure.

## Commands

```bash
docker compose up -d
cd backend
source ../venv/bin/activate
pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m pytest tests/unit
ruff check src tests

cd ../frontend
npm install
npm run build
npm run lint
npm test
```

Use Python 3.11 and the existing `venv`/pip workflow; Poetry is not installed
for this checkout. Local ports may be overridden by gitignored environment
files; never read or edit real `.env` files. Use `.env.example` templates.

## Working Rules

- Preserve unrelated dirty-worktree changes.
- Do not commit unless explicitly asked.
- Do not create README or planning files without an explicit request.
- Add regression tests for fixes and verify changes proportionally to risk.
- Use the project skills under `.agents/skills/` for backend modules, frontend
  entities, UI/design work, and convention reviews.
- Default to direct execution for small tasks; use
  `.agents/skills/bscout-orchestrate/SKILL.md` for budget-aware delegation. Use Luna
  reader for substantial exploration, separate coder for useful independent work,
  and prompt master/reviewer only when needed. Avoid a mandatory agent chain and
  load only task-relevant skills. Preserve user-selected models and efforts.
