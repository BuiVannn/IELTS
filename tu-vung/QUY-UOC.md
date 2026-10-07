# Quy ước kho paraphrase

Mỗi file `tu-vung/paraphrase/<nhom>.json` là một mảng cặp paraphrase kiểu IELTS: **cụm thường gặp trong câu hỏi** (`q`) ↔ **cách bài đọc / bài nghe nói lại ý đó** (`p`). Học viên nhìn `q`, phải nhận ra hoặc tự nói ra `p`.

```json
{"id": "env-001", "q": "reduce", "p": "cut down on", "vi": "giảm bớt", "kind": "synonym", "topic": "environment",
 "ex": "Households can cut down on energy use by insulating their lofts.", "src": ""}
```

| Trường | Quy định |
|---|---|
| `id` | `<tiền tố nhóm>-<3 chữ số>`, duy nhất toàn kho |
| `q` | 1–5 từ, dạng gọn như trong câu hỏi (động từ nguyên mẫu, danh từ số ít trừ khi bắt buộc) |
| `p` | 1–7 từ, cách diễn đạt khác hẳn `q` (không trùng gốc từ, trừ `kind` = `word-form`) |
| `vi` | nghĩa tiếng Việt ngắn gọn (≤ 8 từ) của cả hai |
| `kind` | `synonym` (đồng nghĩa), `word-form` (đổi từ loại: *increase* → *a rise in*), `structure` (đổi cấu trúc: *because of* → *owing to the fact that*), `number` (số liệu: *a third* → *33 per cent*), `opposite` (phủ định ngược: *not cheap* → *expensive*) |
| `topic` | một trong: education, technology, environment, government, urban, work, media, health, family, culture, crime, economy, daily-life, leisure, travel, general |
| `ex` | một câu học thuật 12–30 từ **chứa nguyên văn `p`** (khác hoa/thường được), như câu trong bài đọc IELTS |
| `src` | nguồn nếu lấy từ đề trên web, ví dụ `test-01#2`; ngược lại để `""` |

Chất lượng:
- Cặp phải thay thế được nhau trong cùng ngữ cảnh. Không ghép từ chỉ "gần nghĩa" mà đổi nghĩa câu.
- Ưu tiên cặp thật sự hay gặp trong IELTS Reading/Listening và dùng được trong Writing/Speaking.
- Tiếng Anh kiểu Anh. Không emoji. Không trùng cặp (`q`, `p`) với file khác.

Kiểm tra: `python3 tools/validate_para.py`
