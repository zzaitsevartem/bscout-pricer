import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { AdminSidebar } from './_components/AdminSidebar';
import { AdminShell } from './_components/AdminShell';
import { RequireAdmin } from '@/widgets/RequireAdmin/ui/RequireAdmin';

const route = vi.hoisted(() => ({ pathname: '/admin', replace: vi.fn(), admin: false }));
vi.mock('next/navigation', () => ({ usePathname: () => route.pathname, useRouter: () => ({ replace: route.replace }) }));
vi.mock('@/models/user', () => ({ useMe: () => ({ data: { is_admin: route.admin }, isLoading: false }) }));
vi.mock('@/shared/lib/RequireAuth', () => ({ RequireAuth: ({ children }: { children: React.ReactNode }) => children }));
vi.mock('@/shared/ui/PageTransition', () => ({ PageTransition: ({ children }: { children: React.ReactNode }) => children }));
afterEach(() => { history.replaceState(null, '', '/'); route.pathname = '/admin'; route.replace.mockReset(); });
it('provides distinct section routes and marks the current page', () => {
  route.pathname = '/admin/moderation';
  render(<AdminSidebar />);
  for (const [name, href] of [['Дашборд', '/admin'], ['Пользователи', '/admin/users'], ['Модерация', '/admin/moderation'], ['Импорт офферов', '/admin/import'], ['Парсеры', '/admin/parsers'], ['Рассылки', '/admin/mailings']]) {
    expect(screen.getByRole('link', { name })).toHaveAttribute('href', href);
  }
  expect(screen.getByRole('link', { name: 'Модерация' })).toHaveAttribute('aria-current', 'page');
});
it('maps old section hashes to direct routes while retaining the query', () => {
  history.replaceState(null, '', '/admin?from=test#mailings');
  render(<AdminShell>Content</AdminShell>);
  expect(route.replace).toHaveBeenCalledWith('/admin/mailings?from=test');
});

it('keeps protected content from non-admin users and redirects them', () => {
  route.admin = false;
  render(<RequireAdmin>Protected admin content</RequireAdmin>);
  expect(screen.queryByText('Protected admin content')).not.toBeInTheDocument();
  expect(route.replace).toHaveBeenCalledWith('/account');
});
