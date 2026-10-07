"""Kiểm tra kho paraphrase theo tu-vung/QUY-UOC.md. Chạy: python3 tools/validate_para.py [file...]"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = {"synonym", "word-form", "structure", "number", "opposite"}
TOPICS = {"education", "technology", "environment", "government", "urban", "work", "media", "health", "family", "culture",
          "crime", "economy", "daily-life", "leisure", "travel", "general"}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'")).strip().lower()


def check(files):
    errs, ids, pairs = [], {}, {}
    for f in files:
        try:
            items = json.loads(Path(f).read_text())
        except Exception as e:  # JSON hỏng
            errs.append(f"{f}: JSON lỗi {e}")
            continue
        for i, x in enumerate(items):
            w = f"{Path(f).name}#{x.get('id', i)}"
            for k in ("id", "q", "p", "vi", "kind", "topic", "ex"):
                if not str(x.get(k, "")).strip():
                    errs.append(f"{w}: thiếu {k}")
            if errs and errs[-1].startswith(w):
                continue
            if x["id"] in ids:
                errs.append(f"{w}: trùng id với {ids[x['id']]}")
            ids[x["id"]] = f
            key = (norm(x["q"]), norm(x["p"]))
            if key in pairs:
                errs.append(f"{w}: trùng cặp với {pairs[key]}")
            pairs[key] = w
            if not re.fullmatch(r"[a-z]+-\d{3}", x["id"]):
                errs.append(f"{w}: id sai dạng")
            if x["kind"] not in KINDS:
                errs.append(f"{w}: kind lạ {x['kind']}")
            if x["topic"] not in TOPICS:
                errs.append(f"{w}: topic lạ {x['topic']}")
            if not 1 <= len(x["q"].split()) <= 5 or not 1 <= len(x["p"].split()) <= 7:
                errs.append(f"{w}: q/p quá dài")
            if norm(x["q"]) == norm(x["p"]):
                errs.append(f"{w}: q trùng p")
            if norm(x["p"]) not in norm(x["ex"]):
                errs.append(f"{w}: ex không chứa nguyên văn p {x['p']!r}")
            if not 10 <= len(x["ex"].split()) <= 35:
                errs.append(f"{w}: ex {len(x['ex'].split())} từ")
            if EMOJI.search(json.dumps(x, ensure_ascii=False)):
                errs.append(f"{w}: có emoji")
    return errs, len(pairs)


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(str(p) for p in (ROOT / "tu-vung/paraphrase").glob("*.json"))
    errs, n = check(files)
    print("\n".join(errs) or "OK", f"\n{n} cặp, {len(files)} file, {len(errs)} lỗi")
    sys.exit(1 if errs else 0)
