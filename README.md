# Luyện IELTS Academic — mục tiêu 7.0+

```bash
cd ~/Documents/hochochoc/English/on_ielts && python3 server.py   # http://localhost:8766
```

Dùng Chrome/Edge (ghi âm + chuyển giọng nói thành chữ). Nút **Nộp & chấm** gọi `claude -p` trên máy với rubric ở `cham-diem/`. Kho Aptis cũ vẫn chạy song song ở `../on_aptis` (cổng 8765).

## Có gì

| Màn | Nội dung |
|---|---|
| Writing | Task 1 (biểu đồ vẽ từ khối ```chart) và Task 2; đồng hồ 20/40 phút; đếm từ theo mốc 150/250; chấm 4 tiêu chí |
| Speaking | Part 1; Part 2 cue card (1 phút chuẩn bị, 2 phút nói) + Part 3; chấm FC/LR/GRA/P (P là ước lượng) |
| Reading | Nhập đáp án đề Cambridge của bạn → tự chấm, quy ra band, thống kê theo dạng câu. (Listening tự ôn ngoài web.) |
| Thi thử | Speaking Part 1 → 2 → 3, khoảng 13 phút, bốc đề ngẫu nhiên |

**Band:** mỗi tiêu chí là band nguyên; band task/kỹ năng = trung bình, làm tròn xuống nửa band (server tự tính, không tin số học của model). Writing tổng = (T1 + 2·T2)/3. Máy chấm có sai số, xem `tools/calibrate.py`.

## Cấu trúc

```
on_ielts/
├── server.py                 ← API + chấm bằng claude -p
├── web/index.html            ← toàn bộ giao diện (vanilla JS)
├── cham-diem/                ← rubric-writing.md, rubric-speaking.md
├── writing/task1/T1-*.md     ← đề Task 1
├── writing/task2/T2-*.md     ← đề Task 2
├── speaking/part1/S1-*.md    ← 1 chủ đề Part 1 (nhiều câu)
├── speaking/part2/S2-*.md    ← 1 cue card + câu hỏi Part 3
├── research/                 ← format & band, xu hướng đề 2026
├── hoc/tu-aptis/             ← tài liệu dùng lại từ đợt Aptis
├── attempts/                 ← bài đã chấm (mỗi lần một file .md)
├── calibration/              ← bài mẫu có band chính thức để hiệu chỉnh (không đưa vào git)
└── tools/                    ← build_index.py, calibrate.py, test_scoring.mjs
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
node tools/test_scoring.mjs        # logic chấm Reading + làm tròn band
python3 tools/calibrate.py         # so máy chấm Writing với band giám khảo trên bài mẫu chính thức
```
