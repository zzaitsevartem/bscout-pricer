import html as html_lib
import re

from bs4 import BeautifulSoup


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def extract_canonical(soup: BeautifulSoup) -> str:
    link = soup.select_one("link[rel=canonical]")
    if link is not None and link.get("href"):
        return html_lib.unescape(link.get("href").strip())
    meta = soup.select_one('meta[property="og:url"]')
    if meta is not None and meta.get("content"):
        return html_lib.unescape(meta.get("content").strip())
    return ""


def extract_breadcrumbs(soup: BeautifulSoup) -> list[str]:
    crumbs: list[str] = []
    for node in soup.select("[itemprop=itemListElement] [itemprop=name]"):
        text = clean_text(node.get("content") or node.get_text(" ", strip=True))
        if text and text.lower() != "главная":
            crumbs.append(text)
    return crumbs

