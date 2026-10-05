# Luyện câu — dữ liệu bài tập

Mỗi file là 1 mảng JSON. Web đọc trực tiếp. Kiểm tra: `python3 tools/validate_luyen_cau.py`.

Cụm chủ đề (`cluster`): con-nguoi, nha-cua, an-uong, du-lich, cong-nghe, hoc-tap, the-thao, giai-tri, thien-nhien, mua-sam, cong-dong, trai-nghiem.
`level`: 1 dễ · 2 vừa · 3 khó (trong cùng một bậc).

## bac1.json … bac4.json
```json
{"id": "b1-an-uong-001", "cluster": "an-uong", "level": 1,
 "prompt_vi": "Tôi thích nấu ăn.",          // đề bài tiếng Việt
 "given": [],                               // câu tiếng Anh cho sẵn (bậc 2: câu lõi; bậc 3: 2–3 câu đơn)
 "hint": "be keen on + V-ing",              // khung/cụm gợi ý (bậc 3: từ nối bắt buộc)
 "answers": ["I'm keen on cooking."],       // 1–3 đáp án mẫu đúng
 "note": "keen on + V-ing, không dùng to V", // giải thích ngắn tiếng Việt
 "source": ""}                              // id đề gốc nếu lấy từ kho (bậc 4)
```
## bac5.json (ghép đoạn)
```json
{"id": "b5-an-uong-001", "cluster": "an-uong", "level": 2, "part": "W3",
 "question": "When you are busy, what do you usually eat?", "source": "W-food-club-v1",
 "ideas_vi": ["mì/đồ nhanh", "tiện, rẻ", "cuối tuần tự nấu"],
 "answers": ["<đoạn 35–45 từ>"], "note": "..."}
```
## y-tuong.json (tìm ý 60 giây)
```json
{"id": "y-an-uong-001", "cluster": "an-uong", "kind": "loi-ich", "part": "S4",
 "question": "...", "source": "S4-restaurant-meal",
 "ideas": [{"vi": "sức khỏe: ăn nhà sạch hơn", "en": "home-cooked food is healthier"}],
 "note": "..."}
```
`kind`: loi-ich (ý kiến/lợi ích) · tranh (tả/so sánh tranh) · ke-chuyen (kể trải nghiệm) · clb (email góp ý CLB).
