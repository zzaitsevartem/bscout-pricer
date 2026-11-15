import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { OffersTable } from './OffersTable';

const state = vi.hoisted(() => ({ admin: true, mutate: vi.fn(), reset: vi.fn() }));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/user', () => ({ useMe: () => ({ data: { is_admin: state.admin } }) }));
vi.mock('@/models/admin', () => ({ useDeleteOffer: () => ({ mutate: state.mutate, reset: state.reset }) }));

const offer = {
  id: 1, store_id: 1, source_sku: 'fixture', title: 'Первый товар',
  price_retail: '999.00', price_opt: null, price_old: null, currency: 'RUB',
  stock_status: 'in_stock' as const, stock_qty: null, url: 'https://example.invalid/item',
  match_status: 'manual' as const, match_confidence: '0.7650', last_seen_at: '2026-11-15T12:00:00Z',
  price_changed_at: null, is_cheapest: true, store: { id: 1, name: 'Магазин', slug: 'shop' },
};
const offers = [offer, { ...offer, id: 2, title: 'Второй товар', price_retail: '1200.00' }];

beforeEach(() => {
  state.admin = true;
  state.mutate.mockReset();
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
});

it('shows the supplier title alongside its store link', () => {
  render(<OffersTable offers={offers} />);
  const row = screen.getByText('Первый товар').closest('tr')!;
  expect(within(row).getByRole('link', { name: 'В магазин' })).toHaveAttribute('href', 'https://example.invalid/item');
});

it('opens the selected row with right click, cancels, and confirms the other row via keyboard', () => {
  render(<OffersTable offers={offers} />);
  fireEvent.contextMenu(screen.getByText('Первый товар').closest('tr')!);
  fireEvent.click(screen.getByRole('menuitem', { name: 'Удалить' }));
  expect(screen.getByRole('dialog')).toHaveTextContent('Первый товар');
  fireEvent.click(screen.getByRole('button', { name: 'Отмена' }));
  expect(state.mutate).not.toHaveBeenCalled();
  fireEvent.keyDown(screen.getByText('Второй товар').closest('tr')!, { key: 'F10', shiftKey: true });
  fireEvent.click(screen.getByRole('menuitem', { name: 'Удалить' }));
  expect(screen.getByRole('dialog')).toHaveTextContent('Второй товар');
  fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Удалить' }));
  expect(state.mutate).toHaveBeenCalledWith(2, expect.any(Object));
});

it('does not expose row actions to ordinary users', () => {
  state.admin = false;
  render(<OffersTable offers={offers} />);
  const row = screen.getByText('Первый товар').closest('tr')!;
  fireEvent.contextMenu(row);
  fireEvent.keyDown(row, { key: 'F10', shiftKey: true });
  expect(screen.queryByRole('menu')).not.toBeInTheDocument();
});
