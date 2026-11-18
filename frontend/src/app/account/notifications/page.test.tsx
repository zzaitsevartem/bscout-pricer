import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import Page from './page';

const query = vi.hoisted(() => vi.fn());
vi.mock('@/models/notification', () => ({ useNotifications: query }));
vi.mock('@/widgets/Header/ui/Header', () => ({ Header: () => null }));
vi.mock('@/widgets/Footer/ui/Footer', () => ({ Footer: () => null }));
vi.mock('@/widgets/AccountSidebar/ui/AccountSidebar', () => ({ AccountSidebar: () => null }));
vi.mock('@/shared/lib/RequireAuth', () => ({ RequireAuth: ({ children }: { children: React.ReactNode }) => children }));
vi.mock('@/widgets/Notifications/ui/NotificationItem', () => ({ NotificationItem: () => <article>Уведомление</article> }));
it('changes pages and resets to page one when filtering unread', () => {
  query.mockReturnValue({ isLoading: false, isError: false, data: { total: 21, results: [{ id: 1 }] } });
  render(<Page />);
  fireEvent.click(screen.getByRole('button', { name: 'Вперёд' }));
  expect(query).toHaveBeenLastCalledWith({ page: 2, per_page: 20 });
  fireEvent.click(screen.getByRole('button', { name: 'Только непрочитанные' }));
  expect(query).toHaveBeenLastCalledWith({ page: 1, per_page: 20, unread: true });
  expect(screen.getByRole('button', { name: 'Показать все' })).toHaveAttribute('aria-pressed', 'true');
});
