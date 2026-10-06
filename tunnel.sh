#!/bin/sh
# Mở web ra Internet qua Cloudflare Tunnel (cần server.py đang chạy). Link đổi mỗi lần chạy.
cd "$(dirname "$0")"
[ -s .matkhau ] || { echo "Chưa có mật khẩu: echo 'mat-khau-cua-ban' > .matkhau"; exit 1; }
echo "Đang mở tunnel… (Ctrl+C để tắt)"
cloudflared tunnel --url http://localhost:8766 2>&1 | awk 'match($0, /https:\/\/[a-z0-9-]+\.trycloudflare\.com/) { print substr($0, RSTART, RLENGTH) "/web/   ← mở link này, nhập mật khẩu (tên đăng nhập gõ gì cũng được)"; fflush() }'
