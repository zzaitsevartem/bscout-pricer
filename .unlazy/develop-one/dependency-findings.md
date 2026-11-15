# Зависимости этапа 1

Доказательства: npm-before.json, npm-after.json, pip-before.json, pip-after.json; manifests и lockfiles в репозитории.

- npm audit: 30 (12 moderate, 14 high, 4 critical) → 0 по итоговому package-lock.
- Next 14 → 15.5.29 (поддерживаемая maintenance-ветка); адаптация params и Suspense.
- Vitest 2 → 4.1.12 / Vite 7; workspace заменён projects. Node хоста 22.17.1 соответствует engines. Совместимость подтверждена frontend tests/lint/build и backend unit/auth integration; детали в gptaudits/81.md.
- PostCSS override внутри Next: ^8.5.23, resolved 8.5.33. Требуется из-за закреплённого старого PostCSS внутри Next 15.
- minimatch override внутри @typescript-eslint/typescript-estree: ^11.0.8. Upstream ESLint parser 8.72.2 (текущий latest) тянет уязвимый minimatch 10.2.6. API и поведение override прошли lint/регрессионную проверку; убрать override после исправления upstream.
- Backend audit: 26 записей в пяти пакетах → 3 записи в двух пакетах (2 разных advisory; ecdsa повторён сервисом в двух записях).
- FastAPI 0.163.1 + Starlette 1.3.1, dotenv 1.2.2, pytest 9.0.3 + pytest-asyncio 1.3.0, python-jose 3.5.0. Resolver подтвердил совместимость зависимостей с сохранённым Pydantic 2.9.0; это не runtime-проверка.
- Python 3.11 и runtime/dev версии согласованы в requirements/pyproject; poetry.lock обновлён временным Poetry исключительно для lockfile, установка приложения остаётся через pip.
- pnpm-lock.yaml обновлён импортом package-lock; файлы не удалены.

## Остаточные backend findings

1. PYSEC-2026-4298 / GHSA-3qf3-8w2g-rqmx: python-jose 3.5.0, нет опубликованного исправления. Algorithm confusion при использовании DER public key как HMAC secret и неограниченных algorithms. Код явно передаёт algorithms=[settings.jwt_algorithm]; default HS256 и случайный серверный secret. Это ограничивает применимость при корректном default deployment; фактические production secrets/config не читались и не проверялись. Отдельная замена JWT-библиотеки и live JWT acceptance требуют согласования с разработчиком 2. Finding оставлен открытым, не объявлен устранённым.
2. PYSEC-2026-1325 / GHSA-wj6h-64fc-37mp: timing side channel ECDSA signing/keygen/ECDH; upstream не планирует исправление. В существующем auth пути HS256 нет ECDSA signing; ecdsa транзитивно приносит python-jose. При переходе на ES256 потребуется пересмотр/замена. Finding оставлен открытым.

## Ограничения

Владелец одобрил проверки; gates G1/G2/G5/G1R/G3B/G3C прошли с независимым --reverify. Backend auth integration: 84 passed, без skip, отдельные PostgreSQL16/Redis. Frontend: 220 passed, lint/build прошли. Независимый reviewer нашёл два P2; оба исправлены и покрыты регрессиями. Реальные .env не читались. Production deployment не выполнялся.
