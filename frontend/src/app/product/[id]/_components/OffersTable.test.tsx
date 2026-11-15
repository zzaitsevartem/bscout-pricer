import { render, screen, within } from '@testing-library/react';
import { expect, it } from 'vitest';
import { OffersTable } from './OffersTable';

it('shows the supplier title alongside its store link', () => {
  render(<OffersTable offers={[{
    id: 1, store_id: 1, source_sku: 'fixture', title: 'Дисплей для Orion A10 Q987 (черный)',
    price_retail: '999.00', price_opt: null, price_old: null, currency: 'RUB',
    stock_status: 'in_stock', stock_qty: null, url: 'https://example.invalid/item',
    match_status: 'manual', match_confidence: '0.7650', last_seen_at: '2026-11-15T12:00:00Z',
    price_changed_at: null, is_cheapest: true, store: { id: 1, name: 'Магазин', slug: 'shop' },
  }]} />);
  const row = screen.getByText('Дисплей для Orion A10 Q987 (черный)').closest('tr');
  expect(row).not.toBeNull();
  expect(within(row!).getByRole('link', { name: 'В магазин' })).toHaveAttribute('href', 'https://example.invalid/item');
});
