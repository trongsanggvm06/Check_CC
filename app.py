from flask import Flask, render_template, request, jsonify, url_for, redirect
import urllib.parse
import config
from netflix import (
    parse_cookies,
    parse_cookie_blocks,
    get_login_links,
    refresh_cookies,
    split_cookie_blocks,
    to_cookie_editor_json,
    _extract_dt,
)
from account_info import fetch_account_minimal

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


def _get_base_url() -> str:
    """
    Lấy URL gốc của server đang host (vd "https://autologin-nf.onrender.com").
    Dùng để build intermediary URL trong response của /api/generate.
    Ưu tiên:
      1. Environment variable PUBLIC_BASE_URL (nếu deploy manual config)
      2. request.host_url (tự detect từ request, vd "http://127.0.0.1:5000/")
    """
    import os
    env_base = os.environ.get("PUBLIC_BASE_URL", "").strip()
    if env_base:
        return env_base.rstrip("/")
    return request.host_url.rstrip("/")


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    return jsonify({"ok": False, "error": f"Lỗi server nội bộ: {type(err).__name__}"}), 500


@app.route("/")
def index():
    return render_template("index.html", title=config.APP_TITLE, subtitle=config.APP_SUBTITLE)


# Trang trung gian /r/<token>: MỤC ĐÍCH = thoát WebView app chat (Zalo/Messenger) ra
# TRÌNH DUYỆT MẶC ĐỊNH của máy, rồi mở netflix.com/?nftoken= ở đó. Vì Netflix app dùng
# trình duyệt mặc định làm Custom Tab khi handoff — phải redeem token CÙNG browser đó thì
# cookie mới chung → app login được (nếu redeem trong WebView chat thì cookie không chung
# → NSES-404). JS trong redirect.html bắn intent:// VIEW (no-package) sang browser mặc định.
# Dùng <path:token> để capture cả dấu / có trong token (token Netflix chứa cả + và /).
# Token trong URL phải được URL-encoded (safe="" để giữ nguyên /) — khi browser mở
# link thì tự decode lại thành token gốc.
@app.route("/r/<path:token>")
def redirect_intermediary(token):
    # Flask đã tự URL-decode token rồi (dấu + thành space, %2B vẫn là +).
    # Để chắc chắn token còn nguyên vẹn, ta chỉ cần dùng nó trực tiếp trong HTML.
    # Token chỉ có thời hạn ~59 phút (1 giờ của Netflix). Hiển thị countdown.
    return render_template(
        "redirect.html",
        nftoken=token,
        expiry_min=59,
    )


@app.route("/go/<path:token>")
def go_redirect(token):
    # SERVER 302 sang netflix.com/?nftoken= (no-www). Vì là SERVER redirect nên trình
    # duyệt KHÔNG hand sang app Netflix (App Link chỉ kích khi click/intent trực tiếp,
    # KHÔNG kích trên redirect) → token redeem NGAY TRONG trình duyệt → /unsupported →
    # khách bấm "Open App" của Netflix → app handoff cùng browser → login.
    # /r/ (domain ta) lo việc thoát WebView; /go lo việc đẩy sang netflix mà không bị app cướp.
    # QUAN TRỌNG: trỏ /unsupported?nftoken= (KHÔNG phải /?nftoken=). Vì /?nftoken= sẽ qua
    # chuỗi redirect / → /browse → /unsupported, mà /browse là App Link app CÓ claim → app
    # cướp /browse giữa chừng → mở app COLD → NSES-404/Google chooser. /unsupported?nftoken=
    # vẫn redeem token NHƯNG vào thẳng /unsupported (path app KHÔNG claim) → không bị cướp →
    # dừng ở trang "Open App" đã-login → tap Open App → handoff đúng → login app.
    from flask import redirect
    return redirect("https://netflix.com/unsupported?nftoken=" + token, code=302)


@app.route("/api/generate", methods=["POST"])
def generate():
    body = request.get_json(silent=True) or {}
    raw = body.get("cookies", "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "Vui lòng nhập cookie"}), 400

    parsed_blocks = parse_cookie_blocks(raw)
    cookies_dict = parsed_blocks[0] if parsed_blocks else parse_cookies(raw)
    if not cookies_dict:
        blocks = split_cookie_blocks(raw)
        if len(blocks) > 1:
            return jsonify({
                "ok": False,
                "error": (f"Bạn paste {len(blocks)} bộ cookie nhưng đang ở tab Đơn lẻ "
                          f"(chỉ xử lý 1). Hãy chuyển sang tab 📦 Batch."),
                "suggest_tab": "tab-batch",
                "count": len(blocks),
            }), 400
        return jsonify({"ok": False, "error": "Không thể đọc cookie, kiểm tra định dạng"}), 400
    result = get_login_links(cookies_dict, auto_refresh=body.get("auto_refresh", True), base_url=_get_base_url())
    return jsonify(result)


@app.route("/api/refresh-cookies", methods=["POST"])
def refresh_cookies_endpoint():
    body = request.get_json(silent=True) or {}
    raw = body.get("cookies", "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "Vui lòng nhập cookie"}), 400

    cookies_dict = parse_cookies(raw)
    if not cookies_dict:
        return jsonify({"ok": False, "error": "Không đọc được cookie"}), 400

    old_dt = _extract_dt(cookies_dict.get("SecureNetflixId", ""))
    refreshed = refresh_cookies(cookies_dict)
    new_dt = _extract_dt(refreshed.get("SecureNetflixId", ""))
    refreshed_ok = refreshed.get("_refreshed", False)
    refresh_error = refreshed.get("_refresh_error")

    return jsonify({
        "ok": refreshed_ok,
        "error": refresh_error,
        "old_dt": old_dt,
        "new_dt": new_dt,
        "cookies": {k: v for k, v in refreshed.items() if not k.startswith("_")},
    })


@app.route("/api/split", methods=["POST"])
def split():
    body = request.get_json(silent=True) or {}
    raw_all = body.get("cookies", "").strip()
    if not raw_all:
        return jsonify({"ok": False, "error": "Vui lòng nhập cookie"}), 400

    # Tách input thành các block GIỮ NGUYÊN VĂN BẢN GỐC — KHÔNG decode / re-serialize.
    # Mục đích: cookie lúc check và cookie khi tải file (life.txt/die.txt) phải KHỚP
    # CHÍNH XÁC với cookie người dùng dán vào (vd JSON array Cookie-Editor, value còn
    # URL-encode dạng v%3D3%26ct%3D...). Trước đây bước này hydrate lại từ dict ĐÃ decode
    # rồi ghép "NetflixId=...; SecureNetflixId=..." nên file tải về bị đổi sang dạng
    # "NetflixId=v=3&ct=..." (value đã giải mã) — SAI so với cookie đầu vào.
    raw_blocks = split_cookie_blocks(raw_all)

    # Bỏ block rác (không parse ra được cookie key nào), rồi CHUẨN HOÁ mỗi block hợp lệ về
    # JSON Cookie-Editor: JSON hợp lệ -> giữ nguyên; chuỗi thô -> dựng JSON + re-encode value.
    # Nhờ vậy block dùng để check VÀ block tải về file luôn import lại Cookie-Editor được.
    valid_blocks = [to_cookie_editor_json(b) for b in raw_blocks if parse_cookies(b)]
    blocks = valid_blocks if valid_blocks else raw_blocks

    return jsonify({"ok": True, "blocks": blocks, "count": len(blocks)})


@app.route("/api/account-info", methods=["POST"])
def account_info_endpoint():
    """
    Lấy `Next Payment` + `Plan` từ cookie (đã được /api/generate xác nhận là LIFE).
    Endpoint BỔ SUNG, không động vào /api/generate hay logic die/life.
    """
    body = request.get_json(silent=True) or {}
    raw = body.get("cookies", "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "Vui lòng nhập cookie"}), 400

    try:
        result = fetch_account_minimal(raw, timeout=20)
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Lỗi: {exc}"}), 500

    if not result.get("ok"):
        return jsonify(result), 200

    return jsonify({
        "ok": True,
        "next_payment": result.get("next_payment"),
        "plan": result.get("plan"),
        "raw": result.get("raw", {}),
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", config.PORT))
    print(f"[*] App chạy tại http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=config.DEBUG, threaded=True)
