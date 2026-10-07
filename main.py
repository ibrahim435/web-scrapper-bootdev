import sys
import asyncio
from src.web_scrapper.crawl import get_html, crawl_page, AsyncCrawler
from src.web_scrapper.json_report import write_json_report

def main() -> None:
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    if len(sys.argv) > 4:
        print("too many arguments provided")
        sys.exit(1)

    base_url= sys.argv[1]
    try:
        max_concurrency = int(sys.argv[2]) if len(sys.argv) >=3 else 3
        max_pages = int(sys.argv[3]) if len(sys.argv) == 4 else 10
    except ValueError:
        print("max_concurrency and max_pages must be integers")
        sys.exit(1)
    print(f"starting crawl of: {base_url}")

    #html = get_html(base_url)
    #print(html)
    #page_data = crawl_page(base_url)
    #print(f"\ncrawled {len(page_data)} pages")
    #for data in page_data.values():
    #    print(f"- {data['url']}")
    #    print(f" heading: {data['heading']}")
    #    print(f" first paragraph: {data['first_paragraph']}")
    #    print(f" links: {len(data['outgoing_links'])}, images: {len(data['image_urls'])}")
    crawler = AsyncCrawler(base_url, max_concurrency, max_pages)
    page_data = asyncio.run(crawler.crawl())

    write_json_report(page_data)
    print(f"crawled {len(page_data)} pages, wrote repot.json")

if __name__ == "__main__":
    main()
