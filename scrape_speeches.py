import numpy as np
import re
from typing import List, Set
from pydantic import BaseModel, HttpUrl
from tqdm import tqdm

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import asyncio

from models import Speech

# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------

async def fetch(session: ClientSession, url: HttpUrl) -> str:
    """
    """
    async with session.get(url) as resp:
        
        resp.raise_for_status()
        return await resp.text()
    

async def parse_speech(
    session: ClientSession,
    sem: asyncio.Semaphore,
    url: HttpUrl
) -> Speech:
    """
    """
    async with sem:
        html = await fetch(session, url)
        
    soup = BeautifulSoup(html, "html.parser")
    header = soup.find("h1") or soup.find("h2")
    title = header.get_text(strip = True) if header else ""
    
    date_match = re.search(
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+\d{1,2}\s+\w+\s+\d{4}\b",
        html
    )
    metadata = date_match.group(0) if date_match else None

    divider = soup.find(string=re.compile(r"\*\s*\*\s*\*"))
    start = divider.parent if divider else soup
    paragraphs = [
        p.get_text(strip=True)
        for p in start.find_all_next("p")
        if p.get_text(strip=True) and "© Dicastero per la Comunicazione" not in p.text
    ]
    text_body = "\n\n".join(paragraphs).strip()

    return Speech(url=url, title=title, text_body=text_body, metadata=metadata)

async def scrape_speeches(
    urls: List[HttpUrl],
    concurrency: int = 5
) -> List[Speech]:
    """
    """
    sem = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        
        tasks = [asyncio.create_task(parse_speech(session, sem, url)) for url in urls]
        
        speeches: List[Speech] = []
        
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Scraping speeches"):
            try:
                speech = await task
                speeches.append(speech)
            except Exception as e:
                # handle or log e if you want
                pass
            
    return speeches