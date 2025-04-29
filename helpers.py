import json
from pathlib import Path
from typing import List

from pydantic import BaseModel, HttpUrl
from typing import Optional

# re-define your model (or import it)
class Speech(BaseModel):
    url: HttpUrl
    title: str
    text_body: str
    metadata: Optional[str]

def load_all_speeches_json(dir_path: str) -> List[Speech]:
    """
    Reads every .json file in dir_path, assumes each is either:
      - a list of speech dicts, or
      - a single speech dict.
    Returns a flat list of Speech models.
    """
    out: List[Speech] = []
    data_dir = Path(dir_path)
    for json_file in data_dir.glob("*.json"):
        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # if it’s a list of speeches
        if isinstance(data, list):
            for item in data:
                out.append(Speech(**item))
        # or a single speech
        elif isinstance(data, dict):
            out.append(Speech(**data))
        else:
            raise ValueError(f"Unexpected JSON content in {json_file}")
    return out

