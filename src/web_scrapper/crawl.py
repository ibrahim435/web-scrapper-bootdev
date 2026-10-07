from typing import TypedDict
from urllib.parse import urljoin, urlsplit

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup, Tag


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

def extract_page_data(html:str, page_url:str) -> PageData:
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }

def normalize_url(source_url: str) -> str:
    parts = urlsplit(source_url)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()

# Remove default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    # Remove trailing slashes, but keep a completely empty path as empty
    path = parts.path.rstrip("/")

    # Build normalized URL without scheme or fragment
    normalized = netloc + path if path else netloc

    # Query strings can change the page, so preserve them
    if parts.query:
        normalized += "?" + parts.query

    return normalized

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if isinstance(h1, Tag):
        return h1.get_text(strip=True)
    h2 = soup.find("h2")
    if isinstance(h2, Tag):
        return h2.get_text(strip=True)
    return ""

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if isinstance(main, Tag):
        p = main.find("p")
        if isinstance(p, Tag):
            return p.get_text(strip=True)
    p = soup.find("p")
    if isinstance(p, Tag):
        return p.get_text(strip=True)
    return ""


def get_urls_from_html(html:str,base_url:str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if isinstance(href, str) and href:
            urls.append(urljoin(base_url,href))
    return urls

def get_images_from_html(html:str,base_url:str)-> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    imgs = []

    for img in soup.find_all("img"):
        src = img.get("src")
        if isinstance(src, str) and src:
            imgs.append(urljoin(base_url, src))
    return imgs

def get_html(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    if response.status_code >= 400:
        raise Exception(f"failed to fecth page: HTTP status {response.status_code}")

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise Exception(f"expected text/html content-type, got: {content_type}")
    return response.text


def crawl_page(
    base_url: str,
    current_url: str | None = None,
    page_data: dict[str, PageData] | None = None,
) -> dict[str, PageData]:
    if current_url is None:
        current_url = base_url
    if page_data is None:
        page_data = {}


    base_domain = urlsplit(base_url).netloc
    current_domain = urlsplit(current_url).netloc
    if base_domain != current_domain:
        return page_data

    normalized_url = normalize_url(current_url)
    if normalized_url in page_data:
        return page_data

    print(f"crawling: {current_url}")
    try:
        html = get_html(current_url)
    except Exception as e:
        print(f"error fetching {current_url}: {e}")
        return page_data

    data = extract_page_data(html, current_url)
    page_data[normalized_url] = data

    for link in data["outgoing_links"]:
        crawl_page(base_url,link, page_data)

    return page_data


class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int, max_pages: int):
        self.base_url = base_url
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.visited: set [str] = set()
        self.page_data: dict[str, PageData] = {}
        self.should_stop = False
        self.all_tasks: set[asyncio.Task] = set()
        self.session: aiohttp.ClientSession | None = None

    def add_page_visit(self, normalized_url: str) -> bool:
        if self.should_stop:
            return False
        if len(self.visited) >= self.max_pages:
            self.should_stop = True
            print("Reaching maximum number of pages to crawl.")
            return False
        if normalized_url in self.visited:
            return False
        self.visited.add(normalized_url)
        return True

    async def get_html(self, url: str) -> str:
        if self.session is None:
            raise Exception("crawler session is not open")
        async with self.semaphore:
            async with self.session.get(url, headers={"User-Agent": "BootCrawler/1.0"}) as resp:
                if resp.status >= 400:
                    raise Exception(f"failed to fetch page: HTTP status {resp.status}")
                content_type = resp.headers.get("content-type", "")
                if "text/html" not in content_type:
                    raise Exception(f"expected text/html content-type, got: {content_type}")

                return await resp.text()

    async def crawl_page(self, base_url: str, current_url: str) -> None:
        if self.should_stop:
            return

        base_domain = urlsplit(base_url).netloc
        current_domain = urlsplit(current_url).netloc
        if base_domain != current_domain:
            return

        normalized_url = normalize_url(current_url)
        if not self.add_page_visit(normalized_url):
            return

        print(f"crawling: {current_url}")
        try:
            html = await self.get_html(current_url)
        except Exception as e:
            print(f"error fetching {current_url}: {e}")
            return

        data = extract_page_data(html, current_url)
        self.page_data[normalized_url] = data

        tasks: list[asyncio.Task] = []
        for link in data["outgoing_links"]:
            task = asyncio.create_task(self.crawl_page(base_url, link))
            self.all_tasks.add(task)
            tasks.append(task)

        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                self.all_tasks.discard(task)


    async def crawl(self) -> dict[str, PageData]:
        async with aiohttp.ClientSession() as session:
            self.session = session
            root = asyncio.create_task(self.crawl_page(self.base_url, self.base_url))
            self.all_tasks.add(root)
            try:
                await root
            finally:
                self.all_tasks.discard(root)
        return self.page_data
