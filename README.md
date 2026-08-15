# Netflix Cookie Checker - Login Link Generator

Ung dung Flask nhan cookie Netflix, sinh auto-login link cho 3 platform (PC / iPhone / Android), ho tro check batch nhieu cookie cung luc va xuat file life.txt / die.txt.

## Tinh nang

- Sinh link nftoken qua iOS FTL endpoint.
- Batch check nhieu cookie, phan loai LIVE / DIE theo thoi gian thuc.
- Xuat life.txt theo dinh dang: COOKIE = ... | Next Payment = ... | Plan = ...
- Endpoint /r/<token> trung gian giup thoat WebView chat sang browser mac dinh truoc khi mo Netflix.

## Chay local

```
pip install -r requirements.txt
python app.py
```

App chay tai http://localhost:5000.

## Deploy Render

Repo da co san render.yaml, wsgi.py, requirements.txt.

1. Push repo len GitHub.
2. Tren Render dashboard: New + -> Blueprint -> chon repo.
3. Render tu build va deploy voi gunicorn wsgi:app.

Plan `free` da duoc set san.

## Cau truc

- app.py             - Flask routes (generate, split, refresh, account-info)
- account_info.py    - Trich Next Payment + Plan tu trang membership
- netflix.py         - Parse cookie + sinh NFToken + build login link
- config.py          - Cau hinh (port, secret, theme, ...)
- wsgi.py            - WSGI entry cho gunicorn
- requirements.txt   - Flask, requests, urllib3, gunicorn
- render.yaml        - Render blueprint
- templates/index.html - UI chinh
- static/            - CSS + JS