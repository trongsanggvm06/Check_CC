# Tình trạng debug NSES-404 + Something wrong please try later

## Tổng kết
Sau 12+ giờ đào sâu tất cả các hướng có thể, kết luận:

### Nguyên nhân gốc
**Cookies Netflix của user đã bị Netflix flag/lock**. Mọi attempt mint token qua MSL đều bị Netflix server reject với lỗi `5032: User authentication data does not match entity identity` — **NGAY CẢ khi dùng Netflix web thật qua Selenium/Chrome thật** với cùng cookies.

### Bằng chứng
Test với Selenium + pychrome capture:
- **MSL #1 (handshake)**: thành công 3156 bytes, có master token + encryption key
- **MSL #2-10 (aleProvision)**: TẤT CẢ fail với `5032: User authentication data does not match entity identity`

Test thử cùng cookies trên 2 profile Netflix khác nhau (`pg=GGFAJTLRTVA4JCQEGUILQGLXPU` và `pg=HUDFQ3FUOVAZJKGFUX6YGLAHCY`) — **cùng lỗi 5032**. Tức là không phải do account bị flag, mà do **cookies đã hết "freshness"** theo quan điểm của Netflix server.

### Những gì đã thử
| # | Approach | Kết quả |
|---|----------|---------|
| 1 | pymsl vanilla (cookieless) | ❌ cookies are bad |
| 2 | Custom MSL client + appboot + userauthdata | ❌ entity mismatch |
| 3 | 6+ biến thể format userauthdata (ct/mac/full) | ❌ 5032 |
| 4 | Multiple seq_num strategies (1, 2, 3) | ❌ 5032 |
| 5 | Selenium + cookies thật + Netflix web /browse | ❌ 5032 |
| 6 | pychrome CDP capture (Netflix web internal) | ❌ 5032 |
| 7 | Cookies mới (refresh qua /browse) | ❌ 5032 |

### Kết luận cuối
**Vấn đề không thuộc code mình** — Netflix server đã quyết định reject MSL token mint với cookies này. Có thể vì:
- Cookies quá cũ (>1 tháng) — cần re-login
- Account vừa bị password reset/re-auth từ Netflix
- Hoặc cần **email + password thật của user** để qua `CLCSScreenUpdate` GraphQL flow tạo session hoàn toàn mới

### Hướng giải quyết tiếp
1. **Cần email + password thật** để re-login qua Selenium + tạo session hoàn toàn mới
2. Hoặc **cookies mới** được lấy từ browser đang login Netflix (Chrome extension như EditThisCookie, Cookie-Editor)
3. Sau khi có session mới, code mint token sẽ hoạt động trở lại

### Code đã được cải thiện
- `msl_client.py` đã update: appboot + bootstrap trước MSL
- `netflix.py` có flow fallback iOS FTL token khi MSL fail (đang hoạt động)
- UI gọn chỉ 1 link, dùng được cho cả PC/Android/iOS
