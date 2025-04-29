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
    
