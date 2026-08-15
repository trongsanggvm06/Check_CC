PORT = 5000
DEBUG = False
SECRET_KEY = "n3tf1ix-l0g1n-4pp-2024-xK9mP2vL8wQ3hJ5nR7sT1uY6zA0bC4dE"

# --- Auth credentials (Basic Auth) ---
# Hiện tại không dùng — app public cho vài người dùng
import os
AUTH_USER = ""
AUTH_PASS = ""

# --- Tuỳ chỉnh tiêu đề hiển thị ---
APP_TITLE = "Netflix Login Link Generator"
APP_SUBTITLE = "Chuyển đổi Cookie Netflix thành Link Đăng Nhập"

# --- URL đăng nhập — phân biệt theo platform ---
#   PC / Web / iPhone / iPad → https://netflix.com/?nftoken=<token>  (Universal Link iOS + web login PC)
#   Android                  → <base_url>/r/<token>                (HTTPS landing page của ta; landing page có
#                                                                     nút "Mở Netflix App" → fire intent:// →
#                                                                     Chrome mở com.netflix.mediaclient)
# Lý do KHÔNG dùng https://netflix.com/unsupported?nftoken= cho Android:
#   - Path /unsupported KHÔNG được đăng ký trong AASA / Digital Asset Links của Netflix Android app.
#   - Chrome Android mở nó như 1 trang web bình thường (form email/password), KHÔNG handoff sang app.
#   - Token bị bỏ qua → Netflix trả về NSES-404 ("Lost your way?").
# Token mint qua iOS FTL (ios.prod.ftl.netflix.com/iosui/user/15.48) — y hệt bot gốc.
LOGIN_BASE = "https://netflix.com/?nftoken="                         # PC / Web / iPhone / iPad
# MOBILE_LOGIN_BASE sẽ được build runtime = base_url + /r/<encoded_token>
# → xem _build_result() trong netflix.py
# Giữ constant này rỗng để tương thích code cũ (sẽ tự dùng intermediary_url):
MOBILE_LOGIN_BASE = ""

# ─── ENDPOINT TUỲ CHỈNH ────────────────────────────────────────────────────
# Nếu bạn biết đúng endpoint Netflix, điền vào đây.
# Ví dụ: "https://www.netflix.com/api/shakti/v1db76858/loginWithToken"
# Để trống ("") để dùng danh sách endpoint tự động.
CUSTOM_ENDPOINT = ""

# --- User-Agent cho requests ---
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# --- Màu sắc theme (hex) ---
THEME_PRIMARY = "#E50914"
THEME_BG = "#141414"
THEME_CARD = "#1f1f1f"
