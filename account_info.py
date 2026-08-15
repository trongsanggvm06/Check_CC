"""
Account Info Extractor (chỉ phục vụ Next Payment + Plan cho life.txt).

Tách ra từ `D:\\Ổ F\\Done\\checker_core.py`, CHỈ giữ:
  - parse cookie (string / Netscape / JSON array)
  - trích `nextBillingDate` và `localizedPlanName` từ trang membership
  - định dạng "Next Payment" và "Plan" đúng format `Life.txt` mẫu

KHÔNG chứa: tạo NFToken, phân loại HIT/FREE/DEAD, logic die/life.
Được sử dụng bởi `/api/account-info` — endpoint MỚI, không chạm vào `app.py`
phần `/api/generate` hay `netflix.py`.
"""

import html
import json
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import unquote

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


_KNOWN_COOKIE_NAMES = ("NetflixId", "SecureNetflixId", "flwssn", "nfvdid")

ACCOUNT_PAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


# ── Cookie parsing (copy từ checker_core, không đổi logic) ──

def _decode_unicode_escape(match):
    try:
        return chr(int(match.group(1), 16))
    except Exception:
        return match.group(0)


def _decode_hex_escape(match):
    try:
        return chr(int(match.group(1), 16))
    except Exception:
        return match.group(0)


def decode_netflix_value(value):
    if value is None:
        return None
    cleaned = html.unescape(str(value))
    replacements = {
        "\\x20": " ", "\\u00A0": " ", "\\u00a0": " ", "&nbsp;": " ", "u00A0": " ",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    cleaned = cleaned.replace("\\/", "/").replace('\\"', '"').replace("\\n", " ").replace("\\t", " ")
    for _ in range(3):
        previous = cleaned
        cleaned = re.sub(r"\\u([0-9a-fA-F]{4})", _decode_unicode_escape, cleaned)
        cleaned = re.sub(r"\\x([0-9a-fA-F]{2})", _decode_hex_escape, cleaned)
        cleaned = re.sub(r"(?<!\\)\bu([0-9a-fA-F]{4})(?![0-9a-fA-F])", _decode_unicode_escape, cleaned)
        cleaned = cleaned.replace("\\\\", "\\")
        if cleaned == previous:
            break
    cleaned = re.sub(r"(?<=[A-Za-z])\s+(?=[^\x00-\x7F])", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def _has_ct_token(value: str) -> bool:
    v = value or ""
    return "ct%3D" in v or "ct=" in v


def _split_embedded_cookies(cookies: dict) -> dict:
    if not isinstance(cookies, dict):
        return cookies
    extracted = {}
    for name in list(cookies.keys()):
        value = cookies.get(name) or ""
        if ";" not in value or "=" not in value:
            continue
        segments = [s.strip() for s in value.split(";")]
        base = segments[0]
        found = False
        for seg in segments[1:]:
            if "=" in seg:
                key, _, val = seg.partition("=")
                key = key.strip()
                val = val.strip()
                if key in _KNOWN_COOKIE_NAMES and val:
                    extracted.setdefault(key, []).append(val)
                    found = True
        if found:
            cookies[name] = base
    for key, values in extracted.items():
        candidates = ([cookies[key]] if cookies.get(key) else []) + values
        if key == "NetflixId":
            best = next((v for v in candidates if _has_ct_token(v)), candidates[0])
        else:
            best = candidates[-1]
        cookies[key] = best
    return cookies


def parse_cookies(text: str) -> dict:
    """Parse cookie string từ nhiều định dạng (string / Netscape / JSON array)."""
    text = text.strip()
    cookies = {}

    if text.startswith("["):
        try:
            items = json.loads(text)
            for item in items:
                name = item.get("name", "")
                value = item.get("value", "")
                if name and value:
                    cookies[name] = value
            if cookies:
                return _split_embedded_cookies(cookies)
        except Exception:
            pass

    if "\t" in text:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                name = parts[5].strip()
                value = parts[6].strip()
                if name:
                    cookies[name] = value
        if cookies:
            return _split_embedded_cookies(cookies)

    for part in text.split(";"):
        part = part.strip()
        if "=" in part:
            name, _, value = part.partition("=")
            name = name.strip()
            value = value.strip()
            if name:
                cookies[name] = value

    return _split_embedded_cookies(cookies)


def get_netflix_id(cookies: dict):
    if not isinstance(cookies, dict):
        return None
    for key, value in cookies.items():
        if str(key).lower().replace("_", "").replace("-", "") == "netflixid" and value:
            return value
    return None


# ── Date parsing ──

MONTH_ALIASES = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "janvier": 1, "février": 2, "mars": 3, "avril": 4, "juin": 6, "juillet": 7,
    "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}


def normalize_calendar_year(year):
    try:
        year = int(year)
    except Exception:
        return None
    if 2400 <= year <= 2700:
        return year - 543
    return year


def parse_localized_date(cleaned):
    if not cleaned:
        return None
    for parser in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(cleaned, parser)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except Exception:
        pass
    numeric_parts = [int(part) for part in re.findall(r"\d+", cleaned)]
    if len(numeric_parts) >= 3:
        a, b, c = numeric_parts[0], numeric_parts[1], numeric_parts[2]
        try:
            a = normalize_calendar_year(a)
            c = normalize_calendar_year(c)
            if a and 1900 <= a <= 3000 and 1 <= b <= 12 and 1 <= c <= 31:
                return datetime(a, b, c)
            if c and 1 <= a <= 31 and 1 <= b <= 12 and 1900 <= c <= 3000:
                return datetime(c, b, a)
        except Exception:
            pass
    raw_lower = cleaned.lower()
    month = None
    for alias, alias_month in MONTH_ALIASES.items():
        if alias in raw_lower:
            month = alias_month
            break
    if month is None:
        return None
    year = None
    for number in numeric_parts:
        normalized_year = normalize_calendar_year(number)
        if normalized_year is not None and 1900 <= normalized_year <= 3000:
            year = normalized_year
            break
    if year is None:
        return None
    day = 1
    for number in numeric_parts:
        if normalize_calendar_year(number) == year:
            continue
        if 1 <= number <= 31:
            day = number
            break
    try:
        return datetime(year, month, day)
    except Exception:
        return None


def format_display_date(value):
    cleaned = decode_netflix_value(value)
    if not cleaned:
        return None
    parsed = parse_localized_date(cleaned)
    if parsed is not None:
        return parsed.strftime("%B %d, %Y").replace(" 0", " ")
    return cleaned


# ── Plan label (alias mapping giữ nguyên từ checker_core) ──

PLAN_ALIASES = {
    "Premium": {"premium", "premium_extra_member", "cao_cap", "cao_c_ap", "ozel", "프리미엄", "プレミアム"},
    "Standard With Ads": {"standard_with_ads", "standardwithads", "estandar_con_anuncios", "광고형_스탠다드"},
    "Standard": {"standard", "estandar", "標準方案", "标准", "standaard", "스탠다드"},
    "Basic": {"basic", "basico", "dasar", "basique", "basis", "베이직", "现代农业"},
    "Mobile": {"mobile", "ponsel", "seluler", "movil", "모바일", "モバイル"},
}


def normalize_plan_key(plan_name):
    if not plan_name:
        return "unknown"
    simplified = unicodedata.normalize("NFKD", plan_name)
    simplified = "".join(ch for ch in simplified if not unicodedata.combining(ch))
    normalized = re.sub(r"[^\w]+", "_", simplified.lower(), flags=re.UNICODE).strip("_")
    return normalized or "unknown"


def derive_plan_label(raw_plan):
    if not raw_plan:
        return "Free"
    normalized = normalize_plan_key(raw_plan)
    for label, aliases in PLAN_ALIASES.items():
        if normalized in aliases:
            return label
    return raw_plan


# ── Regex extract (chỉ lấy 2 trường cần thiết) ──

_NEXT_BILLING_PATTERNS = [
    r'"GrowthNextBillingDate"\s*,\s*"date"\s*:\s*"([^"T]+)T',
    r'"nextBillingDate"\s*:\s*"([^"]+)"',
]

_LOCALIZED_PLAN_PATTERNS = [
    r'"MemberPlan"\s*,\s*"fields"\s*:\s*\{\s*"localizedPlanName"\s*:\s*\{\s*"fieldType"\s*:\s*"String"\s*,\s*"value"\s*:\s*"([^"]+)"',
    r'localizedPlanName\":{\\"fieldType\\":\\"String\\",\\"value\\":\\"([^"]+)"',
    r'"localizedPlanName"\s*:\s*"([^"]+)"',
    r'"planName"\s*:\s*"([^"]+)"',
]


def extract_first_match(response_text, patterns, flags=0):
    for pattern in patterns:
        match = re.search(pattern, response_text, flags)
        if match:
            return decode_netflix_value(match.group(1))
    return None


def extract_minimal_info(response_text):
    next_billing_raw = extract_first_match(response_text, _NEXT_BILLING_PATTERNS)
    plan_raw = extract_first_match(response_text, _LOCALIZED_PLAN_PATTERNS)
    info = {}
    if next_billing_raw:
        info["nextBillingDate"] = next_billing_raw
    if plan_raw:
        info["localizedPlanName"] = plan_raw
    return info


# ── GraphQL payload path (richer source) ──

def extract_info_from_graphql_payload(response_text):
    try:
        payload = json.loads(response_text)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    if not isinstance(data, dict):
        return {}
    growth_account = data.get("growthAccount") or {}
    current_plan = ((growth_account.get("currentPlan") or {}).get("plan") or {})
    next_plan = ((growth_account.get("nextPlan") or {}).get("plan") or {})
    next_billing = growth_account.get("nextBillingDate") or {}

    info = {
        "nextBillingDate": decode_netflix_value(next_billing.get("localDate") or next_billing.get("date")),
        "localizedPlanName": decode_netflix_value(current_plan.get("name") or next_plan.get("name")),
    }
    return {k: v for k, v in info.items() if v not in (None, "", [], {})}


def merge_info(*sources):
    out = {}
    for src in sources:
        if not src:
            continue
        for k, v in src.items():
            if v not in (None, "", [], {}) and k not in out:
                out[k] = v
    return out


# ── Public API ──

def fetch_account_minimal(cookie_text: str, timeout: int = 30):
    """
    Trích `Next Payment` + `Plan` từ cookie Netflix (đã biết là sống).

    Returns:
        {
            "ok": bool,
            "next_payment": "June 22, 2026" | None,
            "plan": "Premium" | "Standard" | ... | None,
            "raw": {...},
            "error": str | None,
        }
    """
    try:
        cookies = parse_cookies(cookie_text)
    except Exception as e:
        return {"ok": False, "error": f"Parse cookie lỗi: {e}"}

    if not get_netflix_id(cookies):
        return {"ok": False, "error": "Không tìm thấy NetflixId trong cookie"}

    session = requests.Session()
    session.cookies.update(cookies)
    session.verify = False

    last_error = "Account page fetch failed"
    try:
        response = session.get(
            "https://www.netflix.com/account/membership",
            headers=ACCOUNT_PAGE_HEADERS,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": f"Network error: {e}"}
    except Exception as e:
        return {"ok": False, "error": f"Unexpected error: {e}"}

    if response.status_code in (401, 440):
        return {"ok": False, "error": f"HTTP {response.status_code} — cookie hết hạn"}
    if response.status_code != 200:
        return {"ok": False, "error": f"HTTP {response.status_code}"}

    body = response.text or ""
    final_url = (getattr(response, "url", "") or "").lower()
    if any(seg in final_url for seg in ("/login", "/signin", "/signup", "/logout")):
        return {"ok": False, "error": "Cookie bị chuyển hướng về login"}
    login_wall = (
        'data-uia="login', 'id="id_password"', 'name="userLoginId"',
        '"pageName":"login"', 'action="/login', '"NONMEMBER"',
        '"isMemberOrNonmember":"NONMEMBER"',
    )
    if not any(m in body for m in (
        '"membershipStatus"', '"growthAccount"', '"currentPlan"',
        '"nextBillingDate"', '"memberSince"', '"CURRENT_MEMBER"',
    )):
        if any(m in body for m in login_wall):
            return {"ok": False, "error": "Cookie bị từ chối (login wall)"}

    graphql_info = extract_info_from_graphql_payload(body)
    regex_info = extract_minimal_info(body)
    info = merge_info(regex_info, graphql_info)

    next_payment = format_display_date(info.get("nextBillingDate"))
    plan_label = derive_plan_label(info.get("localizedPlanName"))

    if not next_payment and not plan_label:
        return {
            "ok": False,
            "error": last_error,
            "raw": info,
        }

    return {
        "ok": True,
        "next_payment": next_payment,
        "plan": plan_label,
        "raw": info,
        "error": None,
    }