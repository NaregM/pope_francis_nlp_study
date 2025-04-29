import numpy as np
import re
from typing import List, Set
from pydantic import BaseModel, HttpUrl
from tqdm import tqdm

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import asyncio

import json
from pathlib import Path

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

    header = soup.find("h1") or soup.find("h2")
    if header and header.get_text(strip=True):
        title = header.get_text(strip=True)
        # then fall back to <p> parsing for body as before...
        paras = [
            p.get_text(" ", strip=True)
            for p in soup.find_all("p")
            if p.get_text(strip=True)
               and "Dicastero per la Comunicazione" not in p.text
        ]
        text_body = "\n\n".join(paras).strip()

    else:
        # Minimal-markup case: everything lives under div.text.parbase.vaticanrichtext
        container = soup.find("div", class_="text parbase vaticanrichtext")
        if not container:
            # ultimate fallback: raw-text split
            raw = soup.get_text("\n")
            text_body = "\n\n".join([ln for ln in raw.splitlines() if ln.strip()])
            title = ""
        else:
            # Title = first centered <p>
            p_center = container.find("p", align="center")
            title = p_center.get_text(" ", strip=True) if p_center else ""

            # Body = all other <p> after that one
            paras = []
            seen_title = False
            # new: also skip the “[ Multimedia ]” line
            paras = []
            for p in soup.find_all("p"):
                txt = p.get_text(" ", strip=True)
                if not txt:
                    continue
                if "Dicastero per la Comunicazione" in txt:
                    continue
                if txt == "[ Multimedia ]":
                    continue
                paras.append(txt)
            text_body = "\n\n".join(paras).strip()

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


# ---------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    
    urls = [u.strip() for u in open("data/speech_urls.txt")][:]
    all_speeches = asyncio.run(scrape_speeches(urls, concurrency=10))

    out_path = Path("data/speeches.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w") as f:
        
        # default=str to handle HttpUrl
        json.dump([s.model_dump() for s in all_speeches], f, indent=2, default=str)