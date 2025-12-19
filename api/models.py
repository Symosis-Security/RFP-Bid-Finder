from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Item:
    source: str
    title: str
    buyer: str
    posted_date: str
    due_date: str
    url: str
    item_id: str
    raw: Dict[str, Any]


@dataclass
class SearchRequest:
    sources: List[str]
    keyword: str
    days_back: int
    max_rows: int
    timeout_s: int
    cache_ttl_s: int
    fpds_atom_url: Optional[str] = ""
    socrata_dataset_url: Optional[str] = ""


@dataclass
class SearchResponse:
    items: List[Dict[str, Any]]
    debug: Dict[str, Any]
