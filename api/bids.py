# api/bids.py
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from urllib.parse import quote_plus

import feedparser
import requests
from dateutil import parser as dtparser

from cache import SimpleCache
from models import Item


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _safe_get(d: Dict[str, Any], path: List[Any], default: Any = "") -> Any:
    cur: Any = d
    for p in path:
        if isinstance(p, int):
            if isinstance(cur, list) and 0 <= p < len(cur):
                cur = cur[p]
            else:
                return default
        else:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                return default
    return cur


def _fmt_date_any(s: Any) -> str:
    if not s:
        return ""
    if isinstance(s, (int, float)):
        try:
            return datetime.utcfromtimestamp(int(s)).strftime("%Y-%m-%d")
        except Exception:
            return str(s)
    if isinstance(s, str):
        s2 = s.strip()
        if not s2:
            return ""
        try:
            return dtparser.parse(s2).date().isoformat()
        except Exception:
            return s2
    return str(s)


def _mmddyyyy(d: datetime) -> str:
    return d.strftime("%m/%d/%Y")


def _http_json_or_text(r: requests.Response) -> Dict[str, Any]:
    ct = (r.headers.get("content-type") or "").lower()
    if ct.startswith("application/json"):
        try:
            return r.json()
        except Exception:
            return {"text": r.text}
    return {"text": r.text}


def _ensure_http_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    if u.startswith("http://") or u.startswith("https://"):
        return u
    return u


def _sam_view_url(notice_id: str) -> str:
    nid = (notice_id or "").strip()
    if not nid:
        return ""
    return f"https://sam.gov/opp/{nid}/view"


def _grants_view_url(opportunity_id: str) -> str:
    oid = (opportunity_id or "").strip()
    if not oid:
        return ""
    return f"https://www.grants.gov/search-results-detail/{oid}"


def _usaspending_award_url(award_id: str) -> str:
    aid = (award_id or "").strip()
    if not aid:
        return ""
    return f"https://www.usaspending.gov/award/{aid}"


def fetch_sam_opportunities(
    cache: SimpleCache,
    api_key: str,
    keyword: str,
    posted_from: datetime,
    posted_to: datetime,
    limit: int,
    timeout_s: int,
    cache_ttl_s: int,
) -> Tuple[List[Item], Dict[str, Any]]:
    if not api_key:
        return [], {"error": "SAM_API_KEY not set"}

    base_url = "https://api.sam.gov/opportunities/v2/search"
    params: Dict[str, Any] = {
        "api_key": api_key,
        "postedFrom": _mmddyyyy(posted_from),
        "postedTo": _mmddyyyy(posted_to),
        "limit": max(1, min(int(limit), 1000)),
        "offset": 0,
    }
    if keyword.strip():
        params["title"] = keyword.strip()

    cache_key = _sha("sam|" + json.dumps(params, sort_keys=True))
    cached = cache.get(cache_key, cache_ttl_s)
    if cached:
        return _parse_sam_items(cached), cached

    r = requests.get(base_url, params=params, timeout=timeout_s)
    payload: Dict[str, Any] = _http_json_or_text(r)
    payload["_http_status"] = r.status_code
    payload["_request_url"] = r.url

    if r.status_code == 200:
        cache.set(cache_key, payload)

    return _parse_sam_items(payload), payload


def _parse_sam_items(payload: Dict[str, Any]) -> List[Item]:
    items: List[Item] = []
    data = payload.get("opportunitiesData") or payload.get("data") or []
    if not isinstance(data, list):
        return items

    for row in data:
        if not isinstance(row, dict):
            continue

        title = row.get("title") or ""
        solnum = row.get("solicitationNumber") or row.get("solnum") or ""
        posted = row.get("postedDate") or ""
        due = row.get("responseDeadLine") or row.get("reponseDeadLine") or row.get("rdl") or ""
        buyer = row.get("fullParentPathName") or row.get("organizationName") or ""
        notice_id = row.get("noticeId") or row.get("noticeid") or solnum or title

        url = row.get("uiLink") or row.get("link") or ""
        url = _ensure_http_url(str(url))
        if not url and notice_id:
            url = _sam_view_url(str(notice_id))

        items.append(
            Item(
                source="SAM.gov",
                title=str(title),
                buyer=str(buyer),
                posted_date=_fmt_date_any(posted),
                due_date=_fmt_date_any(due),
                url=str(url),
                item_id=str(notice_id),
                raw=row,
            )
        )
    return items


def fetch_grants_gov(
    cache: SimpleCache,
    keyword: str,
    rows: int,
    timeout_s: int,
    cache_ttl_s: int,
) -> Tuple[List[Item], Dict[str, Any]]:
    base_url = "https://api.grants.gov/v1/api/search2"
    body: Dict[str, Any] = {
        "rows": max(1, min(int(rows), 100)),
        "keyword": keyword.strip() if keyword.strip() else "",
        "oppStatuses": "forecasted|posted",
        "startRecordNum": 0,
    }

    cache_key = _sha("grantsgov|" + json.dumps(body, sort_keys=True))
    cached = cache.get(cache_key, cache_ttl_s)
    if cached:
        return _parse_grants_gov_items(cached), cached

    r = requests.post(base_url, json=body, timeout=timeout_s)
    payload: Dict[str, Any] = _http_json_or_text(r)
    payload["_http_status"] = r.status_code
    payload["_request_url"] = base_url
    payload["_request_body"] = body

    if r.status_code == 200:
        cache.set(cache_key, payload)

    return _parse_grants_gov_items(payload), payload


def _parse_grants_gov_items(payload: Dict[str, Any]) -> List[Item]:
    items: List[Item] = []
    data = payload.get("data") or {}
    hits = data.get("oppHits") or []
    if not isinstance(hits, list):
        return items

    for row in hits:
        if not isinstance(row, dict):
            continue
        title = row.get("title") or ""
        number = row.get("number") or row.get("oppNum") or ""
        agency = row.get("agencyName") or row.get("agencyCode") or ""
        posted = row.get("openDate") or ""
        due = row.get("closeDate") or ""

        opp_id = row.get("id") or row.get("opportunityId") or ""
        item_id = opp_id or number or title

        url = _grants_view_url(str(opp_id)) if opp_id else ""
        if not url and number:
            # fallback: at least take user to grants.gov search for the opp number
            url = f"https://www.grants.gov/search-grants?keywords={quote_plus(str(number))}"

        items.append(
            Item(
                source="Grants.gov",
                title=str(title),
                buyer=str(agency),
                posted_date=_fmt_date_any(posted),
                due_date=_fmt_date_any(due),
                url=str(url),
                item_id=str(item_id),
                raw=row,
            )
        )
    return items


def fetch_simpler_grants(
    cache: SimpleCache,
    api_key: str,
    keyword: str,
    rows: int,
    timeout_s: int,
    cache_ttl_s: int,
) -> Tuple[List[Item], Dict[str, Any]]:
    if not api_key:
        return [], {"error": "SIMPLER_GRANTS_API_KEY not set"}

    base_url = "https://api.simpler.grants.gov/v1/opportunities/search"
    body: Dict[str, Any] = {
        "query": keyword.strip() if keyword.strip() else "",
        "filters": {"opportunity_status": {"one_of": ["posted", "forecasted"]}},
        "pagination": {
            "page_offset": 1,
            "page_size": max(1, min(int(rows), 100)),
            "sort_order": [{"order_by": "opportunity_id", "sort_direction": "descending"}],
        },
    }
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    cache_key = _sha("simpler|" + json.dumps(body, sort_keys=True))
    cached = cache.get(cache_key, cache_ttl_s)
    if cached:
        return _parse_simpler_items(cached), cached

    r = requests.post(base_url, headers=headers, json=body, timeout=timeout_s)
    payload: Dict[str, Any] = _http_json_or_text(r)
    payload["_http_status"] = r.status_code
    payload["_request_url"] = base_url
    payload["_request_body"] = body

    if r.status_code == 200:
        cache.set(cache_key, payload)

    return _parse_simpler_items(payload), payload


def _parse_simpler_items(payload: Dict[str, Any]) -> List[Item]:
    items: List[Item] = []
    data = payload.get("data") or []
    if not isinstance(data, list):
        return items

    for row in data:
        if not isinstance(row, dict):
            continue
        title = row.get("opportunity_title") or row.get("title") or ""
        buyer = row.get("agency_name") or row.get("top_level_agency") or ""
        posted = row.get("post_date") or row.get("posted_date") or ""
        due = row.get("close_date") or row.get("application_deadline") or ""
        url = row.get("opportunity_url") or row.get("listing_url") or ""
        item_id = row.get("opportunity_id") or row.get("id") or title

        items.append(
            Item(
                source="Simpler.Grants.gov",
                title=str(title),
                buyer=str(buyer),
                posted_date=_fmt_date_any(posted),
                due_date=_fmt_date_any(due),
                url=_ensure_http_url(str(url)),
                item_id=str(item_id),
                raw=row,
            )
        )
    return items


def fetch_usaspending_awards(
    cache: SimpleCache,
    keyword: str,
    rows: int,
    timeout_s: int,
    cache_ttl_s: int,
) -> Tuple[List[Item], Dict[str, Any]]:
    base_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    body: Dict[str, Any] = {
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency", "Start Date", "End Date"],
        "page": 1,
        "limit": max(1, min(int(rows), 100)),
        "filters": {"award_type_codes": ["A", "B", "C", "D"]},
    }
    if keyword.strip():
        body["filters"]["keywords"] = [keyword.strip()]

    cache_key = _sha("usaspending|" + json.dumps(body, sort_keys=True))
    cached = cache.get(cache_key, cache_ttl_s)
    if cached:
        return _parse_usaspending_items(cached), cached

    r = requests.post(base_url, json=body, timeout=timeout_s)
    payload: Dict[str, Any] = _http_json_or_text(r)
    payload["_http_status"] = r.status_code
    payload["_request_url"] = base_url
    payload["_request_body"] = body

    if r.status_code == 200:
        cache.set(cache_key, payload)

    return _parse_usaspending_items(payload), payload


def _parse_usaspending_items(payload: Dict[str, Any]) -> List[Item]:
    items: List[Item] = []
    results = payload.get("results") or []
    if not isinstance(results, list):
        return items

    for row in results:
        if not isinstance(row, dict):
            continue

        award_id = row.get("Award ID") or row.get("award_id") or ""
        recipient = row.get("Recipient Name") or row.get("recipient_name") or ""
        agency = row.get("Awarding Agency") or row.get("awarding_agency") or ""
        start = row.get("Start Date") or row.get("start_date") or ""
        end = row.get("End Date") or row.get("end_date") or ""
        amount = row.get("Award Amount") or row.get("award_amount") or ""
        title = f"{recipient} | {amount}"

        url = _usaspending_award_url(str(award_id)) if award_id else ""
        if not url and recipient:
            url = f"https://www.usaspending.gov/search?query={quote_plus(str(recipient))}"

        items.append(
            Item(
                source="USAspending (awards)",
                title=str(title),
                buyer=str(agency),
                posted_date=_fmt_date_any(start),
                due_date=_fmt_date_any(end),
                url=str(url),
                item_id=str(award_id) if award_id else title,
                raw=row,
            )
        )
    return items


def fetch_fpds_atom_feed(atom_url: str, timeout_s: int) -> Tuple[List[Item], Dict[str, Any]]:
    u = (atom_url or "").strip()
    if not u:
        return [], {"error": "FPDS Atom URL is empty. Paste a feed URL from FPDS."}

    parsed = feedparser.parse(u)
    payload = {
        "_request_url": u,
        "_bozo": getattr(parsed, "bozo", False),
        "_bozo_exception": str(getattr(parsed, "bozo_exception", "")),
        "feed": dict(parsed.feed) if hasattr(parsed, "feed") else {},
        "entries": [dict(e) for e in (parsed.entries or [])],
    }

    items: List[Item] = []
    for e in payload["entries"][:200]:
        title = e.get("title", "") or ""
        link = e.get("link", "") or ""
        updated = e.get("updated", "") or e.get("published", "") or ""
        item_id = e.get("id", "") or link or title
        items.append(
            Item(
                source="FPDS Atom (awards)",
                title=str(title),
                buyer="",
                posted_date=_fmt_date_any(updated),
                due_date="",
                url=_ensure_http_url(str(link)),
                item_id=str(item_id),
                raw=e,
            )
        )
    return items, payload


def fetch_data_gov_ckan(
    cache: SimpleCache,
    data_gov_api_key: str,
    keyword: str,
    rows: int,
    timeout_s: int,
    cache_ttl_s: int,
) -> Tuple[List[Item], Dict[str, Any]]:
    if data_gov_api_key:
        base_url = "https://api.gsa.gov/technology/datagov/v3/action/package_search"
        headers = {"x-api-key": data_gov_api_key}
    else:
        base_url = "https://catalog.data.gov/api/3/action/package_search"
        headers = {}

    q = keyword.strip() if keyword.strip() else "rfp OR bid OR solicitation OR procurement"
    params = {"q": q, "rows": max(1, min(int(rows), 100))}

    cache_key = _sha("datagov|" + base_url + "|" + json.dumps(params, sort_keys=True))
    cached = cache.get(cache_key, cache_ttl_s)
    if cached:
        return _parse_ckan_items(cached), cached

    r = requests.get(base_url, params=params, headers=headers, timeout=timeout_s)
    payload: Dict[str, Any] = _http_json_or_text(r)
    payload["_http_status"] = r.status_code
    payload["_request_url"] = r.url

    if r.status_code == 200:
        cache.set(cache_key, payload)

    return _parse_ckan_items(payload), payload


def _parse_ckan_items(payload: Dict[str, Any]) -> List[Item]:
    items: List[Item] = []
    result = _safe_get(payload, ["result"], {})
    results = result.get("results") or []
    if not isinstance(results, list):
        return items

    for ds in results:
        if not isinstance(ds, dict):
            continue
        title = ds.get("title") or ds.get("name") or ""
        org = _safe_get(ds, ["organization", "title"], "") or ""
        url = ds.get("url") or ""
        if not url:
            url = _safe_get(ds, ["resources", 0, "url"], "")

        ds_id = ds.get("id") or ds.get("name") or title

        items.append(
            Item(
                source="Data.gov CKAN (discovery)",
                title=str(title),
                buyer=str(org),
                posted_date="",
                due_date="",
                url=_ensure_http_url(str(url)),
                item_id=str(ds_id),
                raw=ds,
            )
        )
    return items


def fetch_socrata_dataset(
    dataset_url: str,
    keyword: str,
    rows: int,
    timeout_s: int,
) -> Tuple[List[Item], Dict[str, Any]]:
    u = (dataset_url or "").strip()
    if not u:
        return [], {"error": "Socrata dataset URL is empty. Example: https://data.cityofnewyork.us/resource/xxxx.json"}

    params: Dict[str, Any] = {"$limit": max(1, min(int(rows), 5000))}
    if keyword.strip():
        params["$q"] = keyword.strip()

    r = requests.get(u, params=params, timeout=timeout_s)
    payload = _http_json_or_text(r)
    meta = {"_http_status": r.status_code, "_request_url": r.url}

    items: List[Item] = []
    data = payload if isinstance(payload, list) else payload.get("data")
    if isinstance(data, list):
        for row in data[:200]:
            if not isinstance(row, dict):
                continue
            title = (
                row.get("title")
                or row.get("name")
                or row.get("solicitation_title")
                or row.get("project_name")
                or "Socrata record"
            )
            buyer = row.get("agency") or row.get("department") or row.get("owner") or ""
            posted = row.get("posted_date") or row.get("publish_date") or row.get("created_date") or ""
            due = row.get("due_date") or row.get("close_date") or row.get("bid_due_date") or ""
            url = row.get("url") or row.get("link") or ""
            rid = row.get("id") or row.get(":id") or title

            items.append(
                Item(
                    source="Socrata (local)",
                    title=str(title),
                    buyer=str(buyer),
                    posted_date=_fmt_date_any(posted),
                    due_date=_fmt_date_any(due),
                    url=_ensure_http_url(str(url)),
                    item_id=str(rid),
                    raw=row,
                )
            )

    return items, {"meta": meta, "data": payload}


def dedupe_items(items: List[Item]) -> List[Item]:
    seen = set()
    out: List[Item] = []
    for it in items:
        k = (it.source, it.item_id, it.title)
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def to_rows(items: List[Item]) -> List[Dict[str, Any]]:
    return [
        {
            "source": it.source,
            "title": it.title,
            "buyer": it.buyer,
            "posted_date": it.posted_date,
            "due_date": it.due_date,
            "url": it.url,
            "item_id": it.item_id,
        }
        for it in items
    ]


def run_search(
    *,
    cache: SimpleCache,
    sam_api_key: str,
    simpler_api_key: str,
    data_gov_api_key: str,
    sources: List[str],
    keyword: str,
    days_back: int,
    max_rows: int,
    timeout_s: int,
    cache_ttl_s: int,
    fpds_atom_url: str,
    socrata_dataset_url: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    all_items: List[Item] = []
    debug: Dict[str, Any] = {"sources": sources, "keyword": keyword}

    posted_to = datetime.now()
    posted_from = posted_to - timedelta(days=max(1, int(days_back)))

    if "SAM.gov (contracts)" in sources:
        items, raw = fetch_sam_opportunities(
            cache=cache,
            api_key=sam_api_key,
            keyword=keyword,
            posted_from=posted_from,
            posted_to=posted_to,
            limit=max_rows,
            timeout_s=timeout_s,
            cache_ttl_s=cache_ttl_s,
        )
        all_items.extend(items)
        debug["sam"] = raw

    if "Grants.gov (grants)" in sources:
        items, raw = fetch_grants_gov(
            cache=cache,
            keyword=keyword,
            rows=min(max_rows, 100),
            timeout_s=timeout_s,
            cache_ttl_s=cache_ttl_s,
        )
        all_items.extend(items)
        debug["grants_gov"] = raw

    if "Simpler.Grants.gov (grants)" in sources:
        items, raw = fetch_simpler_grants(
            cache=cache,
            api_key=simpler_api_key,
            keyword=keyword,
            rows=min(max_rows, 100),
            timeout_s=timeout_s,
            cache_ttl_s=cache_ttl_s,
        )
        all_items.extend(items)
        debug["simpler_grants"] = raw

    if "USAspending (awards)" in sources:
        items, raw = fetch_usaspending_awards(
            cache=cache,
            keyword=keyword,
            rows=min(max_rows, 100),
            timeout_s=timeout_s,
            cache_ttl_s=cache_ttl_s,
        )
        all_items.extend(items)
        debug["usaspending"] = raw

    if "FPDS Atom (awards)" in sources:
        items, raw = fetch_fpds_atom_feed(atom_url=fpds_atom_url, timeout_s=timeout_s)
        all_items.extend(items)
        debug["fpds_atom"] = raw

    if "Data.gov CKAN (discovery)" in sources:
        items, raw = fetch_data_gov_ckan(
            cache=cache,
            data_gov_api_key=data_gov_api_key,
            keyword=keyword,
            rows=min(max_rows, 100),
            timeout_s=timeout_s,
            cache_ttl_s=cache_ttl_s,
        )
        all_items.extend(items)
        debug["data_gov"] = raw

    if "Socrata dataset (local)" in sources:
        items, raw = fetch_socrata_dataset(
            dataset_url=socrata_dataset_url,
            keyword=keyword,
            rows=min(max_rows, 5000),
            timeout_s=timeout_s,
        )
        all_items.extend(items)
        debug["socrata"] = raw

    all_items = dedupe_items(all_items)
    rows = to_rows(all_items)

    def sort_key(v: Any) -> float:
        try:
            return dtparser.parse(str(v)).timestamp()
        except Exception:
            return 0.0

    # newest posted first; if tie, earlier due first
    rows.sort(
        key=lambda r: (sort_key(r.get("posted_date")), -sort_key(r.get("due_date"))),
        reverse=True,
    )
    return rows, debug
