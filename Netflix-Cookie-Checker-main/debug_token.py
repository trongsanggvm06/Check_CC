"""
Debug script - kiểm tra tại sao NFToken API thất bại với cookie JSON.
"""
import json
import requests
from urllib.parse import unquote, quote
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

COOKIE_JSON = '[{"domain":".netflix.com","hostOnly":false,"httpOnly":false,"name":"flwssn","path":"/","sameSite":"unspecified","secure":false,"session":false,"storeId":"0","value":"372bdc61-d66d-4db3-bdcd-0a22dc1bd5b5"},{"domain":".netflix.com","hostOnly":false,"httpOnly":false,"name":"nfvdid","path":"/","sameSite":"unspecified","secure":false,"session":false,"storeId":"0","value":"BQFmAAEBEELW9vGgqdosogOpWKUfNMVgISvIT0CUd6eHvdkhrUmlUB1OQcIm2jmjB82SxlyghfaalJTI7C9DMlsctQoe4AaP-mYjVQ7YwDD084GFvVbWMr2o3yMXWGb0yWgTqVvp_ZMwZi5tx50HA39afCjI8Tog"},{"domain":".netflix.com","hostOnly":false,"httpOnly":true,"name":"SecureNetflixId","path":"/","sameSite":"strict","secure":true,"session":false,"storeId":"0","value":"v%3D3%26mac%3DAQEAEQABABShvs3iWJn6r770IIP5DaDR7sWt0wFQIjQ.%26dt%3D1770367143648"},{"domain":".netflix.com","hostOnly":false,"httpOnly":true,"name":"NetflixId","path":"/","sameSite":"lax","secure":true,"session":false,"storeId":"0","value":"v%3D3%26ct%3DBgjHlOvcAxLZAzLy5v5nBEdr537w_RVJGovPkfch6zSDL4AO6AoRyL5aYXs1hWsHX6R3r6Jq135kntIxLpbblWcX_a0XDSdhAcN5mQtWn5pMb09oAD8_JvlAt0XSHDfvHfwqdqo9IaaqNLkqdsvkW4lMxKaqo5jeULamw_kBLQagJ1xBLVXWzdR0yBhGw3ZyY6xgZS6NZgHtxFsTSHSKCA7NM7pq0BF9pj10Irh90WzcPvbRImJG3cNBKnysXmLKXDFkrvchmPABZzJEWzCZDMMySkMG4GsQDs57HDy35G9hLgRbBcy60MLloeHI3ur97dGVcXJaSj6VqhW0MUad4FR22flZEoonjrw07qqbg5ohkJn5ip1Kz7wof5lN_zEJjFW6nucxY1m6o0yq5OjjmeJIJjwmFCHcTyHm3rUiRIy-87ZTkiAo-wanDIB28KIl1kPI2GJLG2C75rbLWA-pvKICRcHw59FjXiZyLWzO84xPXA-Bt0a7cb6jXwIY895754XLkJYKn__VpvjokHKIbhrr_HIwUdIsBKGRevf2-g8YYka2rfT168Cm1bwTC7bfYA5MBYDemUGSPMGQwJFmGW6si034vVjd5ffeXN5rRGRh-2Dn-tkzZokxYsb-oqucg9ynGAYiDgoMnLhRmnsEFQ3OrcQX%26pg%3DOADCTHBCCZGSJEQAXZRKISPSI4%26ch%3DAQEAEAABABS_z37JdSQVXaHTJWrtnMv5QS1XqVbEicU."}]'

# --- Parse cookie ---
items = json.loads(COOKIE_JSON)
cookies = {item["name"]: item["value"] for item in items if item.get("name") and item.get("value")}

netflix_id_raw = cookies.get("NetflixId", "")
netflix_id_decoded = unquote(netflix_id_raw)

print("=" * 70)
print("📋 COOKIE INFO")
print("=" * 70)
print(f"Keys parsed       : {list(cookies.keys())}")
print(f"NetflixId (raw)   : {netflix_id_raw[:80]}...")
print(f"NetflixId (decoded): {netflix_id_decoded[:80]}...")
print()

# --- NFToken API params ---
NFTOKEN_API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"
NFTOKEN_QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
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
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "accept-language": "en-US;q=1",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
}

def test_request(label, cookie_header_value):
    print(f"🔬 TEST: {label}")
    print(f"   Cookie sent: NetflixId={cookie_header_value[:60]}...")
    headers = dict(NFTOKEN_HEADERS)
    headers["Cookie"] = f"NetflixId={cookie_header_value}"
    try:
        r = requests.get(
            NFTOKEN_API_URL,
            params=NFTOKEN_QUERY_PARAMS,
            headers=headers,
            timeout=20,
            verify=False,
        )
        print(f"   HTTP Status : {r.status_code}")
        print(f"   Response    : {r.text[:300]}")
    except Exception as e:
        print(f"   ERROR       : {e}")
    print()

print("=" * 70)
print("🧪 TESTING NFToken API")
print("=" * 70)
print()

# Test 1: raw (URL-encoded) value
test_request("Raw URL-encoded value (original code)", netflix_id_raw)

# Test 2: decoded value (current fix)
test_request("URL-decoded value (my fix)", netflix_id_decoded)

# Test 3: All cookies included
print("🔬 TEST: All cookies included (like checkacc does)")
headers = dict(NFTOKEN_HEADERS)
all_cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
headers["Cookie"] = all_cookie_str
print(f"   Cookies sent: {list(cookies.keys())}")
try:
    r = requests.get(
        NFTOKEN_API_URL,
        params=NFTOKEN_QUERY_PARAMS,
        headers=headers,
        timeout=20,
        verify=False,
    )
    print(f"   HTTP Status : {r.status_code}")
    print(f"   Response    : {r.text[:300]}")
except Exception as e:
    print(f"   ERROR       : {e}")
print()

# Test 4: Use requests.Session like checkacc
print("🔬 TEST: requests.Session with cookies dict (like checkacc)")
session = requests.Session()
session.cookies.update(cookies)
headers2 = dict(NFTOKEN_HEADERS)
try:
    r = session.get(
        NFTOKEN_API_URL,
        params=NFTOKEN_QUERY_PARAMS,
        headers=headers2,
        timeout=20,
        verify=False,
    )
    print(f"   HTTP Status : {r.status_code}")
    print(f"   Response    : {r.text[:300]}")
except Exception as e:
    print(f"   ERROR       : {e}")
print()

print("=" * 70)
print("DONE")
