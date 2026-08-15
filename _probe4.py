"""
Probe vòng 3 — đào tầng giao thức: các endpoint app native dùng để LOGIN.
Mục tiêu: tìm endpoint nào nhận cookie web → cấp sign-in code / sign-in link / device auth
mà KHÔNG cần app khởi tạo. Nếu có → reseller có thể tự sinh.
"""
import sys, json, urllib.parse, requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
sys.path.insert(0, ".")
from netflix import parse_cookies, create_nftoken, _build_cookie_header, COOKIE_KEYS

cd = parse_cookies(open("_cookies_in.json","r",encoding="utf-8").read())
token_data, err, logs = create_nftoken(cd, attempts=2)
NFTOKEN = token_data["token"] if token_data else None
print("nftoken:", "OK" if NFTOKEN else err)
ch = _build_cookie_header(cd)

DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def show(name, r):
    if r is None:
        print(f"  [ERR] {name}"); return
    loc = r.headers.get("Location","")[:90]
    ct = r.headers.get("Content-Type","")[:30]
    print(f"  [{r.status_code}] {name}  ct={ct} {('-> '+loc) if loc else ''}")
    body = (r.text or "")[:400]
    for marker in ['"code"','"signInCode"','"token"','rendezvous','authURL','authorizationCode',
                   'PERMISSION_DENIED','NoAuthSession','"errorCode"','signInLink','sendSignIn',
                   'requestCode','membershipStatus','"loginCode"','deviceCode']:
        if marker in (r.text or ""):
            print(f"        >> {marker}")
    return r

def G(name, url, headers=None, **kw):
    h = {"User-Agent": DESKTOP_UA, "Cookie": ch}
    if headers: h.update(headers)
    try:
        return show(name, requests.get(url, headers=h, timeout=20, verify=False, allow_redirects=False, **kw))
    except Exception as e:
        print(f"  [EXC] {name}: {str(e)[:120]}"); return None

def P(name, url, headers=None, data=None, jsonbody=None):
    h = {"User-Agent": DESKTOP_UA, "Cookie": ch}
    if headers: h.update(headers)
    try:
        return show(name, requests.post(url, headers=h, data=data, json=jsonbody, timeout=20, verify=False, allow_redirects=False))
    except Exception as e:
        print(f"  [EXC] {name}: {str(e)[:120]}"); return None

print("\n=== A. SHAKTI API: tìm pathEvaluator / endpoint nội bộ web (cần authURL) ===")
# Lấy authURL + build từ trang browse trước
s = requests.Session()
for k in COOKIE_KEYS:
    v = cd.get(k)
    if v:
        s.cookies.set(k, urllib.parse.quote(v, safe="-_.~") if "%" not in v else v, domain=".netflix.com")
r = s.get("https://www.netflix.com/browse", headers={"User-Agent":DESKTOP_UA}, verify=False, timeout=20, allow_redirects=True)
html = r.text or ""
import re
authURL = None
m = re.search(r'"authURL"\s*:\s*"([^"]+)"', html)
if m: authURL = m.group(1)
mb = re.search(r'"BUILD_IDENTIFIER"\s*:\s*"([^"]+)"', html) or re.search(r'"build"\s*:\s*"([^"]+)"', html)
build = mb.group(1) if mb else None
print("  authURL:", (authURL[:40]+"...") if authURL else None, "| build:", build, "| final:", r.url[:50])

print("\n=== B. Endpoint sign-in CODE / LINK (app dùng) — thử với cookie web ===")
# Các tên đường giả định app gọi để xin code/link
for path in ["/api/signin/code", "/api/sendSignInCode", "/aui/pathEvaluator",
             "/account/getSignInCode", "/signin/code", "/login/code",
             "/api/oauth2/token", "/oauth2/token", "/oauth/token",
             "/ums/v2/oauth2/token", "/nq/aui/oauth2/token"]:
    G(f"GET {path}", f"https://www.netflix.com{path}")

print("\n=== C. iOS FTL — thử các path token KHÁC ngoài account.token.default ===")
from netflix import NFTOKEN_API_URL, NFTOKEN_QUERY_PARAMS, NFTOKEN_HEADERS
for pathexpr in ['["account","signInCode"]','["account","oauthToken"]','["account","deviceToken"]',
                 '["account","token","mobile"]','["account","token","webview"]',
                 '["account","autoLoginToken"]','["account","signInLink"]']:
    params = dict(NFTOKEN_QUERY_PARAMS); params["path"] = pathexpr
    h = dict(NFTOKEN_HEADERS); h["Cookie"] = ch
    try:
        rr = requests.get(NFTOKEN_API_URL, params=params, headers=h, timeout=20, verify=False)
        t = (rr.text or "")[:200]
        has = "token" if '"token"' in (rr.text or "") else ("value-empty" if '"value":{}' in (rr.text or "") else "?")
        print(f"  [{rr.status_code}] path={pathexpr}  {has}  {t[:90]}")
    except Exception as e:
        print(f"  [EXC] {pathexpr}: {str(e)[:80]}")

print("\n=== D. GraphQL createAutoLoginToken (token WEBVIEW) — scope khác ===")
gql_url = "https://www.netflix.com/api/shakti/{b}/pathEvaluator".format(b=build or "vffffffff")
for scope in ["WEBVIEW_MOBILE_STREAMING","MOBILE_NATIVE","ANDROID_APP","WEBSITE"]:
    body = {"path": json.dumps(["createAutoLoginToken", scope]), "method":"call"}
    P(f"createAutoLoginToken {scope}", gql_url + ("?" + urllib.parse.urlencode({"authURL":authURL}) if authURL else ""),
      headers={"Content-Type":"application/x-www-form-urlencoded"}, data=body)

print("\n=== E. /tv2 rendezvous — thử redeem code ngược (web cấp code cho 1 device chờ?) ===")
G("GET /tv2", "https://www.netflix.com/tv2")
G("GET /tv8", "https://www.netflix.com/tv8")
