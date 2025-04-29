import numpy as np
from typing import Set

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import calendar

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

CONCURRENCY = 5 

async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """
    Fetches the URL and returns the response body as text.
    """
    async with session.get(url) as resp:
        
        resp.raise_for_status()
        
        return await resp.text()


async def extract_links_from_index(session: aiohttp.ClientSession,
                                   sem: asyncio.Semaphore,
                                   index_url: str) -> Set[str]:
    """
    Fetch an index page and parse out English speech URLs.
    """
    async with sem:
        html = await fetch(session, index_url)

    soup = BeautifulSoup(html, "html.parser")
    links = set()
    
    for a in soup.find_all("a", string="English"):
        
        href = a.get("href", "")
        if "/content/francesco/en/speeches/" in href and href.endswith(".html"):
            
            links.add(urljoin(index_url, href))
            
    return links


async def main() -> None:
    """
    """
    semaphore = asyncio.Semaphore(CONCURRENCY)
    months = [m.lower() for m in calendar.month_name if m]
    
    index_urls = [
        f"https://www.vatican.va/content/francesco/en/speeches/{year}/{month}.index.html"
        for year in range(2015, 2026)
        for month in months
    ]

    async with aiohttp.ClientSession() as session:
        # scrape all index pages concurrently (but limited by semaphore)
        index_tasks = [
            extract_links_from_index(session, semaphore, idx)
            for idx in index_urls
        ]
        results = await asyncio.gather(*index_tasks, return_exceptions=True)

    # collect successes, ignore pages that 404’d or errored
    all_urls = set()
    for res in results:
        if isinstance(res, set):
            all_urls.update(res)

    # save all the links to scrape later
    with open("data/speech_urls.txt", "w") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    print(f"Found {len(all_urls)} unique English speeches.")


# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------

if __name__ == "__main__":
    
    asyncio.run(main())
