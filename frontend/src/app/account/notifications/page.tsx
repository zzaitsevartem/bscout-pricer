'use client';

import { PageTransition } from '@/shared/ui/PageTransition';
import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/widgets/Header/ui/Header';
import { Footer } from '@/widgets/Footer/ui/Footer';
import { AccountSidebar } from '@/widgets/AccountSidebar/ui/AccountSidebar';
import { RequireAuth } from '@/shared/lib/RequireAuth';
import { useNotifications } from '@/models/notification';
import { NotificationItem } from '@/widgets/Notifications/ui/NotificationItem';

const PER_PAGE = 20;

function NotificationsContent() {
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const notifications = useNotifications({
    page,
    per_page: PER_PAGE,
    ...(unreadOnly ? { unread: true } : {}),
  });
  const totalPages = notifications.data
    ? Math.max(1, Math.ceil(notifications.data.total / PER_PAGE))
    : 1;

  return (
    <>
      <PageTransition className="max-w-[1200px] mx-auto px-6 max-sm:px-4">
        <div className="grid grid-cols-[264px_1fr] gap-8 py-8 max-sm:py-6 min-h-[calc(100vh-64px)] max-md:grid-cols-1">
          <AccountSidebar />

          <main className="min-w-0">
            <div className="mb-8">
              <div className="flex items-baseline justify-between gap-4 mb-6 flex-wrap">
                <h1 className="text-[40px] font-semibold text-slate max-sm:text-[32px]">Уведомления</h1>
                <button
                  type="button"
                  onClick={() => {
                    setUnreadOnly((current) => !current);
                    setPage(1);
                  }}
                  aria-pressed={unreadOnly}
                  className={unreadOnly ? 'btn-primary btn-sm min-h-11' : 'btn-secondary btn-sm min-h-11'}
                >
                  {unreadOnly ? 'Показать все' : 'Только непрочитанные'}
                </button>
              </div>

              <div className="space-y-3" aria-busy={notifications.isLoading}>
                {notifications.isLoading ? (
                  <div role="status" className="rounded-2xl bg-search-row px-5 py-8 text-body-subtle">Загрузка уведомлений…</div>
                ) : notifications.isError ? (
                  <div role="alert" className="rounded-2xl bg-search-row px-5 py-8 text-body-subtle">
                    <p>Не удалось загрузить уведомления.</p>
                    <button type="button" onClick={() => notifications.refetch()} className="btn-secondary btn-sm">Повторить</button>
                  </div>
                ) : notifications.data && notifications.data.results.length > 0 ? (
                  notifications.data.results.map((item) => (
                    <NotificationItem key={item.id} item={item} />
                  ))
                ) : (
                  <div role="status" className="rounded-2xl bg-search-row px-5 py-10 text-center">
                    <p className="text-[15px] text-body-subtle mb-2">
                      {unreadOnly ? 'Непрочитанных уведомлений нет.' : 'Уведомлений пока нет.'}
                    </p>
                    <p className="text-[14px] text-body-muted mb-4">
                      Здесь появятся изменения цен и новые запчасти из вашего мониторинга.
                    </p>
                    <Link href="/account/tracking" className="btn-secondary">
                      К мониторингу
                    </Link>
                  </div>
                )}
              </div>

              {totalPages > 1 && (
                <nav aria-label="Страницы уведомлений" className="mt-6 flex flex-wrap items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                    disabled={page <= 1}
                    className="btn-secondary btn-sm disabled:opacity-40"
                  >
                    Назад
                  </button>
                  <span aria-live="polite" className="text-[14px] text-body-subtle">
                    {page} из {totalPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                    disabled={page >= totalPages}
                    className="btn-secondary btn-sm disabled:opacity-40"
                  >
                    Вперёд
                  </button>
                </nav>
              )}
            </div>
          </main>
        </div>
      </PageTransition>
      <Footer />
    </>
  );
}

export default function AccountNotificationsPage() {
  return (
    <>
      <Header />
      <RequireAuth>
        <NotificationsContent />
      </RequireAuth>
    </>
  );
}
