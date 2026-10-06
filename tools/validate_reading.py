"""Kiểm tra đề Reading theo reading/QUY-UOC.md. Chạy: python3 tools/validate_reading.py [file...]  (mặc định: mọi reading/de/*.json)"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPES = {"tfng", "ynng", "headings", "match-info", "match-features", "endings", "mcq", "mcq2", "sentence", "summary", "short"}
FIXED = {"tfng": {"TRUE", "FALSE", "NOT GIVEN"}, "ynng": {"YES", "NO", "NOT GIVEN"}}
RANGES = [(1, 13), (14, 26), (27, 40)]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
LIMIT_WORDS = {"ONE WORD ONLY": 1, "ONE WORD AND/OR A NUMBER": 1, "NO MORE THAN TWO WORDS": 2, "NO MORE THAN TWO WORDS AND/OR A NUMBER": 2,
               "NO MORE THAN THREE WORDS": 3, "NO MORE THAN THREE WORDS AND/OR A NUMBER": 3}
norm = lambda s: re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip().lower()


def nums(q):
    return q["n"] if isinstance(q["n"], list) else [q["n"]]


def check(path):
    errs = []
    t = json.loads(Path(path).read_text())
    if EMOJI.search(json.dumps(t, ensure_ascii=False)):
        errs.append("có emoji")
    ans, exp = t.get("answers", {}), t.get("explain", {})
    seen = []
    if len(t.get("passages", [])) != 3:
        return [f"cần 3 passage, có {len(t.get('passages', []))}"]
    kinds = set()
    for pi, p in enumerate(t["passages"]):
        text = "\n".join(x["text"] for x in p["paragraphs"])
        ntext = norm(text)
        wc = len(text.split())
        if not 750 <= wc <= 1000:
            errs.append(f"P{pi + 1}: {wc} từ (cần 750–1000)")
        labels = [x.get("label", "") for x in p["paragraphs"]]
        lo, hi = RANGES[pi]
        pnums = []
        for g in p["groups"]:
            ty = g.get("type")
            kinds.add(ty)
            if ty not in TYPES:
                errs.append(f"P{pi + 1}: type lạ {ty}")
                continue
            if not g.get("instructions"):
                errs.append(f"P{pi + 1} {ty}: thiếu instructions")
            gn = [n for q in g["questions"] for n in nums(q)]
            pnums += gn
            okeys = {o["key"] for o in g.get("options", [])}
            limit = LIMIT_WORDS.get(g.get("limit", ""))
            if ty in ("sentence", "short") or (ty == "summary" and not okeys):
                if not limit:
                    errs.append(f"P{pi + 1} {ty} {gn[0]}: limit lạ {g.get('limit')!r}")
            if ty in ("headings", "endings") and len(okeys) < len(gn) + 2:
                errs.append(f"P{pi + 1} {ty}: cần ≥ {len(gn) + 2} lựa chọn, có {len(okeys)}")
            if ty == "headings":
                used = [ans.get(str(n)) for n in gn]
                if len(set(used)) != len(used):
                    errs.append(f"P{pi + 1} headings: một heading dùng 2 lần")
                for q in g["questions"]:
                    lab = q["text"].replace("Paragraph", "").strip()
                    if lab not in labels:
                        errs.append(f"câu {q['n']}: không có đoạn {lab}")
            if ty == "match-info" and not okeys <= set(labels):
                errs.append(f"P{pi + 1} match-info: options không khớp nhãn đoạn")
            if ty in FIXED:
                vals = {ans.get(str(n)) for n in gn}
                if len(gn) >= 4 and vals != FIXED[ty]:
                    errs.append(f"P{pi + 1} {ty} {gn[0]}–{gn[-1]}: nên có đủ 3 loại đáp án, có {sorted(v for v in vals if v)}")
            if ty == "summary":
                body = g.get("text", "") or json.dumps(g.get("table", []), ensure_ascii=False)
                gaps = [int(x) for x in re.findall(r"\{(\d+)\}", body)]
                if sorted(gaps) != sorted(gn):
                    errs.append(f"P{pi + 1} summary: chỗ trống {gaps} ≠ câu {gn}")
            if ty == "sentence":
                for q in g["questions"]:
                    if q["text"].count("___") != 1:
                        errs.append(f"câu {q['n']}: cần đúng một ___")
            if ty == "mcq2":
                for q in g["questions"]:
                    pair = [ans.get(str(n)) for n in nums(q)]
                    if len(nums(q)) != 2 or len(set(pair)) != 2:
                        errs.append(f"câu {q['n']}: mcq2 cần 2 câu, 2 đáp án khác nhau")
            for q in g["questions"]:
                qo = {o["key"] for o in q.get("options", [])}
                if ty in ("mcq", "mcq2") and len(qo) < (5 if ty == "mcq2" else 4):
                    errs.append(f"câu {q['n']}: thiếu lựa chọn")
                for n in nums(q):
                    a = ans.get(str(n))
                    if not a:
                        errs.append(f"câu {n}: thiếu đáp án")
                        continue
                    if ty in FIXED and a not in FIXED[ty]:
                        errs.append(f"câu {n}: đáp án {a!r} không hợp lệ cho {ty}")
                    if (okeys or qo) and a not in (okeys | qo):
                        errs.append(f"câu {n}: đáp án {a!r} không có trong lựa chọn")
                    if limit and not (okeys or qo):
                        for alt in a.split("/"):
                            if len(re.findall(r"[A-Za-z']+", alt)) > limit:
                                errs.append(f"câu {n}: {alt!r} vượt giới hạn {limit} từ")
                        if norm(a.split("/")[0]) not in ntext:
                            errs.append(f"câu {n}: đáp án {a.split('/')[0]!r} không có nguyên văn trong bài")
                    e = exp.get(str(n))
                    if not e or not e.get("why") or not e.get("quote"):
                        errs.append(f"câu {n}: thiếu explain why/quote")
                    elif norm(e["quote"]) not in ntext:
                        errs.append(f"câu {n}: quote không có nguyên văn trong P{pi + 1}: {e['quote'][:60]!r}")
        if sorted(pnums) != list(range(lo, hi + 1)):
            errs.append(f"P{pi + 1}: số câu {sorted(pnums)[:3]}… ≠ {lo}–{hi}")
        seen += pnums
    if len(kinds) < 6:
        errs.append(f"cả đề mới có {len(kinds)} dạng: {sorted(kinds)} (cần ≥ 6)")
    extra = set(ans) - {str(n) for n in seen}
    if extra:
        errs.append(f"đáp án thừa: {sorted(extra)}")
    return errs


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(str(p) for p in (ROOT / "reading/de").glob("*.json"))
    bad = 0
    for f in files:
        try:
            errs = check(f)
        except Exception as e:  # JSON hỏng / thiếu trường bắt buộc
            errs = [f"lỗi cấu trúc: {e!r}"]
        bad += bool(errs)
        print(f"{'OK ' if not errs else 'LỖI'} {f}" + "".join(f"\n    - {e}" for e in errs))
    print(f"{len(files) - bad}/{len(files)} file đạt")
    sys.exit(1 if bad else 0)
