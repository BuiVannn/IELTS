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
print("server OK")
