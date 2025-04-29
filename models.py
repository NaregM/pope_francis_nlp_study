from pydantic import BaseModel, HttpUrl
from typing import Optional

# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------

class Speech(BaseModel):
    url: HttpUrl
    title: str
    text_body:str
    metadata: Optional[str] = None