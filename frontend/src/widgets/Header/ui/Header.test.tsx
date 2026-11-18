import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Header } from './Header';

vi.mock('next/navigation', () => ({ usePathname: () => '/', useRouter: () => ({ push: vi.fn() }) }));
vi.mock('effector-react', () => ({ useUnit: () => false }));
vi.mock('@/models/user', () => ({ useMe: () => ({}) }));
vi.mock('@/models/auth', () => ({ useLogout: () => ({ mutate: vi.fn() }) }));
vi.mock('@/models/notification', () => ({ useUnreadNotificationCount: () => ({}) }));
vi.mock('./ThemeToggle', () => ({ ThemeToggle: () => null }));
vi.mock('./HeaderSearch', () => ({ HeaderSearch: () => null }));
vi.mock('./UserMenu', () => ({ UserMenu: () => null }));

describe('mobile menu', () => {
  it('keeps closed navigation inert and re-enables it while open', () => {
    const view = render(<Header />);
    const panel = view.container.querySelector<HTMLElement>('[data-open]')!;
    expect(panel.inert).toBe(true);
    expect(panel).toHaveAttribute('aria-hidden', 'true');
    fireEvent.click(screen.getByRole('button', { name: 'Открыть меню' }));
    expect(panel.inert).toBe(false);
    expect(panel).toHaveAttribute('aria-hidden', 'false');
    fireEvent.click(screen.getByRole('button', { name: 'Закрыть меню' }));
    expect(panel.inert).toBe(true);
    expect(panel).toHaveAttribute('aria-hidden', 'true');
  });
});

it('provides a direct search page link on desktop and in the mobile menu', () => {
  render(<Header />);
  expect(screen.getAllByRole('link', { name: 'На страницу поиска', hidden: true }))
    .toHaveLength(2);
  for (const link of screen.getAllByRole('link', { name: 'На страницу поиска', hidden: true })) {
    expect(link).toHaveAttribute('href', '/search');
  }
  fireEvent.click(screen.getByRole('button', { name: 'Открыть меню' }));
  const mobileLink = screen.getAllByRole('link', { name: 'На страницу поиска' })[1];
  mobileLink.addEventListener('click', (event) => event.preventDefault());
  fireEvent.click(mobileLink);
  expect(screen.getByRole('button', { name: 'Открыть меню' })).toBeInTheDocument();
});
