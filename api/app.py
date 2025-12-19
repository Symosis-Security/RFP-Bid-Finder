# api/app.py
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from bids import run_search
from cache import SimpleCache

load_dotenv()

APP_DB = os.environ.get("GOV_BIDS_DB", "gov_bids_cache.sqlite3")
CACHE = SimpleCache(APP_DB)

SAM_API_KEY = os.environ.get("SAM_API_KEY", "").strip()
SIMPLER_GRANTS_API_KEY = os.environ.get("SIMPLER_GRANTS_API_KEY", "").strip()
DATA_GOV_API_KEY = os.environ.get("DATA_GOV_API_KEY", "").strip()

cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]


class SearchBody(BaseModel):
    sources: List[str] = Field(default_factory=list)
    keyword: str = ""
    days_back: int = 30
    max_rows: int = 50
    timeout_s: int = 20
    cache_ttl_s: int = 900
    fpds_atom_url: str = ""
    socrata_dataset_url: str = ""


app = FastAPI(title="US Gov Bids API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@app.post("/search")
def search(body: SearchBody) -> Dict[str, Any]:
    items, debug = run_search(
        cache=CACHE,
        sam_api_key=SAM_API_KEY,
        simpler_api_key=SIMPLER_GRANTS_API_KEY,
        data_gov_api_key=DATA_GOV_API_KEY,
        sources=body.sources or [],
        keyword=(body.keyword or "").strip(),
        days_back=int(body.days_back),
        max_rows=int(body.max_rows),
        timeout_s=int(body.timeout_s),
        cache_ttl_s=int(body.cache_ttl_s),
        fpds_atom_url=(body.fpds_atom_url or "").strip(),
        socrata_dataset_url=(body.socrata_dataset_url or "").strip(),
    )
    return {"items": items, "debug": debug}
