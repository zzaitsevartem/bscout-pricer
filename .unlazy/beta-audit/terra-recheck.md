# Дополнительная проверка — 2026-11-15

Проверялся текущий рабочий код; отсутствие новых коммитов не доказывает ни исправление, ни наличие проблемы без проверки кода и условий. Данные платежного провайдера и реальные `.env` не использовались. Временные контейнеры PostgreSQL 16 и Redis созданы отдельно, на случайных loopback-портах; тестовый процесс запущен из `/private/tmp`, чтобы не загружать файлы окружения проекта.

## Двойная активация

**Воспроизведено в изолированном runtime**: скрипт `/private/tmp/bscout_terra_race.py` создаёт pending payment, отправляет два конкурентных POST `/api/payment/webhook` через ASGI с разными DB-сессиями; замена YooKassa синхронизирует два запроса на `get_payment` и обоим возвращает один и тот же успешный ответ. Запуск: `PYTHONPATH=/Users/zzaitsevartem/Desktop/projects/bscout/backend REDIS_HOST=127.0.0.1 REDIS_PORT=65041 JWT_SECRET_KEY=test-only-not-production-1234567890abcdef /Users/zzaitsevartem/Desktop/projects/bscout/backend/venv/bin/python /private/tmp/bscout_terra_race.py` из `/private/tmp` с доступом к loopback; скрипт использовал отдельную БД `127.0.0.1:64997/audit` (контейнеры после проверки удалены, порты непостоянные). Результат: оба ответа `200`, оба `detail: applied`, `subscriptions total: 2 active: 1`. Одна воспроизведённая последовательность, не живой YooKassa и не проверка реальных списаний; результаты подтверждают повторное применение, а не два списания. После вывода были предупреждения о закрытии Redis-соединений после event loop; скрипт завершился 0 и результат БД был получен до предупреждений. Ключевая причина — чтение pending без блокировки и проверка локального статуса до создания подписки (`backend/src/modules/payment/controller/payment.py:162-199`, `backend/src/modules/payment/service/payment_service.py:75-90,155-175,199-223`).

## Отслеживание

`TEST_DATABASE_URL=postgresql+asyncpg://audit:audit@127.0.0.1:64997/audit REDIS_HOST=127.0.0.1 REDIS_PORT=65041 PYTHONPATH=... backend/venv/bin/python -m pytest -q backend/tests/integration/test_tracking_api.py -k 'device_tracking_baseline_matching_and_entitlements or new_device_product_notification_is_visible_to_owner or device_tracking_concurrent_scans_notify_once'` (пути заданы абсолютными, запуск из `/private/tmp`) — **3 passed, 23 deselected**. Проверены отказ Basic и expired Advanced, baseline, последующая деталь, уведомление владельцу, доступ другого пользователя и конкурентное сканирование. Не проверены фактическое выполнение расписания worker и внешняя доставка. Первая попытка без повышения прав дала 3 skipped из-за запрета loopback; это не прохождение тестов.

## Logout

На тех же изолированных сервисах `test_token_lifecycle.py -k 'logout_without_body_revokes_every_session or logout_revokes_refresh_token or reuse_of_rotated_token_revokes_whole_family'` — **3 passed, 28 deselected**. Эти сценарии проверяют отзыв при logout без body, отзыв refresh при logout и отзыв семейства при reuse ротированного токена. Это существующие интеграционные тесты, не ручная browser-приёмка и не отдельно подтверждённое сохранение после перезапуска процесса.

## Восстановление

`docker exec -i bscout-audit-terra-pg pg_restore --list < 'backups/тест бекап.dump'` — архив PostgreSQL custom, pg_dump 16.13, 333 TOC entries. Затем в новую пустую `restore_check` выполнен `pg_restore --exit-on-error --no-owner --no-privileges -U audit -d restore_check` с тем же архивом на stdin — **exit 0**; `select version_num from alembic_version` вернул `20261113_device_tracking`. Это проверяет сам архив и прямое восстановление без owner/privileges, не запуск проектного скрипта восстановления, не сверку содержимого каждой таблицы и не совместимость приложения с восстановленными данными.

Остальные выводы `.unlazy/beta-audit/terra.md` остаются основанными на чтении текущего кода: смена тарифов, автопродление, дневной ключ повтора, потеря выбранного тарифа и отсутствие диалога на странице устройства. Они не называются исправленными из-за отсутствия новых коммитов. Component test карточки 14/14 указан в исходном отчёте.
