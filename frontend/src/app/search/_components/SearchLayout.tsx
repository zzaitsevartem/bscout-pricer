import { useRouter } from 'next/navigation';
import React, { useEffect, useRef, useState, type ReactNode } from 'react';
import Link from 'next/link';
import type { CatalogSortOption } from '@/models/catalog';
import { SearchInput } from '@/app/search/_components/SearchInput';
import { SearchFilters } from '@/app/search/_components/SearchFilters';
import { SORT_OPTIONS } from '@/app/search/_components/lib';
import { cn } from '@/shared/lib/utils';
import type {
  CatalogFacets,
  FilterKey,
  FilterOption,
  SearchControls,
  SearchUrlState,
} from '@/app/search/_components/lib';

function labelFor(options: FilterOption[], id: number): string {
  return options.find((option) => option.id === id)?.label ?? `#${id}`;
}

type SearchLayoutProps = {
  deviceMode?: boolean;
  state: SearchUrlState;
  controls: SearchControls;
  facets: CatalogFacets;
  summary: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  suggestionsEnabled?: boolean;
};

export function SearchLayout({
  state,
  controls,
  facets,
  summary,
  actions,
  children,
  suggestionsEnabled = false,
  deviceMode = false,
}: SearchLayoutProps) {
  const sidebarRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (deviceMode) return;

    const fitSidebar = () => {
      const sidebar = sidebarRef.current;
      const frame = sidebar?.parentElement;
      if (!sidebar || !frame) return;
      if (!window.matchMedia?.('(min-width: 1024px)').matches) {
        sidebar.style.removeProperty('height');
        sidebar.style.removeProperty('transform');
        return;
      }
      const bounds = frame.getBoundingClientRect();
      const headerBottom = document.querySelector('header')?.getBoundingClientRect().bottom ?? 73;
      const top = Math.max(bounds.top, headerBottom + 8);
      sidebar.style.height = `${Math.max(0, Math.min(bounds.bottom, window.innerHeight - 32) - top)}px`;
      sidebar.style.transform = `translateY(${Math.max(0, top - bounds.top)}px)`;
    };
    fitSidebar();
    window.addEventListener('scroll', fitSidebar, { passive: true });
    window.addEventListener('resize', fitSidebar);
    const routeWheel = (event: WheelEvent) => {
      if (event.ctrlKey || !window.matchMedia?.('(min-width: 1024px)').matches) return;
      const sidebar = sidebarRef.current;
      const results = resultsRef.current;
      if (!sidebar || !results) return;
      const headerBottom = document.querySelector('header')?.getBoundingClientRect().bottom ?? 0;
      if (event.clientY < headerBottom) return;
      const footer = document.querySelector('footer');
      if (event.deltaY < 0 && window.scrollY > 0 && footer) {
        const footerTop = footer.getBoundingClientRect().top;
        if (footerTop < window.innerHeight) {
          event.preventDefault();
          const scale = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerHeight : 1;
          window.scrollBy(0, event.deltaY * scale);
          return;
        }
      }
      if (event.clientX >= results.getBoundingClientRect().left) {
        const canScroll = event.deltaY < 0
          ? results.scrollTop > 0
          : results.scrollTop + results.clientHeight < results.scrollHeight - 1;
        if (canScroll) {
          event.preventDefault();
          const scale = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? results.clientHeight : 1;
          results.scrollTop += event.deltaY * scale;
        }
        return;
      }
      if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
      event.preventDefault();
      const scale = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? sidebar.clientHeight : 1;
      sidebar.scrollTop += event.deltaY * scale;
    };
    document.addEventListener('wheel', routeWheel, { passive: false, capture: true });
    return () => {
      document.removeEventListener('wheel', routeWheel, true);
      window.removeEventListener('scroll', fitSidebar);
      window.removeEventListener('resize', fitSidebar);
    };
  }, [deviceMode]);

  const router = useRouter();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const chips: { key: FilterKey; label: string }[] = [];
  if (!deviceMode && state.device_id !== undefined) {
    chips.push({ key: 'device_id', label: labelFor(facets.devices, state.device_id) });
  }
  if (state.part_type_id !== undefined) {
    chips.push({ key: 'part_type_id', label: labelFor(facets.partTypes, state.part_type_id) });
  }
  if (state.quality_tier_id !== undefined) {
    chips.push({
      key: 'quality_tier_id',
      label: labelFor(facets.qualityTiers, state.quality_tier_id),
    });
  }

  if (state.store)
    chips.push({
      key: 'store',
      label: facets.stores?.find((store) => store.slug === state.store)?.name ?? state.store,
    });
  if (state.min_price !== undefined)
    chips.push({ key: 'min_price', label: `От ${state.min_price} ₽` });
  if (state.max_price !== undefined)
    chips.push({ key: 'max_price', label: `До ${state.max_price} ₽` });
  if (state.in_stock !== undefined)
    chips.push({ key: 'in_stock', label: state.in_stock ? 'В наличии' : 'Нет в наличии' });

  return (
    <div className="search-palette max-w-[1200px] mx-auto px-6 max-sm:px-4">
      <div className={cn(
        'grid grid-cols-[264px_1fr] gap-8 py-8 max-sm:gap-6 max-sm:py-6 min-h-[calc(100vh-64px)] max-lg:grid-cols-1 max-lg:content-start',
        !deviceMode && 'lg:h-[calc(100dvh-73px)] lg:min-h-0 lg:overflow-hidden',
      )}>
        <div className="min-w-0 lg:min-h-0">
          <div
            ref={sidebarRef}
            className={cn(
              'self-start scrollbar-hidden',
              !deviceMode && 'lg:h-full lg:overflow-y-auto lg:overscroll-y-contain',
            )}
          >
            <div className="rounded-2xl bg-search-row p-4 lg:bg-transparent lg:p-0">
              <button
                type="button"
                className="flex min-h-11 w-full items-center justify-between rounded-lg font-semibold text-slate focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate lg:hidden"
                aria-expanded={filtersOpen}
                aria-controls="catalog-filters-panel"
                onClick={() => setFiltersOpen((open) => !open)}
              >
                Фильтры{chips.length > 0 ? ` (${chips.length})` : ''}
                <span aria-hidden="true">{filtersOpen ? '−' : '+'}</span>
              </button>
              <div
                id="catalog-filters-panel"
                className={cn('mt-4 lg:mt-0 lg:block', !filtersOpen && 'hidden')}
              >
                <SearchFilters
                  facets={deviceMode ? { ...facets, devices: [] } : facets}
                  state={deviceMode ? { ...state, device_id: undefined } : state}
                  onFilterChange={controls.onFilterChange}
                  onPriceChange={controls.onPriceChange}
                  onReset={controls.onReset}
                  hasActiveFilters={chips.length > 0}
                />
              </div>
            </div>
          </div>

        </div>

        <main
          ref={resultsRef}
          className={cn(
            'min-w-0 scrollbar-hidden',
            !deviceMode && 'lg:min-h-0 lg:overflow-y-auto',
          )}
        >
          {!deviceMode && (
            <div className="flex items-center gap-2 text-[14px] text-body-muted mb-4 flex-wrap">
              <Link
                href="/"
                className="text-body-subtle no-underline hover:text-slate hover:underline"
              >
                Главная
              </Link>
              <span className="text-body-muted">/</span>
              <span>Поиск</span>
            </div>
          )}

          <SearchInput
            query={state.q}
            onQueryChange={controls.onQueryChange}
            onDeviceSelect={(device) =>
              router.push(`/devices/${encodeURIComponent(device.model_key)}`)
            }
            suggestionsEnabled={suggestionsEnabled}
            filters={{
              store: state.store,
              min_price: state.min_price,
              max_price: state.max_price,
              in_stock: state.in_stock,
              device_id: state.device_id,
              part_type_id: state.part_type_id,
              quality_tier_id: state.quality_tier_id,
            }}
          />

          {chips.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap mb-4">
              {chips.map((chip) => (
                <button
                  key={chip.key}
                  type="button"
                  onClick={() => controls.onFilterChange(chip.key, null)}
                  className="inline-flex items-center gap-2 rounded-full text-[14px] text-slate bg-ivory-elevated border border-border-subtle px-3 py-1 transition-colors hover:bg-ivory-warm"
                >
                  {chip.label}
                  <span aria-hidden="true">×</span>
                  <span className="sr-only">Убрать фильтр</span>
                </button>
              ))}
              <button
                type="button"
                onClick={controls.onReset}
                className="min-h-11 text-[14px] text-body-subtle underline underline-offset-[3px] hover:text-slate focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate"
              >
                Сбросить всё
              </button>
            </div>
          )}

          <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
            <span className="text-[15px] text-body-subtle">{summary}</span>
            <div className="flex items-center gap-4 flex-wrap">
              {actions}
              <div className="flex items-center gap-2">
                <label htmlFor="catalog-sort" className="text-[15px] text-body-subtle">
                  Сортировка:
                </label>
                <div className="relative">
                  <select
                    id="catalog-sort"
                    value={state.sort_by}
                    onChange={(event) =>
                      controls.onSortChange(event.target.value as CatalogSortOption)
                    }
                    className="appearance-none rounded-full pr-9 pl-3 py-2 text-[15px] text-slate bg-ivory border border-border-input transition-colors search-control"
                  >
                    {SORT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 w-0 h-0 border-l-[5px] border-r-[5px] border-t-[5px] border-body-subtle pointer-events-none" />
                </div>
              </div>
            </div>
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}
