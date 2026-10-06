# Quy ước đề Reading (làm trực tiếp trên web)

Mỗi đề = 1 file `reading/de/test-NN.json`, đúng cấu trúc IELTS Academic Reading trên máy tính:
3 passage, 40 câu, 60 phút. Passage 1 = câu 1–13, Passage 2 = câu 14–26, Passage 3 = câu 27–40.
Độ khó tăng dần: P1 dễ nhất (band 5.5–6), P3 khó nhất (band 7.5–8, lập luận học thuật, có Yes/No/Not Given).

Bài đọc là **bài viết mới, nguyên bản** theo phong cách bài IELTS (tạp chí khoa học phổ thông như New Scientist, The Economist, sách chuyên khảo). Không chép bài từ sách Cambridge hay web luyện thi.

## Cấu trúc JSON

```json
{
  "id": "test-01",
  "title": "Reading Test 1",
  "passages": [
    {
      "title": "The history of glass",
      "intro": "",
      "paragraphs": [{"label": "A", "text": "..."}, {"label": "B", "text": "..."}],
      "groups": [ ... ]
    }
  ],
  "answers": {"1": "TRUE", "7": "canal/canals"},
  "explain": {"1": {"quote": "câu nguyên văn trong bài làm bằng chứng", "why": "giải thích tiếng Việt ≤ 40 từ: paraphrase nào khớp, vì sao"}}
}
```

- `label` của đoạn: `"A"`, `"B"`… khi passage có câu hỏi theo đoạn (headings, matching information); ngược lại để `""`.
- `answers`: nhiều cách viết chấp nhận được ngăn bằng `/` (`"19th century/nineteenth century"`). Chữ hoa/thường không quan trọng.
- `explain[n].quote`: **chuỗi con nguyên văn** trong một đoạn của passage (web dùng nó để tô vàng chỗ có đáp án). Câu NOT GIVEN: quote là câu gần nhất bàn về ý đó, `why` nói rõ bài không nhắc tới điều gì.

## Các loại nhóm câu (`groups[].type`)

Mỗi nhóm: `{"type", "instructions", "questions": [...]}` + trường riêng. `instructions` viết y hệt đề thật (tiếng Anh), ví dụ "Do the following statements agree with the information given in Reading Passage 1?". Dòng "Questions 1–6" web tự tạo, không viết vào.

| type | Dạng | Trường riêng | Câu hỏi | Đáp án |
|---|---|---|---|---|
| `tfng` | True/False/Not Given | — | `{"n":1,"text":"statement"}` | `TRUE` / `FALSE` / `NOT GIVEN` |
| `ynng` | Yes/No/Not Given | — | như trên | `YES` / `NO` / `NOT GIVEN` |
| `headings` | Matching headings | `options:[{"key":"i","text":"..."}]` (nhiều hơn số đoạn ≥ 2) | `{"n":14,"text":"Paragraph A"}` | `"iv"` — mỗi heading dùng tối đa 1 lần |
| `match-info` | Matching information | `options` = các chữ đoạn `[{"key":"A","text":""}]`, `note` "You may use any letter more than once." | `{"n":20,"text":"a reference to ..."}` | `"C"` |
| `match-features` | Matching features | `options:[{"key":"A","text":"Dr Jane Smith"}]` | `{"n":..,"text":"statement"}` | `"B"` |
| `endings` | Matching sentence endings | `options:[{"key":"A","text":"ending ..."}]` (nhiều hơn số câu ≥ 2) | `{"n":..,"text":"sentence start"}` | `"E"` |
| `mcq` | Multiple choice 1 đáp án | — | `{"n":..,"text":"...","options":[{"key":"A","text":".."}, ×4]}` | `"C"` |
| `mcq2` | Choose TWO letters | — | `{"n":[21,22],"text":"Which TWO ...?","options":[A–E]}` | `"21":"B","22":"D"` (thứ tự nào cũng được) |
| `sentence` | Sentence completion | `limit` | `{"n":..,"text":"Câu có ___ đúng một chỗ trống."}` | từ lấy nguyên văn trong bài |
| `summary` | Summary / note / table / flow-chart completion | `limit` hoặc `options` (word box A–H), `title`, và **một trong hai**: `text` (dòng ngăn `\n`, chỗ trống ghi `{14}`; dòng bắt đầu `## ` là tiêu đề, `- ` là gạch đầu dòng) hoặc `table` (mảng hàng, mỗi ô là chuỗi, chỗ trống `{14}`, hàng đầu là tiêu đề cột) | `{"n":14}` (không cần text) | từ trong bài, hoặc chữ cái nếu có word box |
| `short` | Short answer | `limit` | `{"n":..,"text":"Question?"}` | từ trong bài |

`limit` viết y đề thật: `"ONE WORD ONLY"`, `"NO MORE THAN TWO WORDS"`, `"NO MORE THAN TWO WORDS AND/OR A NUMBER"`, `"NO MORE THAN THREE WORDS"`.

## Chuẩn chất lượng

- Mỗi passage 800–950 từ (tối đa 1000), giọng học thuật, có số liệu, tên nhà nghiên cứu (hư cấu nhưng hợp lý), quan điểm trái chiều ở P3.
- Mỗi passage 2–3 nhóm câu khác dạng. Cả đề có ít nhất 6 dạng khác nhau, luôn có `tfng` hoặc `ynng`, có ít nhất một dạng matching và một dạng completion.
- Câu hỏi paraphrase bài đọc, không lặp nguyên văn. Đáp án completion lấy **nguyên văn** từ bài, đúng giới hạn từ, đúng ngữ pháp khi điền vào.
- Câu hỏi theo thứ tự xuất hiện trong bài (trừ headings, matching information, matching features, summary có word box: theo quy tắc đề thật).
- FALSE = bài nói ngược lại rõ ràng; NOT GIVEN = bài không nói. Mỗi nhóm TFNG/YNNG có đủ cả 3 loại đáp án.
- Không câu nào có hai đáp án đúng. Bẫy phải hợp lý (từ khoá xuất hiện nhưng nghĩa khác), không đánh đố vô lý.
- Không emoji. Tiếng Anh kiểu Anh (colour, organisation).

Kiểm tra: `python3 tools/validate_reading.py reading/de/test-01.json`
