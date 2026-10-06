# Luyện IELTS Academic — mục tiêu 7.0+

```bash
cd ~/Documents/hochochoc/English/on_ielts && python3 server.py   # http://localhost:8766
```

Dùng Chrome/Edge (ghi âm + chuyển giọng nói thành chữ). Muốn có icon riêng trên thanh taskbar/Dock: Chrome → menu ⋮ → Truyền, lưu và chia sẻ → Cài đặt trang dưới dạng ứng dụng. Phím `[` thu gọn / mở rộng thanh bên. Nút **Nộp & chấm** gọi `claude -p` trên máy với rubric ở `cham-diem/`. Kho Aptis cũ vẫn chạy song song ở `../on_aptis` (cổng 8765).

## Có gì

| Màn | Nội dung |
|---|---|
| Học | 51 bài học 10–15 phút theo kỹ năng (Nền tảng, Task 1, Task 2, Speaking, Reading, Listening) và 15 trang theo chủ đề; mỗi bài: cần nhớ, ví dụ chuẩn, lỗi hay gặp, cụm nên học (thêm vào kho Từ chủ động), kiểm tra nhanh. Gợi ý bài theo tiêu chí và lỗi yếu nhất |
| Writing | Task 1 (biểu đồ vẽ từ khối ```chart) và Task 2; đồng hồ 20/40 phút; đếm từ theo mốc 150/250; chấm 4 tiêu chí |
| Speaking | Part 1; Part 2 cue card (1 phút chuẩn bị, 2 phút nói) + Part 3; chấm FC/LR/GRA/P (P là ước lượng) |
| Reading | Đề làm trực tiếp như thi trên máy (`reading/de/*.json`, 3 passage · 40 câu · 60 phút, hoặc 1 passage 20 phút): bài đọc trái, câu hỏi phải, kéo đổi độ rộng, tô sáng, đồng hồ, thanh số câu. Nộp → band, thống kê theo dạng câu, giải thích từng câu và tô chỗ có đáp án trong bài. Vẫn nhập được đáp án đề sách giấy. (Listening tự ôn ngoài web.) |
| Thi thử | Speaking Part 1 → 2 → 3, khoảng 13 phút, bốc đề ngẫu nhiên |
| Tổng quan | Đọc mỗi ngày (1 quote hoặc truyện ngắn, xoay vòng 120 bài trong `hoc/doc-moi-ngay.json`), Chuỗi ngày học, phút học hôm nay/tuần, hạn mức 3 việc mỗi ngày (tự đánh dấu khi làm xong), ghi tay phút Listening, 2 ngày nghỉ phép/tháng, tiêu chí yếu nhất, bảng band theo tiêu chí |
| Từ chủ động | Kho cụm tự thu từ mỗi lần chấm; ôn giãn cách 1→2→4→8→16 ngày với 4 kiểu bài (gợi nhớ ngược, điền câu, tự đặt câu, nói); “từ đích” hiện khi làm bài, máy chấm kiểm tra đã dùng đúng chưa; dùng đúng ở 3 bài khác nhau = chủ động |
| Tiến độ | Lịch tháng, lưới chặng tới ngày thi, cài đặt mục tiêu; biểu đồ giờ học/tuần, band theo thời gian, tiêu chí Writing, Reading theo dạng câu, lỗi lặp lại, phễu từ chủ động |

**Giờ học** được tự đếm khi đang mở một bài (đề, Reading có bấm giờ, ôn từ, thi thử) và tab đang hiện, có thao tác trong 2 phút gần nhất hoặc đồng hồ đang chạy.

**Band:** mỗi tiêu chí là band nguyên; band task/kỹ năng = trung bình, làm tròn xuống nửa band (server tự tính, không tin số học của model). Writing tổng = (T1 + 2·T2)/3. Máy chấm có sai số, xem `tools/calibrate.py`.

## Cấu trúc

```
on_ielts/
├── server.py                 ← API + chấm bằng claude -p
├── web/index.html            ← toàn bộ giao diện (vanilla JS)
├── cham-diem/                ← rubric-writing.md, rubric-speaking.md, rubric-tu.md (chấm nhanh câu tự đặt, model haiku)
├── writing/task1/T1-*.md     ← đề Task 1
├── writing/task2/T2-*.md     ← đề Task 2
├── speaking/part1/S1-*.md    ← 1 chủ đề Part 1 (nhiều câu)
├── speaking/part2/S2-*.md    ← 1 cue card + câu hỏi Part 3
├── research/                 ← format & band, xu hướng đề 2026
├── hoc/bai/*.md              ← bài học kỹ năng (quy ước: hoc/QUY-UOC.md, kiểm tra: tools/validate_hoc.py)
├── hoc/chu-de/*.md           ← trang học theo chủ đề
├── hoc/doc-moi-ngay.json     ← 80 quote + 40 truyện ngắn cho mục Đọc mỗi ngày
├── hoc/tu-aptis/             ← tài liệu dùng lại từ đợt Aptis
├── attempts/                 ← bài đã chấm (mỗi lần một file .md, kèm nhãn lỗi)
│   ├── _log/study.jsonl      ← giờ học theo ngày · _log/state.json: cài đặt, check-in, ngày nghỉ phép
│   ├── _vocab/vocab.json     ← kho từ chủ động
│   └── _rl/log.jsonl         ← kết quả Reading
├── calibration/              ← bài mẫu có band chính thức để hiệu chỉnh (không đưa vào git)
└── tools/                    ← build_index.py, calibrate.py, test_scoring.mjs, test_server.py
```

## Quy ước file đề

Frontmatter (mọi đề):

```yaml
id: T2-compulsory-art      # = tên file
skill: writing             # writing | speaking
part: 2                    # writing: 1 = Task 1, 2 = Task 2 · speaking: 1 = Part 1, 2 = Part 2+3
title: ...
qtype: opinion             # T2: opinion|discussion|two-part|problem-solution|adv-dis
                           # T1: bar|line|pie|table|mixed|process|map · S2: person|place|object|event|experience
theme: education           # education|work|technology|media|environment|health|urban|family|culture|government|crime|economy|daily-life|leisure|travel
hot: true                  # trọng điểm (forecast / recall gần đây)
source: ...
status: todo               # todo | doing | done (web tự cập nhật)
attempts: 0
best_score:
```

Thân bài:
- **Writing:** `## Đề` (đề trong `>` blockquote; Task 1 thêm khối ```chart JSON `{"type","title","unit","labels","datasets":[{"label","data"}]}` hoặc bảng markdown) → tuỳ chọn `## Bài mẫu`.
- **Speaking Part 1:** `## Câu hỏi` với các dòng `**Q1.** …` → tuỳ chọn `## Bài mẫu`.
- **Speaking Part 2:** `## Cue card` (blockquote, dòng đầu in đậm là đề) → `## Part 3` với `**Q1.** …` → tuỳ chọn `## Bài mẫu`.

Sau khi thêm/sửa đề: `python3 tools/build_index.py`.

## Kiểm tra

```bash
python3 tools/validate_reading.py  # cấu trúc đề Reading, đáp án có nguyên văn trong bài (quy ước: reading/QUY-UOC.md)
node tools/test_scoring.mjs        # chấm Reading, làm tròn band, chuỗi ngày, tô câu sửa, nhận cụm đích
python3 tools/validate_hoc.py       # định dạng bài học
python3 tools/test_server.py       # ôn giãn cách, giai đoạn từ, thu hoạch từ, ngày nghỉ phép, giờ học
python3 tools/calibrate.py         # so máy chấm Writing với band giám khảo trên bài mẫu chính thức
```

## Mở từ điện thoại / máy khác (Cloudflare Tunnel)

Cần Mac bật và `python3 server.py` đang chạy.

1. Đặt mật khẩu một lần: `echo 'mat-khau-cua-ban' > .matkhau` (file này không lên git).
2. Chạy `./tunnel.sh` → in ra link `https://….trycloudflare.com/web/`. Link đổi mỗi lần chạy; Ctrl+C để tắt.
3. Mở link, nhập mật khẩu (tên đăng nhập gõ gì cũng được). Truy cập qua tunnel mà chưa có `.matkhau` sẽ bị chặn hết; `localhost` vẫn vào thẳng.
