'use client';

import { useEffect, type ReactNode } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { PageTransition } from '@/shared/ui/PageTransition';
import { AdminSidebar } from '@/app/admin/_components/AdminSidebar';

const LEGACY_SECTIONS = ['users', 'moderation', 'import', 'parsers', 'mailings'];

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const openLegacySection = () => {
      const section = window.location.hash.slice(1);
      if (pathname === '/admin' && LEGACY_SECTIONS.includes(section)) {
        router.replace(`/admin/${section}${window.location.search}`);
      }
    };
    openLegacySection();
    window.addEventListener('hashchange', openLegacySection);
    return () => window.removeEventListener('hashchange', openLegacySection);
  }, [pathname, router]);

  return (
    <div className="mx-auto flex min-h-[calc(100vh-72px)] max-w-[1600px] max-lg:flex-col">
      <a href="#admin-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-20 focus:z-50 focus:rounded-full focus:bg-ivory focus:px-4 focus:py-3 focus:text-slate">К содержимому</a>
      <AdminSidebar />
      <main id="admin-content" className="min-w-0 flex-1 px-8 py-10 max-lg:px-6 max-sm:px-4 max-sm:py-6">
        <PageTransition key={pathname}>{children}</PageTransition>
      </main>
    </div>
  );
}
