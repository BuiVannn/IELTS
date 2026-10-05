"""Kiểm tra định dạng bài học trong hoc/bai và hoc/chu-de theo hoc/QUY-UOC.md. Chạy: python3 tools/validate_hoc.py [file...]"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from build_index import frontmatter  # noqa: E402

LESSON_SECS = ["Cần nhớ", "Ví dụ chuẩn", "Lỗi hay gặp", "Cụm nên học", "Kiểm tra nhanh"]
TOPIC_SECS = ["Cụm từ", "Kho ý tưởng Task 2", "Speaking dự đoán", "Từ vựng Reading & Listening"]
SKILLS = {"writing", "speaking", "reading", "listening", "nen-tang"}
CRITS = {"TA", "TR", "CC", "LR", "GRA", "FC", "P"}
ERRS = {"article", "plural", "tense", "agreement", "word_form", "collocation", "spelling", "punctuation", "repetition", "sentence"}
THEMES = {"education", "work", "technology", "media", "environment", "health", "urban", "family", "culture", "government", "crime", "economy", "daily-life", "leisure", "travel"}
PHRASE = re.compile(r"^- \*\*([^*]+)\*\* — ([^—]+) — (.+)$")
FIX = re.compile(r"^- ❌ ([^`*\n]+?) → ✅ ([^`*\n]+?) — (.+)$")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


def sections(body):
    parts = re.split(r"^## (.+)$", body, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def check_phrases(text, lo, hi, errs):
    lines = [l for l in text.splitlines() if l.startswith("- ")]
    bad = [l for l in lines if not PHRASE.match(l)]
    errs += [f"dòng cụm sai dạng: {l[:70]}" for l in bad]
    for l in lines:
        m = PHRASE.match(l)
        if m and m.group(1).strip().lower().split()[0] not in m.group(3).lower():
            errs.append(f"câu ví dụ không chứa cụm: {m.group(1)}")
    if not lo <= len(lines) <= hi:
        errs.append(f"số cụm {len(lines)} ngoài khoảng {lo}–{hi}")


def check_quiz(text, errs):
    qs = re.split(r"^\d+\.\s", text.strip(), flags=re.M)[1:]
    if not 3 <= len(qs) <= 5:
        errs.append(f"Kiểm tra nhanh có {len(qs)} câu (cần 3–5)")
    for i, q in enumerate(qs, 1):
        opts = re.findall(r"^\s+- \[( |x)\] .+$", q, re.M)
        if len(opts) < 2 or opts.count("x") != 1:
            errs.append(f"câu {i}: cần ≥2 phương án và đúng 1 [x] (có {len(opts)}, {opts.count('x')} đúng)")
        if not re.search(r"^\s+> .+", q, re.M):
            errs.append(f"câu {i}: thiếu dòng giải thích '> '")


def validate(p):
    errs, text = [], p.read_text(encoding="utf-8")
    m = frontmatter(p) or {}
    body = text.split("---", 2)[2] if text.startswith("---") else ""
    if m.get("id") != p.stem:
        errs.append("id phải trùng tên file")
    if EMOJI.search(body.replace("❌", "").replace("✅", "")):
        errs.append("có emoji")
    secs = sections(body)
    names = [s for s, _ in secs]
    if p.parent.name == "chu-de":
        if m.get("kind") != "topic" or p.stem not in THEMES:
            errs.append("chủ đề: kind: topic và tên file phải là theme hợp lệ")
        if names != TOPIC_SECS:
            errs.append(f"mục phải đúng {TOPIC_SECS}, đang có {names}")
        d = dict(secs)
        check_phrases(d.get("Cụm từ", ""), 15, 20, errs)
        if len(re.findall(r"^### ", d.get("Kho ý tưởng Task 2", ""), re.M)) < 4:
            errs.append("Kho ý tưởng cần ≥4 mục ###")
        rows = [l for l in d.get("Từ vựng Reading & Listening", "").splitlines() if l.startswith("|") and "---" not in l]
        if not 13 <= len(rows) <= 21:
            errs.append(f"bảng từ vựng có {len(rows) - 1} dòng (cần 12–20)")
    else:
        for k in ("skill", "group", "order", "title", "minutes", "crit", "summary"):
            if not m.get(k):
                errs.append(f"thiếu frontmatter {k}")
        if m.get("skill") not in SKILLS:
            errs.append("skill sai")
        if not set(filter(None, (m.get("crit") or "").split(","))) <= CRITS:
            errs.append("crit sai")
        if m.get("errors") and not set(m["errors"].split(",")) <= ERRS:
            errs.append("errors sai")
        if names != LESSON_SECS:
            errs.append(f"mục phải đúng {LESSON_SECS}, đang có {names}")
        d = dict(secs)
        fixes = [l for l in d.get("Lỗi hay gặp", "").splitlines() if l.startswith("- ")]
        errs += [f"dòng lỗi sai dạng: {l[:70]}" for l in fixes if not FIX.match(l)]
        if not 4 <= len(fixes) <= 8:
            errs.append(f"Lỗi hay gặp có {len(fixes)} dòng (cần 4–8)")
        check_phrases(d.get("Cụm nên học", ""), 6, 12, errs)
        check_quiz(d.get("Kiểm tra nhanh", ""), errs)
    return errs


if __name__ == "__main__":
    files = [Path(f).resolve() for f in sys.argv[1:]] or sorted((ROOT / "hoc/bai").glob("*.md")) + sorted((ROOT / "hoc/chu-de").glob("*.md"))
    bad = 0
    for p in files:
        e = validate(p)
        bad += bool(e)
        print(("OK  " if not e else "LỖI ") + p.relative_to(ROOT).as_posix() + "".join(f"\n    - {x}" for x in e))
    print(f"\n{len(files) - bad}/{len(files)} file đạt")
    sys.exit(1 if bad else 0)
