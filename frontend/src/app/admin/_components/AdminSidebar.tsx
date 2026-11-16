'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/shared/lib/utils';

type SidebarItem = {
  label: string;
  href: string;
  icon: React.ReactNode;
};

const MAIN_ITEMS: SidebarItem[] = [
  {
    label: 'Дашборд',
    href: '/admin',
    icon: (
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
    ),
  },
  {
    label: 'Пользователи',
    href: '/admin/users',
    icon: (
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
    ),
  },
];

const SYSTEM_ITEMS: SidebarItem[] = [
  {
    label: 'Модерация',
    href: '/admin/moderation',
    icon: (
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
    ),
  },
  {
    label: 'Импорт офферов',
    href: '/admin/import',
    icon: (
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
    ),
  },
  {
    label: 'Парсеры',
    href: '/admin/parsers',
    icon: (
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
    ),
  },
  {
    label: 'Рассылки',
    href: '/admin/mailings',
    icon: (
      <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/></svg>
    ),
  },
];

function SidebarLink({ item }: { item: SidebarItem }) {
  const active = usePathname() === item.href;
  return (
    <Link
      href={item.href}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'flex min-h-11 shrink-0 items-center gap-3 rounded-full px-4 py-2 text-[15px] no-underline transition-colors hover:bg-search-row focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate',
        active ? 'bg-search-row text-slate font-semibold' : 'text-body',
      )}
    >
      {item.icon}
      {item.label}
    </Link>
  );
}

export function AdminSidebar() {
  return (
    <aside className="w-[240px] shrink-0 border-r border-border-light-subtle bg-ivory lg:sticky lg:top-[72px] lg:h-[calc(100vh-72px)] lg:overflow-y-auto max-lg:w-full max-lg:border-b max-lg:border-r-0">
      <div className="px-6 pb-5 pt-8 max-lg:pb-3 max-lg:pt-5 max-sm:px-4">
        <Link href="/admin" className="rounded text-base font-semibold text-body-subtle no-underline hover:text-slate focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-slate">Панель управления</Link>
      </div>
      <nav aria-label="Разделы панели управления" className="px-3 pb-5 max-lg:flex max-lg:gap-1 max-lg:overflow-x-auto max-sm:px-2">
        <p className="mb-2 px-3 text-xs uppercase tracking-[0.04em] text-body-muted max-lg:hidden">Основное</p>
        {MAIN_ITEMS.map((item) => <SidebarLink key={item.href} item={item} />)}
        <p className="mb-2 mt-6 px-3 text-xs uppercase tracking-[0.04em] text-body-muted max-lg:hidden">Система</p>
        {SYSTEM_ITEMS.map((item) => <SidebarLink key={item.href} item={item} />)}
      </nav>
    </aside>
  );
}
