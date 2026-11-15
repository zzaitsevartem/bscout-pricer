import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import RegisterPage from './page';

const state = vi.hoisted(() => ({ push: vi.fn(), mutate: vi.fn(), query: '' }));
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: state.push }),
  useSearchParams: () => new URLSearchParams(state.query),
}));
vi.mock('@/widgets/Header/ui/Header', () => ({ Header: () => null }));
vi.mock('@/shared/ui/PageTransition', () => ({
  PageTransition: ({ children }: { children: React.ReactNode }) => children,
}));
vi.mock('@/models/payment', () => ({ usePlans: () => ({ data: [] }) }));
vi.mock('@/models/auth', async (original) => ({
  ...(await original<object>()),
  useRegister: () => ({ mutate: state.mutate, isPending: false }),
}));

async function submit() {
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'new@example.com' } });
  fireEvent.change(screen.getByLabelText('Имя и фамилия'), { target: { value: 'Иван' } });
  fireEvent.change(screen.getByLabelText('Пароль', { exact: true }), {
    target: { value: 'long-password-123' },
  });
  fireEvent.change(screen.getByLabelText('Подтвердите пароль'), {
    target: { value: 'long-password-123' },
  });
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: 'Создать аккаунт' }));
  await waitFor(() => expect(state.mutate).toHaveBeenCalledOnce());
}

beforeEach(() => {
  vi.clearAllMocks();
  state.query = '';
});

describe('selected registration plan', () => {
  it.each(['basic', 'advanced'])('returns to checkout for %s only after success', async (plan) => {
    state.query = `plan=${plan}`;
    render(<RegisterPage />);
    await submit();
    expect(state.push).not.toHaveBeenCalled();
    const [body, options] = state.mutate.mock.calls[0];
    expect(body).not.toHaveProperty('plan');
    options.onSuccess();
    expect(state.push).toHaveBeenCalledWith(`/subscription?plan=${plan}`);
  });

  it.each(['', 'plan=trial', 'plan=admin', 'plan=https://evil.test', 'plan=ADVANCED'])(
    'rejects invalid plan %s',
    async (query) => {
      state.query = query;
      render(<RegisterPage />);
      await submit();
      state.mutate.mock.calls[0][1].onSuccess();
      expect(state.push).toHaveBeenCalledWith('/account');
    },
  );
});
