"""Kiểm tra dữ liệu luyen-cau/*.json đúng schema web cần. Chạy: python3 tools/validate_luyen_cau.py"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "luyen-cau"
CLUSTERS = {"con-nguoi", "nha-cua", "an-uong", "du-lich", "cong-nghe", "hoc-tap", "the-thao", "giai-tri",
            "thien-nhien", "mua-sam", "cong-dong", "trai-nghiem"}
REQ = {"bac": ["prompt_vi", "hint", "answers"], "bac5": ["question", "ideas_vi", "answers"], "y-tuong": ["question", "kind", "ideas"]}


def check(name, items):
    errs, ids = [], Counter(i.get("id") for i in items)
    errs += [f"id trùng: {k}" for k, n in ids.items() if n > 1]
    req = REQ["bac5"] if name == "bac5" else REQ["y-tuong"] if name == "y-tuong" else REQ["bac"]
    for i in items:
        where = f"{name}:{i.get('id')}"
        if i.get("cluster") not in CLUSTERS:
            errs.append(f"{where} cluster sai: {i.get('cluster')}")
        if i.get("level") not in (1, 2, 3):
            errs.append(f"{where} level sai")
        errs += [f"{where} thiếu {k}" for k in req if not i.get(k)]
        if name == "bac2" and len(i.get("given") or []) != 1:
            errs.append(f"{where} bậc 2 cần đúng 1 câu given")
        if name == "bac3" and len(i.get("given") or []) < 2:
            errs.append(f"{where} bậc 3 cần ≥ 2 câu given")
        if name == "bac5" and len(i.get("ideas_vi") or []) != 3:
            errs.append(f"{where} cần đúng 3 ideas_vi")
        if name == "y-tuong" and (i.get("kind") not in ("loi-ich", "tranh", "ke-chuyen", "clb")
                                  or any(not (x.get("vi") and x.get("en")) for x in i.get("ideas", []))):
            errs.append(f"{where} kind/ideas sai")
    return errs


def main():
    errs = []
    for name in ["bac1", "bac2", "bac3", "bac4", "bac5", "y-tuong"]:
        f = ROOT / f"{name}.json"
        if not f.exists():
            errs.append(f"thiếu {f.name}")
            continue
        items = json.loads(f.read_text(encoding="utf-8"))
        errs += check(name, items)
        print(f"{name}: {len(items)} câu · {len(Counter(i.get('cluster') for i in items))} cụm")
    print("\n".join(errs[:50]) or "OK")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
