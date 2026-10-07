"""Kiểm tra logic server: Leitner, giai đoạn từ, thu hoạch từ, ngày nghỉ phép, giờ học. Chạy: python3 tools/test_server.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server  # noqa: E402

tmp = Path(tempfile.mkdtemp())
server.VOCAB, server.STATE, server.STUDY_LOG = tmp / "vocab.json", tmp / "state.json", tmp / "study.jsonl"

c = {"box": 0, "uses": []}
for ok, box in [(True, 1), (True, 2), (False, 1), (True, 2)]:
    server.review_card(c, ok, "2026-10-05")
    assert c["box"] == box, (c, box)
assert c["due"] == "2026-10-07"
c = {"box": 3, "uses": [{"id": "a", "ok": True}, {"id": "a", "ok": True}, {"id": "b", "ok": False}]}
assert server.stage(c) == "used"
c["uses"] += [{"id": "b", "ok": True}, {"id": "c", "ok": True}]
assert server.stage(c) == "active"
server.review_card(c, True, "2026-10-05")
assert c["due"] == "2026-11-04", "từ chủ động ôn sau 30 ngày"

added = server.harvest({"vocab": [{"en": "do more harm than good", "vi": "hại nhiều hơn lợi"}, {"en": "Do more harm than good."}, {"en": ""}]}, "T2-x", "education")
assert added == 1, added
for src in ("T2-a", "T2-b", "S1-c"):
    server.harvest({"targets": [{"en": "do more harm than good", "used": True, "ok": True}]}, src, None)
card = server.vocab_list()[0]
assert card["stage"] == "active" and card["theme"] == "education", card

st = server.update_state({"freeze": {"date": "2026-11-03", "on": True}})
server.update_state({"freeze": {"date": "2026-11-10", "on": True}})
try:
    server.update_state({"freeze": {"date": "2026-11-20", "on": True}})
    raise AssertionError("phải chặn ngày nghỉ phép thứ 3 trong tháng")
except ValueError:
    pass
assert server.update_state({"check": {"date": "2026-11-03", "key": "vocab", "done": True}})["checks"]["2026-11-03"] == ["vocab"]

server.add_study("writing", 600, day="2026-11-03")
server.add_study("writing", 300, day="2026-11-03")
server.add_study("listening", 1200, True, "2026-11-03")
assert server.study_days() == {"2026-11-03": {"writing": 900, "listening": 1200}}
for bad in [("music", 60), ("writing", 0), ("writing", 99999)]:
    try:
        server.add_study(*bad)
        raise AssertionError(bad)
    except ValueError:
        pass
assert server.clean_errors({"article": "2", "tense": -1, "x": 5})["article"] == 2
st = server.update_state({"lesson": {"id": "w2-opinion", "quiz": "3/4"}})
assert st["lessons"]["w2-opinion"]["quiz"] == "3/4"
assert "w2-opinion" not in server.update_state({"lesson": {"id": "w2-opinion", "done": False}})["lessons"]
try:
    server.update_state({"lesson": {"id": "../../server"}})
    raise AssertionError("phải chặn id bài học lạ")
except ValueError:
    pass
import base64
server.PASS_FILE = tmp / ".matkhau"
basic = lambda pw: {"Cf-Connecting-IP": "1.2.3.4", "Authorization": "Basic " + base64.b64encode(f"u:{pw}".encode()).decode()}
assert server.authorized({})  # localhost
assert not server.authorized(basic("x"))  # tunnel mà chưa đặt mật khẩu → chặn
server.PASS_FILE.write_text("bi-mat\n")
assert server.authorized(basic("bi-mat")) and not server.authorized(basic("sai"))
assert not server.authorized({"Cf-Connecting-IP": "1.2.3.4"})
c = server.review_card({"box": 2, "due": "2026-11-01", "reviews": 3, "lapses": 0}, False, "2026-11-05")
assert c["box"] == 1 and c["lapses"] == 1
c.update(c.pop("prev")); server.review_card(c, True, "2026-11-05")  # hoàn tác lần sai rồi chấm đúng
assert c["box"] == 3 and c["lapses"] == 0 and c["reviews"] == 4
server.PARA_STATE = tmp / "para.json"
server.para_pairs = lambda: [{"id": "gen-001", "q": "show", "p": "demonstrate"}]
assert server.para_list()[0]["box"] == 0
server.para_review({"id": "gen-001", "ok": True}); server.para_review({"id": "gen-001", "ok": False})
c = server.para_review({"id": "gen-001", "ok": True, "undo": True})["card"]
assert c["box"] == 2 and c["lapses"] == 0, c  # sai rồi bấm "Tôi đúng" = như chưa từng sai
try:
    server.para_review({"id": "../x", "ok": True})
    raise AssertionError("phải chặn id lạ")
except ValueError:
    pass
print("server OK")
