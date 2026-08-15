"""
Netflix Login Link Generator

Token NATIVE qua iOS FTL NFToken — path ["account","token","default"].
  Endpoint: https://ios.prod.ftl.netflix.com/iosui/user/15.48
  Logic port NGUYÊN từ bot tele (Netflix-Cookie-Checker-main/bot.py):
    - GET với NFTOKEN_QUERY_PARAMS + NFTOKEN_HEADERS cố định (ESN/guid hardcode)
    - version 15.48, gửi đầy đủ cookie
    - 1 token dùng cho CẢ PC lẫn Mobile:
        https://netflix.com/?nftoken=<token>

Lý do 1 link cho tất cả: Netflix AASA chính thức (apple-app-site-association) loại
trừ /unsupported khỏi Universal Link. Path "/* (root) thì KHÔNG bị exclude → iOS
handoff sang app Netflix, Android mở app qua App Link, web/desktop set session
cookie và redirect vào Netflix. 1 link dùng được cho cả 3 platform.

Ref: github.com/harshitkamboj/Netflix-NFToken-Generator
"""
import json
import re
import time
import urllib.parse
from datetime import datetime, timezone

import requests
from urllib3.exceptions import InsecureRequestWarning

from config import LOGIN_BASE, MOBILE_LOGIN_BASE

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# ─── Cookie keys ───────────────────────────────────────────────────────────────

COOKIE_KEYS = ("NetflixId", "SecureNetflixId", "nfvdid", "OptanonConsent", "flwssn", "gsid")

# Random ESN per request — tránh Netflix blacklist cùng ESN cho tất cả user.
import secrets as _secrets
import string as _string

def _gen_esn(prefix: str, length: int = 90) -> str:
    return prefix + ''.join(_secrets.choice(_string.ascii_uppercase + _string.digits) for _ in range(length))

def _gen_guid() -> str:
    return ''.join(_secrets.choice('0123456789ABCDEF') for _ in range(16))

# iOS ESN + GUID — random mỗi lần import (mỗi server process restart = 1 ESN mới).
# Module-level random vẫn tốt hơn hardcoded, nhưng tốt nhất nên random per-request trong hàm mint.
_IOS_ESN_FIXED   = "NFAPPL-02-IPHONE8=1-PXA-"
_IOS_ESN          = _gen_esn(_IOS_ESN_FIXED, 90)
_IOS_GUID         = _gen_guid()

# ─── NFToken API (iOS FTL) — token NATIVE "account.token.default" ─────────────────
# Port NGUYÊN từ bot tele: version 15.48, ESN + guid hardcode, headers cố định.
# 1 token này dùng cho CẢ link PC và Mobile.
NFTOKEN_API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"

NFTOKEN_QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": urllib.parse.quote(_IOS_ESN, safe=""),
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}

NFTOKEN_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": _IOS_GUID,
    "x-netflix.context.profile-guid": _IOS_GUID,
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": _IOS_ESN,
    "x-netflix.context.locales": "en-US",
    "accept-language": "en-US;q=1",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
}


# ─── Android FTL endpoint — fallback cho iOS FTL khi token iOS-bound gây NSES-404 trên Android
# Android client dùng endpoint này với Android-specific ESN. Token Android thường tương thích
# tốt hơn với Netflix Android app, giảm NSES-404 khi mở link trên Chrome Android.
# Ref: tham khảo _test_more_endpoints.py (tested 2025).
ANDROID_NFTOKEN_API_URL = "https://android.prod.ftl.netflix.com/androidui/user/15.48"


def _build_android_params_and_headers():
    esn = _get_android_esn()
    guid = _get_android_guid()
    return {
        "params": {
            "appVersion": "15.48.1",
            "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
            "device_type": "NFANDROID-01-",
            "esn": urllib.parse.quote(esn, safe=""),
            "languages": "en-US",
            "locale": "en-US",
            "path": '["account","token","default"]',
            "pathFormat": "graph",
            "progressive": "false",
            "responseFormat": "json",
        },
        "headers": {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; SM-S908B Build/TP1A.220624.014)",
            "x-netflix.request.attempt": "1",
            "x-netflix.request.client.user.guid": guid,
            "x-netflix.context.profile-guid": guid,
            "x-netflix.request.routing": '{"path":"/nq/android/nqandroid/~15.48.0/user","control_tag":"androidui_argo"}',
            "x-netflix.context.app-version": "15.48.1",
            "x-netflix.argo.translated": "true",
            "x-netflix.context.form-factor": "phone",
            "x-netflix.context.sdk-version": "2012.4",
            "x-netflix.client.appversion": "15.48.1",
            "x-netflix.client.type": "argo",
            "x-netflix.client.ftl.esn": esn,
            "x-netflix.context.locales": "en-US",
            "accept-language": "en-US;q=1",
            "x-netflix.context.os-version": "14",
            "x-netflix.request.client.context": '{"appState":"foreground"}',
            "x-netflix.context.ui-flavor": "argo",
        },
    }


# Module-level constants (backward compat) — KHÔNG dùng trực tiếp nữa, dùng _build_android_params_and_headers()
_ANDROID_ESN_FALLBACK = "NFANDROID-01-" + "A" * 30
ANDROID_NFTOKEN_QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFANDROID-01-",
    "esn": urllib.parse.quote(_ANDROID_ESN_FALLBACK, safe=""),
    "languages": "en-US",
    "locale": "en-US",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "progressive": "false",
    "responseFormat": "json",
}
ANDROID_NFTOKEN_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; SM-S908B Build/TP1A.220624.014)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HLL",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HLL",
    "x-netflix.request.routing": '{"path":"/nq/android/nqandroid/~15.48.0/user","control_tag":"androidui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": _ANDROID_ESN_FALLBACK,
    "x-netflix.context.locales": "en-US",
    "accept-language": "en-US;q=1",
    "x-netflix.context.os-version": "14",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
}


# ─── Cookie parser ────────────────────────────────────────────────────────────

def _decode_cookie_value(value: str) -> str:
    if isinstance(value, str) and "%" in value:
        try:
            return urllib.parse.unquote(value)
        except Exception:
            return value
    return value


def _strip_quotes(value: str) -> str:
    """Bỏ cặp nháy bao quanh value nếu có: \"v=3...\" -> v=3..."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def split_cookie_blocks(raw: str) -> list:
    """
    Tách input thành nhiều block cookie.
    Hỗ trợ:
    - ---- separator
    - Mỗi dòng 1 account: raw "key=...; NetflixId=..." HOẶC 1 JSON array/dòng — KỂ CẢ trộn lẫn
    - JSON arrays (kể cả khi 1 array trải nhiều dòng)
    - Raw: SecureNetflixId= đứng trước NetflixId= (mỗi dòng riêng)
    - Raw: NetflixId= đứng đầu (mỗi dòng riêng)
    - Raw: mỗi cặp key=value riêng trên 1 dòng
    - Paragraphs (dòng trắng ngăn cách)
    """
    text = raw.strip()
    if not text:
        return []

    # 1. ---- separator
    if "----" in text:
        return [b.strip() for b in text.split("----") if b.strip()]

    # 2. Mỗi dòng là 1 account HOÀN CHỈNH — raw "nfvdid=...; NetflixId=..." HOẶC 1 JSON array/dòng,
    #    KỂ CẢ khi TRỘN lẫn 2 kiểu trong cùng input. Điều kiện: ≥2 dòng và MỖI dòng tự parse ra
    #    được NetflixId của riêng nó.
    #    PHẢI check TRƯỚC bước gom JSON array (step 3): nếu không, các dòng raw bị bỏ sót — chỉ
    #    nhận JSON array → "paste 4 ra 2". Cũng tránh tách theo vị trí NetflixId= gây lệch chéo cookie.
    nonempty_lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if len(nonempty_lines) >= 2 and all(
        parse_cookies(ln).get("NetflixId") for ln in nonempty_lines
    ):
        return nonempty_lines

    # 3. Multiple JSON arrays
    blocks = []
    depth = 0
    start = -1
    in_str = False
    escape = False
    for i, c in enumerate(text):
        if escape:
            escape = False
            continue
        if in_str:
            if c == "\\":
                escape = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            continue
        if c == "[":
            if depth == 0:
                start = i
            depth += 1
        elif c == "]":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    blocks.append(text[start:i + 1])
                    start = -1
    if len(blocks) >= 2:
        return blocks

    # 4. Split bằng dòng trắng lớn (phòng batch multi-line: mỗi block trải nhiều dòng)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) >= 2:
        return paragraphs

    # 5. Dòng bắt đầu bằng SecureNetflixId= HOẶC NetflixId= → mỗi dòng là 1 block
    lines = text.split("\n")
    line_blocks = []
    current = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("SecureNetflixId=") or stripped.startswith("NetflixId="):
            if current:
                joined = " ".join(current)
                if joined not in line_blocks:
                    line_blocks.append(joined)
            current = [stripped]
        else:
            current.append(stripped)

    if current:
        joined = " ".join(current)
        if joined not in line_blocks:
            line_blocks.append(joined)

    if len(line_blocks) >= 2:
        return line_blocks

    # 6. Raw: anchor NetflixId= hoặc SecureNetflixId= ở đầu dòng / sau \n
    anchor_pat = re.compile(
        r"(?:^|\n)\s*(NetflixId=|SecureNetflixId=)",
        re.IGNORECASE
    )
    anchors = list(anchor_pat.finditer(text))
    if len(anchors) >= 2:
        raw_blocks = []
        for i, m in enumerate(anchors):
            start = m.start()
            end = anchors[i + 1].start() if i + 1 < len(anchors) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                raw_blocks.append(chunk)
        if len(raw_blocks) >= 2:
            return raw_blocks

    # 7. Nhiều NetflixId= trong text
    netflix_positions = [m.start() for m in re.finditer(r"\bNetflixId=", text)]
    if len(netflix_positions) >= 2:
        raw_blocks = []
        for i, start in enumerate(netflix_positions):
            end = netflix_positions[i + 1] if i + 1 < len(netflix_positions) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                raw_blocks.append(chunk)
        if len(raw_blocks) >= 2:
            return raw_blocks

    # 8. Fallback: 1 block
    return [text]


def _fill_missing_shared_cookies(block_dicts: list) -> list:
    """Quét toàn batch tìm nfvdid; gán cho block thiếu."""
    if not block_dicts:
        return block_dicts

    all_nfvdids = []
    for cd in block_dicts:
        if cd.get("nfvdid"):
            all_nfvdids.append(cd["nfvdid"])

    if not all_nfvdids:
        return block_dicts

    for cd in block_dicts:
        if not cd.get("nfvdid") and all_nfvdids:
            cd["nfvdid"] = all_nfvdids[0]

    return block_dicts


def parse_cookies(raw: str) -> dict:
    """
    Parse cookie string thành dict — hỗ trợ MỌI format Netflix phổ biến:
      • JSON array (Cookie-Editor / EditThisCookie) — kể cả khi name/value KHÔNG liền nhau
      • JSON object {NetflixId: ...} hoặc {"cookies": [...]}
      • Chuỗi header: NetflixId=...; SecureNetflixId=...
      • Raw key=value mỗi dòng
      • Netscape cookies.txt (TAB-separated — từ tiện ích "Get cookies.txt")
      • name: value (dấu hai chấm)
      • JSON hỏng / cắt dở (vẫn vớt được name+value)
      • Giá trị có/không URL-encode, có/không bọc nháy
    """
    text = raw.strip()
    cookie_dict: dict = {}

    def _take(name, value):
        if (name in COOKIE_KEYS and isinstance(value, str)
                and value and name not in cookie_dict):
            cookie_dict[name] = _decode_cookie_value(value)

    def _from_objects(items):
        for c in items:
            if not isinstance(c, dict):
                continue
            name = c.get("name") or c.get("Name") or c.get("key") or c.get("Key")
            value = c.get("value")
            if value is None:
                value = c.get("Value")
            _take(name, value)

    # 1) JSON hợp lệ ──────────────────────────────────────────────────
    data = None
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    if isinstance(data, list):
        _from_objects(data)
    elif isinstance(data, dict):
        if isinstance(data.get("cookies"), list):
            _from_objects(data["cookies"])
        for key in COOKIE_KEYS:
            v = data.get(key)
            if isinstance(v, str):
                _take(key, v)

    # 2) JSON-fragment (JSON hỏng / cắt dở / name-value không liền nhau):
    if not all(k in cookie_dict for k in ("NetflixId", "SecureNetflixId", "nfvdid")):
        for obj in re.findall(r"\{[^{}]*\}", text):
            nm = re.search(r'"name"\s*:\s*"([^"]+)"', obj, re.IGNORECASE)
            vl = re.search(r'"value"\s*:\s*"([^"]*)"', obj, re.IGNORECASE)
            if nm and vl:
                _take(nm.group(1), vl.group(1))
        for key in COOKIE_KEYS:
            if key in cookie_dict:
                continue
            nm = re.search(rf'"name"\s*:\s*"{re.escape(key)}"', text, re.IGNORECASE)
            if not nm:
                continue
            vm = re.search(r'"value"\s*:\s*"([^"]*)"',
                           text[nm.end():nm.end() + 500], re.IGNORECASE)
            if not vm:
                befs = list(re.finditer(r'"value"\s*:\s*"([^"]*)"',
                                        text[max(0, nm.start() - 500):nm.start()],
                                        re.IGNORECASE))
                vm = befs[-1] if befs else None
            if vm:
                _take(key, vm.group(1))

    # 3) Chuỗi thô — tách name/value bằng '='  |  ':'  |  TAB (Netscape):
    for key in COOKIE_KEYS:
        if key in cookie_dict:
            continue
        m = re.search(
            rf"(?<!\w){re.escape(key)}[ ]*[=:\t][ ]*"
            rf"(?:\"([^\"]*)\"|'([^']*)'|([^;,\s\"']+))",
            text,
        )
        if m:
            val = m.group(1) or m.group(2) or m.group(3)
            if val:
                cookie_dict[key] = _decode_cookie_value(_strip_quotes(val))

    return cookie_dict


def parse_cookie_blocks(raw: str) -> list:
    """Parse toàn bộ input thành list cookie dict, bù nfvdid toàn batch."""
    blocks = split_cookie_blocks(raw)
    parsed_blocks = [parse_cookies(block) for block in blocks]
    parsed_blocks = [cd for cd in parsed_blocks if cd]
    return _fill_missing_shared_cookies(parsed_blocks)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _fmt_expiry(expiry) -> str:
    if not expiry:
        return "Không xác định"
    try:
        ts = int(expiry)
        if ts > 1e12:
            ts //= 1000
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(expiry)


def _build_result(token: str, expiry, method_name: str, platform: str = "laptop",
                  base_url: str = "") -> dict:
    """
    Build result với nhiều URL format cho từng platform.

    URL formats:
      - https://www.netflix.com/?nftoken=<token>
        ↑ HTTPS Universal Link / App Link. iOS Safari tự mở Netflix app qua Universal Links.
          Trên Android Chrome: mở trang web (nếu user paste vào address bar) HOẶC hiện
          banner "Open in app" (nếu click từ web khác).

      - <base_url>/r/<token>
        ↑ TRANG TRUNG GIAN. Khi user mở link HTTPS này, server trả về HTML có JS detect
          Android và hiện nút "Mở Netflix App" → bấm vào sẽ fire intent:// → Chrome mở
          com.netflix.mediaclient. Đây là cách ổn định nhất để user mở trên Android
          (vì Chrome chỉ fire intent:// khi có USER GESTURE — bắt buộc phải có 1 trang
          trung gian host ở HTTPS domain). Trên iOS: redirect thẳng tới Universal Link.
          Trên PC: redirect thẳng tới web.

      - intent://www.netflix.com/?nftoken=<token>#Intent;scheme=https;package=com.netflix.mediaclient;...
        ↑ Raw intent URL. Chỉ hoạt động khi click từ 1 trang web khác trong Chrome
          (user gesture). Dùng để backup nếu user muốn copy thẳng intent://
          NHƯNG không paste vào address bar (Chrome sẽ block).

    Trước đây có `netflix://nftoken=...` deep link, nhưng Netflix KHÔNG đăng ký scheme
    "netflix://" trong Android app (xem tech stack audit: chỉ có intent:https, intent:market)
    → link đó không trigger gì cả. ĐÃ BỎ.
    """
    # Trang trung gian: user mở link HTTPS này → server trả HTML có nút bấm để mở app.
    # QUAN TRỌNG: phải URL-encode token trong URL vì token chứa ký tự đặc biệt (+, /).
    # - Dấu + trong URL không được quote thì server sẽ decode thành SPACE → lỗi 500
    # - Dấu / cần quote để không bị hiểu là path separator
    # → dùng quote() với safe="" để encode tất cả ký tự đặc biệt
    if base_url:
        base = base_url.rstrip("/")
        # quote với safe="" để encode cả "/" (để token "a/b" không bị split thành path)
        encoded_token = urllib.parse.quote(token, safe="")
        intermediary_url = f"{base}/r/{encoded_token}"
    else:
        # Fallback nếu server không truyền base_url
        encoded_token = urllib.parse.quote(token, safe="")
        intermediary_url = f"https://example.com/r/{encoded_token}"

    # ── Theo platform ──────────────────────────────────────────────────────────
    #   PC / Web   → https://netflix.com/?nftoken=<token>
    #                 (paste vào trình duyệt → vào Netflix web)
    #
    #   iPhone/iPad → https://netflix.com/unsupported?nftoken=<token>
    #                 (link từ bot gốc Netflix-Cookie-Checker-main/bot.py)
    #                 → Safari redeem token → /unsupported page → tap "Open App"
    #
    #   Android     → <base_url>/r/<token>
    #                 (landing page có nút "Mở Netflix App" → intent:// → app)
    pc_url = LOGIN_BASE + token              # PC / Web
    ios_url = "https://netflix.com/unsupported?nftoken=" + token
    mobile_url = intermediary_url             # Android → landing page
    return {
        "ok": True,
        "token": token,
        "url": pc_url,                                    # PC/Web (reference)
        "pc": pc_url,
        "ios": ios_url,                                   # iPhone / iPad
        "mobile": mobile_url,                             # Android
        "expiry": _fmt_expiry(expiry),
        "expires_ts": int(expiry) if expiry else None,    # Unix ms timestamp for countdown
        "build_id": method_name,
        "strategy": method_name,
        "platform": platform,
    }


def _build_cookie_header(cookies_dict: dict) -> str:
    """
    Build cookie header gửi cho Netflix.
    Gửi đúng dạng TRÌNH DUYỆT lưu = URL-encoded (NetflixId/SecureNetflixId chứa = & .).
    parse_cookies đã decode value → ở đây encode lại để khớp dạng gốc (giống cookie
    bot gửi qua requests.Session).
    """
    parts = []
    for key in COOKIE_KEYS:
        value = cookies_dict.get(key)
        if not value:
            continue
        if "%" not in value:  # value đã decode → encode lại về dạng browser gửi
            value = urllib.parse.quote(value, safe="-_.~")
        parts.append(f"{key}={value}")
    return "; ".join(parts)


# ─── Cookie refresh qua browser flow ──────────────────────────────────────────

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
}


def refresh_cookies(cookies_dict: dict, timeout: int = 20) -> dict:
    """
    Refresh Netflix cookies bằng cách simulate browser navigate tới /browse.

    Netflix sẽ Set-Cookie mới với ct/mac/dt mới khi browser thật truy cập.
    Hàm này tận dụng behavior đó để "tái cấp" session từ cookies cũ (còn sống).

    Args:
        cookies_dict: dict chứa NetflixId, SecureNetflixId, nfvdid, flwssn (đã decoded).
        timeout: timeout cho HTTP request.

    Returns:
        dict cookies mới (URL-decoded) — merge với input cookies, ghi đè nếu trùng.
        Thêm 'gsid' nếu Netflix trả về.
    """
    if not cookies_dict.get("NetflixId"):
        return cookies_dict

    try:
        s = requests.Session()
        s.headers.update(BROWSER_HEADERS)
        # Set cookies với domain đúng
        for k, v in cookies_dict.items():
            if not v:
                continue
            is_secure = k in ("SecureNetflixId",)
            s.cookies.set(k, v, domain='.netflix.com', path='/', secure=is_secure)

        # Navigate tới /browse — Netflix sẽ Set-Cookie mới
        r = s.get('https://www.netflix.com/browse', allow_redirects=True, timeout=timeout)

        if r.status_code != 200:
            return {**cookies_dict, "_refresh_error": f"HTTP {r.status_code}"}

        # Lấy cookies mới từ session
        new_cookies = dict(cookies_dict)  # Copy
        for c in s.cookies:
            if c.domain == '.netflix.com' and c.name in COOKIE_KEYS:
                new_cookies[c.name] = urllib.parse.unquote(c.value)

        # gsid có thể không trong COOKIE_KEYS mặc định, lấy riêng
        for c in s.cookies:
            if c.domain == '.netflix.com' and c.name == 'gsid':
                new_cookies['gsid'] = urllib.parse.unquote(c.value)

        new_cookies['_refreshed'] = True
        return new_cookies

    except Exception as e:
        return {**cookies_dict, "_refresh_error": str(e)}


# ─── NFToken (port từ bot tele create_nftoken) ────────────────────────────────

def create_nftoken(cookies_dict: dict, attempts: int = 3) -> tuple:
    """
    Lấy token NATIVE qua iOS FTL account.token.default — logic giống hệt bot tele.
    Trả về (token_data | None, error | None, logs).
    """
    if not cookies_dict.get("NetflixId"):
        return None, "Không tìm thấy NetflixId trong cookie", []

    cookie_header = _build_cookie_header(cookies_dict)
    logs = []
    last_error = "NFToken API error"

    for attempt in range(1, attempts + 1):
        log = {"method": f"NFToken iosui/15.48 (try {attempt})",
               "url": NFTOKEN_API_URL, "status": None, "preview": ""}
        try:
            headers = dict(NFTOKEN_HEADERS)
            headers["Cookie"] = cookie_header
            resp = requests.get(
                NFTOKEN_API_URL,
                params=NFTOKEN_QUERY_PARAMS,
                headers=headers,
                timeout=30,
                verify=False,
            )
            log["status"] = resp.status_code
            log["preview"] = (resp.text or "")[:300]
            logs.append(log)

            if resp.status_code == 403:
                last_error = "403 Forbidden — cookie có thể đã hết hạn hoặc bị chặn"
                continue
            if resp.status_code == 429:
                last_error = "429 Rate Limited — thử lại sau"
                continue
            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code} error"
                continue

            try:
                data = resp.json()
            except Exception:
                data = None

            token = None
            expires = None
            if isinstance(data, dict):
                token_data = (
                    (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default")
                    or {}
                )
                token = token_data.get("token")
                expires = token_data.get("expires")
            if not token:
                m = re.search(r'"token"\s*:\s*"([^"]+)"', resp.text or "")
                if m:
                    token = m.group(1)

            if token:
                return {"token": token, "expires": expires}, None, logs

            # HTTP 200 nhưng value rỗng {} → Netflix NHẬN request nhưng KHÔNG cấp token cho
            # account này (từ chối mềm). Hay gặp với cookie "sống" trên web nhưng luồng token
            # iOS FTL từ chối, hoặc account đã đăng xuất/đổi mật khẩu phía server.
            if isinstance(data, dict) and not (data.get("value") or {}):
                last_error = ("Netflix không cấp token (HTTP 200, value rỗng) — account bị từ chối "
                              "Cookies Hỏng")
            else:
                last_error = "Token không có trong response (cookie có thể đã hết hạn)"

        except requests.exceptions.Timeout:
            last_error = f"Timeout (attempt {attempt}/{attempts})"
            log["status"] = "ERR"
            log["preview"] = last_error
            logs.append(log)
        except requests.exceptions.RequestException as e:
            last_error = f"Network error: {e}"
            log["status"] = "ERR"
            log["preview"] = str(e)[:200]
            logs.append(log)
        except Exception as e:
            last_error = f"Unexpected error: {e}"
            log["status"] = "ERR"
            log["preview"] = str(e)[:200]
            logs.append(log)

    return None, last_error, logs


def create_nftoken_android(cookies_dict: dict, attempts: int = 3) -> tuple:
    """
    Lấy token qua Android FTL endpoint — dùng làm fallback khi iOS FTL token gây NSES-404
    trên Android app. Token được mint với ESN Android nên Netflix Android app verify tốt hơn.

    Returns: (token_data | None, error | None, logs)
    """
    if not cookies_dict.get("NetflixId"):
        return None, "Thiếu NetflixId", []

    cookie_header = _build_cookie_header(cookies_dict)
    logs = []
    last_error = "Android FTL error"

    for attempt in range(1, attempts + 1):
        log = {"method": f"NFToken androidui/15.48 (try {attempt})",
               "url": ANDROID_NFTOKEN_API_URL, "status": None, "preview": ""}
        try:
            android = _build_android_params_and_headers()
            headers = dict(android["headers"])
            headers["Cookie"] = cookie_header
            resp = requests.get(
                ANDROID_NFTOKEN_API_URL,
                params=android["params"],
                headers=headers,
                timeout=30,
                verify=False,
            )
            log["status"] = resp.status_code
            log["preview"] = (resp.text or "")[:300]
            logs.append(log)

            if resp.status_code == 403:
                last_error = "403 Forbidden"
                continue
            if resp.status_code == 429:
                last_error = "429 Rate Limited"
                continue
            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code}"
                continue

            try:
                data = resp.json()
            except Exception:
                data = None

            token = None
            expires = None
            if isinstance(data, dict):
                token_data = (
                    (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default")
                    or {}
                )
                token = token_data.get("token")
                expires = token_data.get("expires")
            if not token:
                m = re.search(r'"token"\s*:\s*"([^"]+)"', resp.text or "")
                if m:
                    token = m.group(1)

            if token:
                return {"token": token, "expires": expires}, None, logs

            if isinstance(data, dict) and not (data.get("value") or {}):
                last_error = "Android FTL: value rỗng — account bị từ chối"
            else:
                last_error = "Android FTL: token không có trong response"

        except requests.exceptions.Timeout:
            last_error = f"Timeout (attempt {attempt}/{attempts})"
            log["status"] = "ERR"
            log["preview"] = last_error
            logs.append(log)
        except requests.exceptions.RequestException as e:
            last_error = f"Network error: {e}"
            log["status"] = "ERR"
            log["preview"] = str(e)[:200]
            logs.append(log)
        except Exception as e:
            last_error = f"Unexpected error: {e}"
            log["status"] = "ERR"
            log["preview"] = str(e)[:200]
            logs.append(log)

    return None, last_error, logs


# ─── Main generation function ────────────────────────────────────────────────

def get_login_links(cookies_dict: dict, auto_refresh: bool = True, base_url: str = "") -> dict:
    """
    Tạo 1 login link dùng được cho cả PC, Android, iOS:
        https://netflix.com/?nftoken=<token>

    - PC/Desktop: mở trong trình duyệt → Netflix web set session → auto login.
    - iOS: click/paste vào Safari → Universal Link handoff sang app Netflix → auto login.
    - Android: dùng intermediary URL <base_url>/r/<token> → server trả HTML có nút
      "Mở Netflix App" → bấm vào sẽ fire intent:// → Chrome mở com.netflix.mediaclient.
      Token có hiệu lực ~1 giờ, không bị bind IP/region/device.

    Args:
        cookies_dict: dict chứa NetflixId, SecureNetflixId, nfvdid, flwssn
        auto_refresh: nếu True (mặc định), tự động refresh cookies qua /browse trước khi
                     tạo token. Giúp overcome "cookies quá cũ" issue với iOS FTL.
        base_url: URL gốc của server (vd "http://127.0.0.1:5000" hoặc "https://autologin-nf.onrender.com").
                  Dùng để build intermediary URL. Nếu rỗng, fallback dùng example.com.
    """
    if not cookies_dict.get("NetflixId"):
        return {"ok": False, "error": "Thiếu cookie: NetflixId"}

    debug = []

    if auto_refresh:
        refreshed = refresh_cookies(cookies_dict)
        if refreshed.get("_refreshed"):
            debug.append({
                "method": "Cookie refresh qua /browse",
                "old_dt": _extract_dt(cookies_dict.get("SecureNetflixId", "")),
                "new_dt": _extract_dt(refreshed.get("SecureNetflixId", "")),
            })
            cookies_dict = refreshed

    # Try iOS FTL trước (đã proven work trên iOS, có thể work trên Android)
    token_data, error, logs = create_nftoken(cookies_dict, attempts=2)
    debug.extend(logs)
    used_method = "iOS FTL NFToken 15.48 (native)"

    if not token_data:
        # Fallback: thử Android FTL endpoint (token Android-bound, work tốt hơn trên Android app)
        debug.append({
            "method": "iOS FTL failed → trying Android FTL",
            "reason": error,
        })
        token_data, error, logs = create_nftoken_android(cookies_dict, attempts=2)
        debug.extend(logs)
        used_method = "Android FTL NFToken 15.48 (fallback)"

    if error or not token_data:
        return {
            "ok": False,
            "error": error or "Cookies die (NFToken không cấp token)",
            "debug": debug,
        }

    token = token_data["token"]
    expiry = token_data.get("expires")
    return {**_build_result(token, expiry, used_method, "android", base_url=base_url), "debug": debug}


def _extract_dt(securenetflixid: str) -> str:
    """Extract dt (timestamp) từ SecureNetflixId cookie."""
    if not securenetflixid:
        return ""
    m = re.search(r'dt=(\d+)', urllib.parse.unquote(securenetflixid))
    return m.group(1) if m else ""


def get_login_links_multi_platform(cookies_dict: dict, auto_refresh: bool = True, use_browser_refresh: bool = False) -> dict:
    """
    Mint 3 token riêng cho từng platform qua MSL: laptop, iphone, android.
    Mỗi token có size/structure khác nhau (theo phân tích 3 link neogkey thật).

    Args:
        cookies_dict: dict chứa NetflixId, SecureNetflixId, nfvdid, flwssn
        auto_refresh: nếu True (mặc định), tự động refresh cookies qua /browse trước khi
                     tạo token. Giúp overcome "The cookies are bad" error từ MSL server.
        use_browser_refresh: nếu True, dùng Chrome thật (Selenium + pychrome) để refresh
                     cookies. Mạnh hơn nhiều so với HTTP refresh vì Netflix tự verify session
                     qua browser. CẦN pychrome installed.

    Returns dict có 3 link: pc_url, iphone_url, android_url + expiry + per-platform status.
    """
    if not cookies_dict.get("NetflixId"):
        return {"ok": False, "error": "Thiếu cookie: NetflixId"}

    debug = []

    # 0) Auto-refresh cookies qua Chrome thật (nếu được yêu cầu)
    if use_browser_refresh:
        try:
            from browser_refresh import refresh_cookies_via_browser
            print("[*] Refreshing cookies via browser...")
            refreshed, err = refresh_cookies_via_browser(cookies_dict, timeout=20)
            if refreshed and refreshed.get('NetflixId'):
                # Validate refresh
                import re as _re
                old_ct = _re.search(r'ct=([^&]+)', urllib.parse.unquote(cookies_dict.get('NetflixId', '')))
                new_ct = _re.search(r'ct=([^&]+)', refreshed['NetflixId'])
                if old_ct and new_ct and old_ct.group(1) != new_ct.group(1):
                    debug.append({
                        "method": "Browser refresh (Chrome thật) - CT REFRESHED",
                        "old_dt": _extract_dt(cookies_dict.get("SecureNetflixId", "")),
                        "new_dt": _extract_dt(refreshed.get("SecureNetflixId", "")),
                        "old_ct_len": len(old_ct.group(1)),
                        "new_ct_len": len(new_ct.group(1)),
                    })
                    cookies_dict = refreshed
                    print(f"[+] Cookies refreshed! new ct len: {len(new_ct.group(1))}")
                else:
                    debug.append({
                        "method": "Browser refresh (Chrome thật) - CT NOT REFRESHED",
                        "warning": err or "Netflix có thể đã reject cookies cũ",
                    })
                    print(f"[!] Browser refresh không thay đổi CT: {err}")
            else:
                debug.append({
                    "method": "Browser refresh FAILED",
                    "error": err,
                })
                print(f"[!] Browser refresh failed: {err}")
        except ImportError:
            debug.append({"method": "Browser refresh", "error": "pychrome not installed"})
            print("[!] pychrome not installed, skip browser refresh")
        except Exception as e:
            debug.append({"method": "Browser refresh exception", "error": str(e)})
            print(f"[!] Browser refresh exception: {e}")

    # 1) Auto-refresh cookies qua HTTP (nếu chưa browser-refresh)
    elif auto_refresh:
        refreshed = refresh_cookies(cookies_dict)
        if refreshed.get("_refreshed"):
            debug.append({
                "method": "Cookie refresh qua /browse (HTTP)",
                "old_dt": _extract_dt(cookies_dict.get("SecureNetflixId", "")),
                "new_dt": _extract_dt(refreshed.get("SecureNetflixId", "")),
            })
            cookies_dict = {k: v for k, v in refreshed.items() if not k.startswith("_")}

    # 1) Mint qua iOS FTL (token "nhẹ") - fallback nếu MSL fail
    fallback_data, fallback_error, logs = create_nftoken(cookies_dict, attempts=2)
    debug.extend(logs)

    # 2) Thử mint qua MSL cho 3 platform
    from msl_client import MslClient
    import logging
    logging.basicConfig(level=logging.WARNING)
    log_msl = logging.getLogger("msl")

    platforms = [
        ("laptop", "PC / Laptop (browser)"),
        ("iphone", "iPhone / iPad (iOS app)"),
        ("android", "Android (Android app)"),
    ]

    result = {
        "ok": True,
        "links": {},  # {platform: {ok, url, error, method}}
        "debug": debug,
    }

    # Tạo 1 MSL client duy nhất (chia sẻ session) cho cả 3 platform
    # Mỗi platform cần ESN riêng → 3 lần mint
    for platform_key, platform_label in platforms:
        link_info = {
            "platform": platform_key,
            "label": platform_label,
            "ok": False,
            "url": None,
            "token": None,
            "error": None,
            "method": None,
        }
        try:
            client = MslClient(cookies_dict, platform=platform_key)
            if not client.perform_key_handshake():
                link_info["error"] = "MSL handshake failed"
                link_info["method"] = "MSL handshake"
            else:
                # Request nftoken
                request_data = {
                    'version': 2,
                    'url': '/account/token',
                    'id': __import__('random').randint(1, 10**15),
                    'esn': client.esn,
                    'languages': ['en-US'],
                    'uiVersion': 'shakti-v4bf615c3',
                    'clientVersion': '6.0011.511.011',
                    'params': {'type': 'standard'},
                }
                msl_result = client.send_request(request_data)
                if not msl_result:
                    link_info["error"] = "MSL request failed (no response)"
                    link_info["method"] = f"MSL ({platform_key})"
                elif 'error' in msl_result:
                    link_info["error"] = msl_result['error']
                    link_info["method"] = f"MSL ({platform_key})"
                elif 'data_decoded' in msl_result:
                    # Parse token data
                    try:
                        token_data = __import__('json').loads(
                            msl_result['data_decoded'].decode('utf-8')
                        )
                        # Tìm token trong structure
                        # Thường: data → value → account → token → default → token
                        token = None
                        expires = None
                        if isinstance(token_data, dict):
                            td = (((token_data.get("value") or {}).get("account") or {}).get("token") or {}).get("default") or {}
                            token = td.get("token")
                            expires = td.get("expires")
                        if not token:
                            # Thử các format khác
                            import re as _re
                            m = _re.search(r'"token"\s*:\s*"([A-Za-z0-9+/=_-]{50,})"', msl_result['data_decoded'].decode('utf-8', errors='replace'))
                            if m:
                                token = m.group(1)
                        if token:
                            link_info["ok"] = True
                            link_info["url"] = LOGIN_BASE + token
                            link_info["token"] = token
                            link_info["expires"] = expires
                            link_info["method"] = f"MSL ({platform_key}, ESN {client.esn[:15]}...)"
                        else:
                            link_info["error"] = "No token in MSL response"
                            link_info["method"] = f"MSL ({platform_key})"
                            link_info["raw"] = msl_result['data_decoded'].decode('utf-8', errors='replace')[:200]
                    except Exception as e:
                        link_info["error"] = f"Parse error: {e}"
                        link_info["method"] = f"MSL ({platform_key})"
                else:
                    link_info["error"] = "Unknown MSL response format"
                    link_info["method"] = f"MSL ({platform_key})"
                    link_info["raw"] = str(msl_result)[:200]
        except Exception as e:
            link_info["error"] = f"{type(e).__name__}: {e}"
            link_info["method"] = f"MSL ({platform_key})"
        result["links"][platform_key] = link_info

    # 3) Nếu TẤT CẢ MSL fail, dùng iOS FTL fallback cho laptop (vẫn tốt hơn không có gì)
    all_failed = all(not info["ok"] for info in result["links"].values())
    if all_failed and fallback_data and not fallback_error:
        result["links"]["laptop"]["ok"] = True
        result["links"]["laptop"]["url"] = LOGIN_BASE + fallback_data["token"]
        result["links"]["laptop"]["token"] = fallback_data["token"]
        result["links"]["laptop"]["method"] = "iOS FTL (fallback cho cả 3 platform)"
        result["links"]["laptop"]["expires"] = fallback_data.get("expires")
        result["links"]["laptop"]["error"] = None
        result["links"]["laptop"]["fallback"] = True
        result["links"]["laptop"]["fallback_note"] = (
            "MSL mint thất bại, dùng iOS FTL token làm fallback. "
            "Token này sẽ hoạt động cho cả 3 platform (giống hệt neogkey link PC)."
        )
        # 2 cái còn lại vẫn fail
        for k in ("iphone", "android"):
            if not result["links"][k]["ok"]:
                result["links"][k]["fallback"] = True
                result["links"][k]["fallback_url"] = result["links"]["laptop"]["url"]
                result["links"][k]["fallback_note"] = (
                    f"Dùng cùng link laptop ({result['links']['laptop']['url'][:60]}...). "
                    "Mở trên thiết bị, paste vào Chrome/Safari → 'Open App' → 'Continue'."
                )

    # Backward compat
    if result["links"].get("laptop", {}).get("ok"):
        result["url"] = result["links"]["laptop"]["url"]
        result["token"] = result["links"]["laptop"]["token"]

    return result


# ─── Debug probe ──────────────────────────────────────────────────────────────

def probe_endpoint(cookies_dict: dict, url: str, method: str = "POST") -> dict:
    """Test endpoint tùy ý với cookies đã cho (dùng header NFToken + cookie)."""
    headers = dict(NFTOKEN_HEADERS)
    headers["Cookie"] = _build_cookie_header(cookies_dict)

    try:
        if method.upper() == "POST":
            resp = requests.post(url, headers=headers, timeout=30, verify=False)
        else:
            resp = requests.get(url, headers=headers, timeout=30, verify=False)
        body_preview = (resp.text or "")[:1500]
        return {
            "status": resp.status_code,
            "body": body_preview,
            "cookies_sent": list(cookies_dict.keys()),
            "token_found": ('"token"' in body_preview) or ("createAutoLoginToken" in body_preview),
        }
    except Exception as e:
        return {
            "status": "ERR",
            "body": str(e)[:300],
            "cookies_sent": list(cookies_dict.keys()),
            "token_found": False,
        }
