import { describe, expect, it } from 'vitest';
import { apiErrorMessage as admin } from '@/app/admin/_components/lib';
import { apiErrorMessage as product } from '@/app/product/[id]/_components/lib';
import { apiErrorMessage as search } from '@/app/search/_components/lib';

describe.each([admin, product, search])('API error message', (message) => {
  it('returns nonempty Axios detail and falls back otherwise', () => {
    const error = (detail: unknown) => ({ isAxiosError: true, response: { data: { detail } } });
    expect(message(error('Ошибка'), 'fallback')).toBe('Ошибка');
    expect(message(error(' '), 'fallback')).toBe(' ');
    expect(message(error(''), 'fallback')).toBe('fallback');
    expect(message(error(['Ошибка']), 'fallback')).toBe('fallback');
    expect(message({ isAxiosError: true }, 'fallback')).toBe('fallback');
    expect(message({ response: { data: { detail: 'Ошибка' } } }, 'fallback')).toBe('fallback');
  });
});
