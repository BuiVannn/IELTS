# Quy ước file bài học (web đọc trực tiếp, `tools/validate_hoc.py` kiểm tra)

## Bài học kỹ năng: `hoc/bai/<id>.md`

```yaml
---
id: w2-opinion              # = tên file; tiền tố: w1- w2- sp- rd- ls- nt-
skill: writing              # writing | speaking | reading | listening | nen-tang
group: Task 2                # nhóm hiển thị: Task 1 | Task 2 | Speaking | Reading | Listening | Nền tảng
order: 2                     # thứ tự trong nhóm
title: Opinion – Agree or disagree
minutes: 15
crit: TR,CC                  # tiêu chí liên quan (TA TR CC LR GRA FC P), ngăn bằng dấu phẩy, không khoảng trắng
errors: article,plural       # (tuỳ chọn) nhãn lỗi liên quan: article plural tense agreement word_form collocation spelling punctuation repetition sentence
qtype: opinion               # (tuỳ chọn) dạng đề để nối "Luyện đề dạng này": opinion discussion two-part problem-solution adv-dis bar line pie table mixed process map
part: 2                      # (tuỳ chọn) đi kèm qtype hoặc speaking: writing 1/2, speaking 1/2
summary: Một câu nói bài này giúp gì.
---
```

Thân bài, đúng 5 mục `##` theo thứ tự:

1. `## Cần nhớ`: 5–8 gạch đầu dòng, tiếng Việt, cụ thể, có thể kèm ví dụ tiếng Anh ngắn. Được dùng `###`, bảng.
2. `## Ví dụ chuẩn`: ví dụ band 7–8 TỰ VIẾT (không chép sách/website), có phân tích ngắn vì sao tốt. In đậm cụm đáng học.
3. `## Lỗi hay gặp`: 4–8 dòng, mỗi dòng ĐÚNG một dòng dạng
   `- ❌ câu sai → ✅ câu đúng — giải thích ngắn`
   (không in nghiêng, không backtick, không xuống dòng giữa chừng; câu sai/đúng chỉ khác ở phần cần sửa, web tự tô đỏ/xanh).
4. `## Cụm nên học`: 6–12 dòng, mỗi dòng ĐÚNG dạng
   `- **cụm tiếng Anh** — nghĩa tiếng Việt — Câu ví dụ tiếng Anh chứa nguyên cụm.`
   (dấu — là em dash có khoảng trắng hai bên; web có nút đưa cụm vào kho Từ chủ động.)
5. `## Kiểm tra nhanh`: 3–5 câu trắc nghiệm, mỗi câu:
   ```
   1. Câu hỏi?
      - [ ] Phương án sai
      - [x] Phương án đúng (đúng MỘT phương án [x])
      - [ ] Phương án sai
      > Giải thích vì sao.
   ```

## Trang chủ đề: `hoc/chu-de/<theme>.md`

```yaml
---
id: education                # = theme trong CLUSTERS của web
kind: topic
title: Giáo dục
summary: ...
---
```

Đúng 4 mục `##`:
1. `## Cụm từ`: 15–20 dòng đúng dạng cụm như trên (dùng được cho cả Writing và Speaking, ưu tiên collocation band 7).
2. `## Kho ý tưởng Task 2`: 4–6 `###` tiểu chủ đề (lấy từ đề recall 2026), mỗi cái có ý ủng hộ / phản đối (mỗi ý: luận điểm → giải thích → ví dụ cụ thể, tiếng Anh ngắn gọn).
3. `## Speaking dự đoán`: 4–6 câu hỏi Part 1/Part 3 thuộc chủ đề (từ forecast Q3/2026), mỗi câu kèm câu trả lời mẫu band 7 tự nhiên 3–5 câu, in đậm cụm hay.
4. `## Từ vựng Reading & Listening`: bảng | Từ | Nghĩa | Ghi chú (chính tả hay sai, từ đồng nghĩa hay paraphrase) | 12–20 dòng.

## Chung
- Viết tiếng Việt có dấu, giọng thẳng, ngắn; ví dụ tiếng Anh British English.
- Không emoji (trừ ❌ ✅ trong mục Lỗi hay gặp). Không chép nguyên văn sách Cambridge hay website: tự viết ví dụ.
- Kiểm tra: `python3 tools/validate_hoc.py`.
