import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { NotificationItem } from './NotificationItem';
import type { NotificationResponse } from '@/models/notification';

const state = vi.hoisted(() => ({ mutate: vi.fn(), isPending: false, isError: false }));
vi.mock('@/models/notification', () => ({ useMarkNotificationRead: () => state }));
const item: NotificationResponse = {
  id: 7, user_id: 1, tracked_product_id: null, product_id: 12, type: 'price_drop',
  channel: 'in_app', status: 'sent', title: 'Цена', body: 'Цена изменилась', old_price: '100',
  new_price: '0', error: null, created_at: '2026-11-17T00:00:00Z', sent_at: null,
  read_at: null, is_read: false,
};
beforeEach(() => { state.mutate.mockReset(); state.isPending = false; state.isError = false; });
it('shows unread state, zero price, product link and marks the selected item', () => {
  render(<NotificationItem item={item} />);
  expect(screen.getByText('Новое')).toBeInTheDocument();
  expect(screen.getByText(/100.*→.*0/)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'К товару' })).toHaveAttribute('href', '/product/12');
  fireEvent.click(screen.getByRole('button', { name: 'Прочитано' }));
  expect(state.mutate).toHaveBeenCalledWith(7);
});
it('shows read state without a mark action and reports mutation errors', () => {
  state.isError = true;
  const view = render(<NotificationItem item={item} />);
  expect(screen.getByRole('alert')).toHaveTextContent('Не удалось отметить');
  state.isError = false;
  view.rerender(<NotificationItem item={{ ...item, is_read: true }} />);
  expect(screen.getByText('Прочитано')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Прочитано' })).not.toBeInTheDocument();
});
