'use client';

import { useIsFetching, useQueryClient } from '@tanstack/react-query';
import { StatsCards } from '@/app/admin/_components/StatsCards';
import { UsersTable } from '@/app/admin/_components/UsersTable';

export default function AdminPage() {
  const queryClient = useQueryClient();
  const fetching = useIsFetching({ queryKey: ['admin'] });

  return (
    <div id="dashboard">
      <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="mb-1 text-[40px] font-semibold text-slate max-sm:text-[32px]">Дашборд</h1>
          <p className="mb-0 text-base text-body-subtle">Сводка по системе</p>
        </div>
        <button type="button" onClick={() => queryClient.invalidateQueries({ queryKey: ['admin'] })} disabled={fetching > 0} className="btn-primary btn-sm min-h-11 disabled:cursor-not-allowed disabled:opacity-60">
          {fetching > 0 ? 'Обновление…' : 'Обновить'}
        </button>
      </div>
      <StatsCards />
      <UsersTable preview />
    </div>
  );
}
