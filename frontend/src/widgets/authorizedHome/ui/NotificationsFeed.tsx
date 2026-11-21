'use client';

import React from 'react';
import Link from 'next/link';
import { useUnit } from 'effector-react';
import { $isAuth } from '@/shared/config/store';
import { useNotifications } from '@/models/notification';
import { NotificationItem } from '@/widgets/Notifications/ui/NotificationItem';

const FEED_SIZE = 3;

const NotificationsFeed: React.FC = () => {
  const isAuth = useUnit($isAuth);
  const notifications = useNotifications({ page: 1, per_page: FEED_SIZE }, { enabled: isAuth });
  const feed = notifications.data;

  if (!isAuth) return null;

  return (
    <section aria-label="Уведомления" className="pb-20 max-md:pb-14">
      <div className="mx-auto max-w-[1200px] px-6 max-sm:px-4">
        <div className="mb-6 flex flex-wrap items-baseline justify-between gap-4">
          <div>
            <p className="mb-2 text-xs uppercase tracking-[0.04em] text-body-muted">Уведомления</p>
            <h2 className="mb-0 text-[40px] font-semibold leading-[1.15] tracking-[-0.01em] text-slate max-md:text-[32px] max-[480px]:text-[28px]">Новое для вас</h2>
          </div>
          <Link href="/account/notifications" className="btn-arrow rounded focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-slate">
            Все уведомления{feed ? ` (${feed.total})` : ''}
          </Link>
        </div>
        <div className="space-y-3" aria-busy={notifications.isPending}>
          {notifications.isPending ? (
            <p role="status" className="rounded-2xl bg-search-row px-5 py-8 text-body-subtle">Загрузка уведомлений…</p>
          ) : notifications.isError ? (
            <div role="alert" className="rounded-2xl bg-search-row px-5 py-8 text-body-subtle">
              <p>Не удалось загрузить уведомления.</p>
              <button type="button" onClick={() => notifications.refetch()} className="btn-secondary btn-sm">Повторить</button>
            </div>
          ) : feed && feed.results.length > 0 ? (
            feed.results.slice(0, FEED_SIZE).map((item) => <NotificationItem key={item.id} item={item} />)
          ) : (
            <div role="status" className="rounded-2xl bg-search-row px-5 py-8 text-body-subtle">
              <p className="mb-2">Уведомлений пока нет.</p>
              <p className="mb-4 text-sm">Здесь появятся изменения цен и новые запчасти из вашего мониторинга.</p>
              <Link href="/account/tracking" className="btn-secondary btn-sm">К мониторингу</Link>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export { NotificationsFeed };
