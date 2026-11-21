import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { SearchLayout } from './SearchLayout';

beforeEach(() => {
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false })));
});

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));
vi.mock('./SearchInput', () => ({ SearchInput: () => <input aria-label="Поиск" /> }));

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it('keeps the mobile filter panel usable without replacing the results', () => {
  const onFilterChange = vi.fn();
  render(
    <SearchLayout
      state={{ q: '', sort_by: 'min_price_asc', page: 1 }}
      controls={{
        onQueryChange: vi.fn(),
        onFilterChange,
        onPriceChange: vi.fn(),
        onSortChange: vi.fn(),
        onPageChange: vi.fn(),
        onReset: vi.fn(),
      }}
      facets={{
        devices: [],
        partTypes: [{ id: 7, label: 'Дисплей' }],
        qualityTiers: [],
      }}
      summary="Найдено: 1 товарная позиция"
    >
      <article>Предложение магазина</article>
    </SearchLayout>,
  );

  const toggle = screen.getByRole('button', { name: /^Фильтры/ });
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(document.getElementById(toggle.getAttribute('aria-controls')!)).not.toBeNull();
  fireEvent.click(toggle);
  expect(toggle).toHaveAttribute('aria-expanded', 'true');
  fireEvent.click(screen.getByRole('button', { name: 'Дисплей' }));
  expect(onFilterChange).toHaveBeenCalledWith('part_type_id', 7);
  fireEvent.click(toggle);
  expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(screen.getByText('Предложение магазина')).toBeInTheDocument();
});

it('routes desktop left-side wheel gestures to filters and contains them at the boundary', () => {
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => ({ matches: true })),
  );
  const view = render(
    <SearchLayout
      state={{ q: '', sort_by: 'min_price_asc', page: 1 }}
      controls={{
        onQueryChange: vi.fn(),
        onFilterChange: vi.fn(),
        onPriceChange: vi.fn(),
        onSortChange: vi.fn(),
        onPageChange: vi.fn(),
        onReset: vi.fn(),
      }}
      facets={{ devices: [], partTypes: [], qualityTiers: [] }}
      summary="Найдено: 1"
    >
      <article>Выдача</article>
    </SearchLayout>,
  );
  const main = screen.getByRole('main');
  vi.spyOn(main, 'getBoundingClientRect').mockReturnValue({ left: 400 } as DOMRect);
  Object.defineProperties(main, {
    clientHeight: { configurable: true, value: 500 },
    scrollHeight: { configurable: true, value: 1500 },
  });
  const panel = document.getElementById('catalog-filters-panel')!;
  const sidebar = panel.parentElement!.parentElement!;
  // jsdom has no scroll geometry; model a real scroll container with a 600px limit.
  let scrollTop = 0;
  Object.defineProperty(sidebar, 'scrollTop', {
    configurable: true,
    get: () => scrollTop,
    set: (value: number) => {
      scrollTop = Math.max(0, Math.min(600, value));
    },
  });
  const wheel = (init: WheelEventInit = {}) => {
    const event = new WheelEvent('wheel', {
      bubbles: true,
      cancelable: true,
      clientX: 50,
      clientY: 200,
      deltaY: 100,
      ...init,
    });
    document.dispatchEvent(event);
    return event;
  };

  expect(wheel().defaultPrevented).toBe(true);
  expect(sidebar.scrollTop).toBe(100);
  expect(main.scrollTop).toBe(0);
  expect(wheel({ clientX: 800 }).defaultPrevented).toBe(true);
  expect(main.scrollTop).toBe(100);
  expect(sidebar.scrollTop).toBe(100);
  main.scrollTop = 1000;
  expect(wheel({ clientX: 800 }).defaultPrevented).toBe(false);
  expect(main.scrollTop).toBe(1000);
  expect(sidebar.scrollTop).toBe(100);
  expect(wheel({ clientX: 800, deltaY: -100 }).defaultPrevented).toBe(true);
  expect(main.scrollTop).toBe(900);

  const footer = document.createElement('footer');
  document.body.append(footer);
  vi.spyOn(footer, 'getBoundingClientRect').mockReturnValue({ top: 700 } as DOMRect);
  vi.stubGlobal('scrollY', 500);
  const scrollBy = vi.fn();
  vi.stubGlobal('scrollBy', scrollBy);
  expect(wheel({ clientX: 800, deltaY: -100 }).defaultPrevented).toBe(true);
  expect(scrollBy).toHaveBeenCalledWith(0, -100);
  expect(main.scrollTop).toBe(900);
  footer.remove();

  expect(wheel({ ctrlKey: true }).defaultPrevented).toBe(false);
  expect(sidebar.scrollTop).toBe(100);
  sidebar.scrollTop = 600;
  expect(wheel().defaultPrevented).toBe(true);
  expect(sidebar.scrollTop).toBe(600);

  vi.mocked(window.matchMedia).mockReturnValue({ matches: false } as MediaQueryList);
  expect(wheel({ deltaY: -100 }).defaultPrevented).toBe(false);
  expect(sidebar.scrollTop).toBe(600);
  view.unmount();
  vi.mocked(window.matchMedia).mockReturnValue({ matches: true } as MediaQueryList);
  expect(wheel().defaultPrevented).toBe(false);
});

it('keeps filters below the header and above the footer when the document scrolls', () => {
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: true })));
  vi.stubGlobal('innerHeight', 900);
  render(
    <>
      <header>Шапка</header>
      <SearchLayout
        state={{ q: '', sort_by: 'min_price_asc', page: 1 }}
        controls={{
          onQueryChange: vi.fn(),
          onFilterChange: vi.fn(),
          onPriceChange: vi.fn(),
          onSortChange: vi.fn(),
          onPageChange: vi.fn(),
          onReset: vi.fn(),
        }}
        facets={{ devices: [], partTypes: [], qualityTiers: [] }}
        summary="Найдено: 1"
      >
        <article>Выдача</article>
      </SearchLayout>
    </>,
  );
  vi.spyOn(screen.getByRole('banner'), 'getBoundingClientRect').mockReturnValue({ bottom: 73 } as DOMRect);
  const panel = document.getElementById('catalog-filters-panel')!;
  const sidebar = panel.parentElement!.parentElement!;
  const frame = sidebar.parentElement!;
  vi.spyOn(frame, 'getBoundingClientRect').mockReturnValue({ top: -300, bottom: 500 } as DOMRect);

  fireEvent.scroll(window);
  expect(sidebar.style.height).toBe('419px');
  expect(sidebar.style.transform).toBe('translateY(381px)');
  const sidebarTop = -300 + 381;
  expect(sidebarTop).toBeGreaterThanOrEqual(73);
  expect(sidebarTop + Number.parseFloat(sidebar.style.height)).toBeLessThanOrEqual(500);

  vi.mocked(window.matchMedia).mockReturnValue({ matches: false } as MediaQueryList);
  fireEvent.resize(window);
  expect(sidebar.style.height).toBe('');
  expect(sidebar.style.transform).toBe('');
});
