'use client';

import Link from 'next/link';
import { useMarkNotificationRead, type NotificationResponse } from '@/models/notification';
import { formatDateTime, formatMoney } from '@/shared/lib/format';
import { cn } from '@/shared/lib/utils';

const TYPE_LABELS: Record<string, string> = {
  price_drop: 'Цена снизилась',
  new_device_product: 'Новая запчасть',
  target_reached: 'Достигнута целевая цена',
};

export function NotificationItem({ item }: { item: NotificationResponse }) {
  const markRead = useMarkNotificationRead();

  return (
    <article className={cn('rounded-2xl px-5 py-5 max-sm:px-4', item.is_read ? 'bg-ivory' : 'bg-search-row')}>
      <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-body-muted">
        <span className={cn('inline-flex items-center gap-2 font-medium', !item.is_read && 'text-slate')}>
          {!item.is_read && <span aria-hidden="true" className="h-2 w-2 rounded-full bg-accent" />}
          {item.is_read ? 'Прочитано' : 'Новое'}
        </span>
        <span>{TYPE_LABELS[item.type] ?? item.type}</span>
        <time dateTime={item.created_at}>{formatDateTime(item.created_at)}</time>
      </div>
      <h3 className="mb-1 break-words text-base font-semibold text-slate">{item.title}</h3>
      <p className="mb-0 break-words text-sm leading-relaxed text-body-subtle">{item.body}</p>
      {item.old_price !== null && item.new_price !== null && (
        <p className="mb-0 mt-2 text-sm tabular-nums text-body-subtle">
          {formatMoney(item.old_price)} → {formatMoney(item.new_price)}
        </p>
      )}
      {(item.product_id !== null || !item.is_read) && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {item.product_id !== null && (
            <Link href={`/product/${item.product_id}`} className="btn-secondary btn-sm min-h-11">К товару</Link>
          )}
          {!item.is_read && (
            <button type="button" onClick={() => markRead.mutate(item.id)} disabled={markRead.isPending} className="btn-ghost btn-sm min-h-11 disabled:opacity-60">
              {markRead.isPending ? 'Сохранение…' : 'Прочитано'}
            </button>
          )}
        </div>
      )}
      {markRead.isError && <p role="alert" className="mb-0 mt-2 text-sm text-clay">Не удалось отметить уведомление. Попробуйте ещё раз.</p>}
    </article>
  );
}
