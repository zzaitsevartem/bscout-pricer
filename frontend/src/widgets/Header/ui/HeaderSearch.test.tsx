import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { HeaderSearch } from './HeaderSearch';

const push = vi.fn();
vi.mock('next/navigation', () => ({ useRouter: () => ({ push }) }));
vi.mock('@/widgets/ProductSearch/ui/ProductSearchField', () => ({
  ProductSearchField: ({ id, value, onValueChange }: { id: string; value: string; onValueChange: (value: string) => void }) => (
    <input id={id} value={value} onChange={(event) => onValueChange(event.target.value)} />
  ),
}));

it('submits the typed search with Enter without a search icon button inside the field', async () => {
  const user = userEvent.setup();
  render(<HeaderSearch />);
  const field = screen.getByRole('textbox', { name: 'Поиск запчастей' });
  await user.type(field, 'iPhone 15{Enter}');
  expect(push).toHaveBeenCalledWith('/search?q=iPhone%2015');
  expect(screen.queryByRole('button', { name: /^(найти|поиск)$/i })).not.toBeInTheDocument();
});
