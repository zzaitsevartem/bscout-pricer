import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { NotificationsFeed } from './NotificationsFeed';

const state = vi.hoisted(() => ({ auth: true, query: {} as Record<string, unknown>, refetch: vi.fn() }));
vi.mock('effector-react', () => ({ useUnit: () => state.auth }));
vi.mock('@/models/notification', () => ({ useNotifications: () => state.query }));
vi.mock('@/widgets/Notifications/ui/NotificationItem', () => ({ NotificationItem: () => <article>Уведомление</article> }));
beforeEach(() => { state.auth = true; state.refetch.mockReset(); state.query = { isPending: false, isError: false, data: { total: 0, results: [] }, refetch: state.refetch }; });
it('hides the feed for guests and shows loading and empty states for signed-in users', () => {
  state.auth = false;
  const view = render(<NotificationsFeed />);
  expect(screen.queryByRole('region', { name: 'Уведомления' })).not.toBeInTheDocument();
  state.auth = true; state.query = { isPending: true };
  view.rerender(<NotificationsFeed />);
  expect(screen.getByRole('status')).toHaveTextContent('Загрузка');
  state.query = { isPending: false, data: { total: 0, results: [] } };
  view.rerender(<NotificationsFeed />);
  expect(screen.getByText('Уведомлений пока нет.')).toBeInTheDocument();
});
it('offers retry when loading fails', () => {
  state.query = { isPending: false, isError: true, refetch: state.refetch };
  render(<NotificationsFeed />);
  expect(screen.getByRole('alert')).toHaveTextContent('Не удалось загрузить');
  fireEvent.click(screen.getByRole('button', { name: 'Повторить' }));
  expect(state.refetch).toHaveBeenCalledOnce();
});
