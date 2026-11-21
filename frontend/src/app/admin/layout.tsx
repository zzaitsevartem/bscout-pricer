import type { ReactNode } from 'react';
import { Header } from '@/widgets/Header/ui/Header';
import { RequireAdmin } from '@/widgets/RequireAdmin/ui/RequireAdmin';
import { AdminShell } from '@/app/admin/_components/AdminShell';

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Header />
      <RequireAdmin>
        <AdminShell>{children}</AdminShell>
      </RequireAdmin>
    </>
  );
}
