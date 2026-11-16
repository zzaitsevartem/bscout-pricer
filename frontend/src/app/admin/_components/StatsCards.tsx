'use client';

import React from 'react';
import { useAdminStats } from '@/models/admin';
import { apiErrorMessage, formatNumber } from '@/app/admin/_components/lib';

export function StatsCards() {
  const stats = useAdminStats();

  if (stats.isError) {
    return (
      <div role="alert" className="mb-8 rounded-2xl bg-search-row p-5">
        <div className="text-[15px] text-clay">
          {apiErrorMessage(stats.error, 'Не удалось загрузить статистику')}
        </div>
        <button
          type="button"
          onClick={() => stats.refetch()}
          className="btn-secondary btn-sm mt-3"
        >
          Повторить
        </button>
      </div>
    );
  }

  const cards: { label: string; value: number | undefined }[] = [
    { label: 'Пользователей', value: stats.data?.total_users },
    { label: 'Активных подписок', value: stats.data?.active_subscriptions },
    { label: 'Товаров в базе', value: stats.data?.total_products },
    { label: 'Магазинов', value: stats.data?.total_stores },
  ];

  return (
    <div className="mb-12 grid grid-cols-4 gap-x-6 gap-y-8 max-xl:grid-cols-2">
      {cards.map((card) => (
        <div key={card.label} className="border-l border-border-light-subtle pl-6 first:border-l-0 first:pl-0 max-xl:odd:border-l-0 max-xl:odd:pl-0">
          <div className="mb-3 text-[36px] font-semibold leading-none tabular-nums text-slate">
            {card.value === undefined ? '—' : formatNumber(card.value)}
          </div>
          <div className="text-[14px] text-body-subtle">{card.label}</div>
        </div>
      ))}
    </div>
  );
}
