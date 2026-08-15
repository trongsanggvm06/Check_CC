# Hướng Dẫn Đăng Nhập Netflix Theo Từng Thiết Bị

## Tổng Quan

Mỗi thiết bị có một luồng riêng để đảm bảo token được redeem đúng cách mà không bị Netflix phát hiện/bắt.

---

## 1. PC / Web (Windows, Mac, Linux)

### Link được cấp:
```
https://netflix.com/?nftoken=<TOKEN>
```

### Cách đăng nhập:

1. **Copy** link từ ứng dụng
2. **Paste** trực tiếp vào **thanh địa chỉ** trình duyệt (Chrome, Edge, Firefox đều được)
3. **Enter** — trình duyệt tự động:
   ```
   /?nftoken=<TOKEN>
        ↓ HTTP GET (301)
   /
        ↓ HTTP GET (302)
   /browse
        ↓ (đã login, redirect tự động)
   Trang chính Netflix
   ```

### Tại sao hoạt động:
- Trình duyệt gửi request với User-Agent desktop → Netflix nhận diện là PC
- Cookie login được set ngay trong browser session
- Không qua bất kỳ app hay WebView trung gian nào
- Token redeem **hoàn toàn trong trình duyệt**

### Lưu ý:
- **ĐÚNG**: Paste vào thanh địa chỉ
- **KHÔNG**: Mở từ link trong Telegram/chat app (sẽ mở trong WebView của app đó, cookie không chung với trình duyệt chính)

---

## 2. iPhone / iPad (iOS Safari)

### Link được cấp:
```
https://netflix.com/unsupported?nftoken=<TOKEN>
```

### Cách đăng nhập:

1. **Copy** link từ ứng dụng
2. **Mở Safari** trên iPhone/iPad
3. **Paste** vào thanh địa chỉ Safari
4. **Enter** — Netflix sẽ:
   ```
   /unsupported?nftoken=<TOKEN>
        ↓ HTTP GET (301) — set NetflixId cookie
   /unsupported
        ↓ (trang "Open in App")
   Trang hỏi "Open this page in Netflix?"
   ```

5. **Bấm nút "Open"** (hoặc "Mở" trong tiếng Việt)
   - iOS handoff sang app Netflix
   - App Netflix mở ở trạng thái **warm** (đã có session)
   - → **Đăng nhập thành công**

### Tại sao dùng `/unsupported`:

| Path | Universal Link (iOS) | Hành vi |
|---|---|---|
| `/?nftoken=` | ❌ Bị exclude (`/?*`) | Safari mở web, không handoff |
| `/unsupported?nftoken=` | ❌ Bị exclude | Safari hiện nút "Open App" |
| `/browse?nftoken=` | ✅ App claimed | App mở COLD → NSES-404 |

→ `/unsupported` **KHÔNG tự động handoff**, user phải TAP nút — đây là **intentional design** của Netflix để:
- Ngăn app mở lạnh (cold start) không có session
- Đảm bảo token được redeem trong cùng browser session trước khi handoff

### Lưu ý:
- **ĐÚNG**: Paste vào Safari, bấm "Open" khi thấy thông báo
- **KHÔNG**: Mở từ link trong Telegram/chat app (sẽ dùng WKWebView của app, không phải Safari thật)
- **KHÔNG**: Dùng Chrome iOS — Chrome iOS dùng WKWebView giống app, không phải Safari
- **ĐÚNG**: Dùng **Safari iOS** — đây là browser duy nhất handoff đúng sang Netflix app

---

## 3. Android (Chrome)

### Link được cấp:
```
https://<YOUR_SERVER>/r/<TOKEN>
```
(ví dụ: `https://autologin-nf.onrender.com/r/Bgi8u%2BvcAx...`)

### Cách đăng nhập:

**Từ link trong chat app (Telegram, Zalo, Messenger):**

1. **Bấm vào link** → mở landing page trên **Chrome Android**
   ```
   https://<server>/r/<TOKEN>
        ↓
   Landing page: countdown + nút "Open Netflix"
   ```

2. **Đợi 350ms** hoặc **bấm nút "Open Netflix"**
   - JavaScript phát hiện đang ở trong WebView chat
   - Bắn `intent://` để thoát ra **Chrome Android thật** (trình duyệt mặc định)
   - Chrome Android mở link `/go/<TOKEN>`

3. **Server redirect** tự động:
   ```
   /go/<TOKEN>
        ↓ HTTP 302
   https://netflix.com/unsupported?nftoken=<TOKEN>
        ↓ HTTP GET (301) — set NetflixId cookie
   /unsupported
        ↓
   Trang "Open Netflix?"
   ```

4. **Bấm nút "Open"** (nếu có) hoặc **app Netflix tự mở**
   - App Netflix nhận session từ Chrome
   - → **Đăng nhập thành công**

**Từ Chrome Android trực tiếp:**

1. Copy link
2. Mở Chrome Android
3. Paste vào thanh địa chỉ
4. Bấm nút "Open" (banner "Open in app" hoặc trên /unsupported page)
5. App Netflix mở → **Đăng nhập**

### Tại sao dùng intermediary page:

Netflix Android app đăng ký **Digital Asset Links** cho các path App Link:
- `/watch/*`, `/browse/*`, `/title/*`, v.v. → App tự động mở
- `/?nftoken=` → **Không** được claim → Chrome mở như web

→ Link `https://netflix.com/?nftoken=` mở trang web (form login), không handoff sang app.

→ Intermediary page dùng `intent://` để force open app sau khi token đã redeem.

### Lưu ý:
- **ĐÚNG**: Bấm link từ chat → landing page → thoát ra Chrome thật → "Open"
- **KHÔNG**: Paste trực tiếp `https://netflix.com/?nftoken=` vào Chrome (sẽ mở web, không phải app)
- **QUAN TRỌNG**: Luôn dùng link có `/r/<TOKEN>` (intermediary) cho Android, không dùng link `https://netflix.com/?nftoken=`

---

## 4. Android TV / Smart TV

### Link được cấp:
```
https://netflix.com/?nftoken=<TOKEN>
```

### Cách đăng nhập:

1. **Trên TV**: Mở trình duyệt TV (nếu có)
2. **Trên điện thoại/pc**: Truy cập `https://www.netflix.com/activate`
3. Nhập **mã xác thực** hiển thị trên TV
4. **Đăng nhập thành công** trên TV

**HOẶC** (nếu TV có trình duyệt):

1. Mở trình duyệt trên TV
2. Truy cập link: `https://netflix.com/?nftoken=<TOKEN>`
3. TV tự đăng nhập

### Lưu ý:
- Smart TV thường không mở app được từ link (không có App Link)
- Cách an toàn nhất: dùng `netflix.com/activate`

---

## Bảng Tổng Hợp

| Thiết bị | Link dùng | Browser/App | Hành động | Notes |
|---|---|---|---|---|
| **PC Windows/Mac** | `https://netflix.com/?nftoken=` | Chrome/Edge/Firefox | Paste → Enter | Paste trực tiếp, không từ chat |
| **iPhone/iPad** | `https://netflix.com/unsupported?nftoken=` | **Safari iOS** | Paste → Enter → Tap "Open" | KHÔNG dùng Chrome iOS |
| **Android Phone** | `<server>/r/<TOKEN>` | Chrome Android | Bấm link → Tap "Open" | Dùng intermediary, không paste trực tiếp |
| **Android TV** | `https://netflix.com/?nftoken=` | TV Browser | Paste → Enter | Hoặc dùng netflix.com/activate |

---

## Sai Lầm Phổ Biến

### ❌ Sai: Mở link từ Telegram/Zalo
```
User bấm link trong Telegram → Telegram mở trong WebView
→ Token redeem TRONG WebView → Cookie không chung với Chrome/Safari
→ Khi app Netflix mở → Không có session → NSES-404
```

**Fix**: Từ chat app → bấm "Open in Browser" → mở Chrome thật → redeem

### ❌ Sai: iOS dùng Chrome thay vì Safari
```
Chrome iOS dùng WKWebView (giống app chat)
→ Không handoff đúng sang Netflix app
→ Phải dùng Safari iOS
```

### ❌ Sai: Android paste trực tiếp link Netflix
```
User copy https://netflix.com/?nftoken=<TOKEN>
→ Paste vào Chrome Android
→ Chrome mở trang web, KHÔNG mở app
→ Phải dùng intermediary /r/<TOKEN>
```

---

## Lý Do Kỹ Thuật

### Tại sao Netflix không phát hiện?

1. **Token không bị encode sai**: `+` trong base64 token được giữ nguyên, Netflix server decode đúng
2. **Cookie chung session**: User redeem token trong cùng browser session mà Netflix app dùng làm Custom Tab
3. **Warm handoff**: iOS/Android nhận session đã có từ browser, không phải khởi tạo lạnh
4. **Timing**: Token có hiệu lực ~59 phút, redeem ngay lập tức không có delay đáng nghi
