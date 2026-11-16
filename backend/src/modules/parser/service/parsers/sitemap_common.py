import html as html_lib
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from src.modules.parser.service.base import ParseResult


class SitemapParserMixin:
    def _absolute(self, url: str | None) -> str:
        if not url:
            return ""
        return urljoin(self.base_url + "/", html_lib.unescape(url.strip()))

    def parse_sitemap_urls(self, xml: str) -> tuple[list[str], list[str]]:
        soup = BeautifulSoup(xml, "xml")
        nested = [
            self._absolute(loc.get_text(strip=True))
            for sitemap in soup.find_all("sitemap")
            for loc in sitemap.find_all("loc")
        ]
        nested_set = set(nested)
        pages = [
            self._absolute(loc.get_text(strip=True))
            for loc in soup.find_all("loc")
            if self._absolute(loc.get_text(strip=True)) not in nested_set
        ]
        return nested, pages

    async def collect_product_urls(
        self,
        client: httpx.AsyncClient,
        section: str | None = None,
    ) -> list[str]:
        pending = [(self._absolute(self.sitemap_path), 0)]
        collected: list[str] = []
        visited: set[str] = set()
        while pending:
            url, depth = pending.pop(0)
            if url in visited or depth > self.max_sitemap_depth:
                continue
            visited.add(url)
            xml = await self._fetch(client, url)
            if xml is None:
                continue
            try:
                nested, pages = self.parse_sitemap_urls(xml)
            except Exception as exc:
                self.errors.append(f"sitemap parse failed: {url} ({exc})")
                continue
            collected.extend(pages)
            pending.extend((child, depth + 1) for child in nested)
        return self.filter_product_urls(collected, section)

    async def parse_product(self, url: str) -> ParseResult | None:
        async with self._session() as client:
            html = await self._fetch(client, url)
        if html is None:
            return None
        try:
            return self.parse_product_html(html, url)
        except Exception as exc:
            self.errors.append(f"parse failed: {url} ({exc})")
            return None

    async def parse_catalog_batch(self, urls: list[str]) -> list[ParseResult]:
        async with self._session() as client:
            return await self._parse_many(client, urls)
