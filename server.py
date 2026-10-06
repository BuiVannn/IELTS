"""Web luyện IELTS Academic — chạy: python3 server.py  → mở http://localhost:8766
Stdlib only. Chấm Writing/Speaking bằng Claude Code CLI local (`claude -p`)."""
import base64
import hmac
import json
import math
import mimetypes
import os
import re
import subprocess
import sys
import threading
from datetime import date, datetime, timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from build_index import frontmatter, main as build_index  # noqa: E402

PORT = 8766
mimetypes.add_type("application/manifest+json", ".webmanifest")
EXAM_DIRS = ["writing/task1", "writing/task2", "speaking/part1", "speaking/part2"]
ATTEMPTS = ROOT / "attempts"
RUBRIC = {"writing": ROOT / "cham-diem/rubric-writing.md", "speaking": ROOT / "cham-diem/rubric-speaking.md"}
CLAUDE_TIMEOUT = 900
LOG = ATTEMPTS / "_log"
STUDY_LOG = LOG / "study.jsonl"      # mỗi dòng: {d, skill, sec, manual}
STATE = LOG / "state.json"           # cài đặt, check-in, ngày nghỉ phép
VOCAB = ATTEMPTS / "_vocab" / "vocab.json"
STUDY_SKILLS = {"writing", "speaking", "reading", "vocab", "listening"}
ERROR_KEYS = ["article", "plural", "tense", "agreement", "word_form", "collocation", "spelling", "punctuation", "repetition", "sentence"]
LEITNER = [0, 1, 2, 4, 8, 16]        # số ngày chờ theo hộp 0–5
ACTIVE_USES = 3                      # dùng đúng trong 3 bài khác nhau → từ chủ động
LOCK = threading.Lock()              # ponytail: một khoá chung cho mọi file JSON, đủ cho 1 người dùng


def exam_files():
    return {p.stem: p for d in EXAM_DIRS for p in (ROOT / d).glob("*.md")}


def set_fields(path, **fields):
    """Sửa các dòng key: value trong frontmatter (giữ nguyên phần còn lại)."""
    text = path.read_text(encoding="utf-8")
    _, fm, body = text.split("---", 2)
    for k, v in fields.items():
        line = f"{k}: {v}"
        fm, n = re.subn(rf"^{k}:.*$", line, fm, count=1, flags=re.M)
        if not n:
            fm = fm.rstrip("\n") + f"\n{line}\n"
    path.write_text(f"---{fm}---{body}", encoding="utf-8")


def chart_to_table(spec):
    """Khối ```chart (JSON) → bảng markdown, để Claude đọc được số liệu của biểu đồ."""
    try:
        c = json.loads(spec)
    except json.JSONDecodeError:
        return spec
    unit = f" ({c['unit']})" if c.get("unit") else ""
    head = f"**{c.get('title', 'Chart')}**{unit} — dạng {c.get('type', '?')}\n\n"
    cols = c.get("labels", [])
    rows = [f"| | {' | '.join(map(str, cols))} |", "|---" * (len(cols) + 1) + "|"]
    rows += [f"| {d.get('label', '')} | {' | '.join(map(str, d.get('data', [])))} |" for d in c.get("datasets", [])]
    return head + "\n".join(rows)


def exam_without_samples(path):
    body = path.read_text(encoding="utf-8").split("---", 2)[2]
    body = re.split(r"^## Bài mẫu", body, flags=re.M)[0]
    body = re.sub(r"<details>.*?</details>", "", body, flags=re.S)
    return re.sub(r"```chart\s*(.*?)```", lambda m: chart_to_table(m.group(1)), body, flags=re.S)


def band_of(criteria):
    """Band = trung bình các tiêu chí, làm tròn XUỐNG nửa band (cách phổ biến ở cấp W/S)."""
    xs = [float(v) for v in (criteria or {}).values() if isinstance(v, (int, float))]
    if not xs:
        return None, None
    raw = sum(xs) / len(xs)
    return raw, math.floor(raw * 2) / 2


def previous_attempt(item_id):
    """Lần chấm gần nhất của đề này → để Claude so sánh tiến bộ."""
    files = sorted((ATTEMPTS / item_id).glob("*.md"))
    if not files:
        return ""
    m = frontmatter(files[-1]) or {}
    todo = re.search(r"^## 3 việc cần làm lần sau\n(.*?)(?=^```|^## |\Z)", files[-1].read_text(encoding="utf-8"), re.M | re.S)
    return (f"# LẦN CHẤM TRƯỚC CỦA ĐỀ NÀY ({m.get('date')}, tổng {len(files)} lần)\n"
            f"Band: {m.get('band')} · tiêu chí: {m.get('criteria')}\n"
            f"Việc đã dặn lần trước:\n{todo.group(1).strip() if todo else '(không có)'}\n\n")


def parse_json_block(feedback):
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", feedback, re.S)
    try:
        return json.loads(blocks[-1]) if blocks else {}
    except json.JSONDecodeError:
        return {}


def parse_result(feedback):
    result = parse_json_block(feedback)
    result["raw"], result["band"] = band_of(result.get("criteria"))
    return result


def run_claude(rubric, prompt, model=None):
    # Bỏ ANTHROPIC_API_KEY + settings user (settings.json đang đặt key hỏng) → dùng đăng nhập claude.ai
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    cmd = ["claude", "-p", "--setting-sources", "project", "--tools", "",
           "--system-prompt", rubric.read_text(encoding="utf-8")] + (["--model", model] if model else [])
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=CLAUDE_TIMEOUT, cwd=ROOT, env=env)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip() or "claude CLI lỗi")
    return r.stdout.strip()


def format_answers(answers):
    return "\n\n".join(
        f"### {a.get('label', '')}\n**Câu hỏi:** {a.get('question', '')}\n"
        + (f"**Thời lượng nói:** {a['seconds']} giây / giới hạn {a.get('limit', '?')} giây\n" if a.get("seconds") else "")
        + f"**Số từ:** {len((a.get('text') or '').split())}\n"
        + f"**Bài làm:**\n{(a.get('text') or '').strip() or '(bỏ trống)'}"
        for a in answers)


def targets_note(targets):
    if not targets:
        return ""
    return ("# TỪ ĐÍCH\nHọc viên được giao cố dùng các cụm sau trong bài: "
            + "; ".join(f"`{t}`" for t in targets)
            + ". Trong json, trả mảng `targets` (mỗi cụm một phần tử, giữ nguyên chữ `en`).\n\n")


def grade(item_id, answers, targets=None):
    path = exam_files()[item_id]
    meta = frontmatter(path)
    skill, part = meta["skill"], meta.get("part")
    what = f"IELTS Academic Writing Task {part}" if skill == "writing" else \
        f"IELTS Speaking {'Part 1' if part == '1' else 'Part 2 (cue card) + Part 3'}"
    ans = format_answers(answers)
    prompt = (f"Chấm bài {what} — đề `{item_id}`.\n\n"
              f"# ĐỀ\n{exam_without_samples(path)}\n\n# BÀI LÀM CỦA HỌC VIÊN\n{ans}\n\n{previous_attempt(item_id)}"
              f"{targets_note(targets)}"
              "Chấm đúng format output bắt buộc trong system prompt, kết thúc bằng khối ```json.")
    feedback = run_claude(RUBRIC[skill], prompt)
    result = parse_result(feedback)
    save_attempt(meta["id"], skill, part, ans, feedback, result, path)
    result["vocab_added"] = harvest(result, meta["id"], meta.get("theme"))
    return {"feedback": feedback, "result": result}


def save_attempt(item_id, skill, part, ans, feedback, result, path=None):
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    d = ATTEMPTS / item_id
    d.mkdir(parents=True, exist_ok=True)
    band, raw = result.get("band"), result.get("raw")
    (d / f"{ts}.md").write_text(
        f"---\nid: {item_id}\nskill: {skill}\npart: {part}\ndate: {ts}\nband: {'' if band is None else band}\n"
        f"raw: {'' if raw is None else round(raw, 2)}\ncriteria: {json.dumps(result.get('criteria', {}))}\n"
        f"errors: {json.dumps(clean_errors(result.get('errors')))}\n---\n\n"
        f"# Bài làm\n\n{ans}\n\n# Nhận xét\n\n{feedback}\n", encoding="utf-8")
    if not path:
        return
    meta = frontmatter(path)
    best = meta.get("best_score") or ""
    try:
        best = max(float(best), float(band)) if best else band
    except (TypeError, ValueError):
        best = best or band
    set_fields(path, status="done", attempts=int(meta.get("attempts") or 0) + 1,
               best_score="" if best is None else best)
    build_index()


def append_jsonl(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    t = datetime.now().isoformat(timespec="seconds")
    with path.open("a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps({**e, "t": t}, ensure_ascii=False) + "\n")


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


MOCK_NOTE = """
# GHI CHÚ: ĐÂY LÀ BÀI THI THỬ SPEAKING ĐẦY ĐỦ (Part 1 → Part 2 cue card → Part 3, ~12 phút, bốc đề ngẫu nhiên)
- Chấm theo hiệu suất trung bình của CẢ BÀI như thi thật.
- Trong "## Nhận xét từng phần", tách rõ Part 1 / Part 2 / Part 3 và nói part nào đang kéo band xuống.
"""


def grade_mock(items):
    """Chấm bài thi thử Speaking IELTS."""
    files, seen, exams = exam_files(), set(), []
    for it in items:
        eid = it.get("exam_id")
        if eid in files and eid not in seen and it.get("part") != 1:
            seen.add(eid)
            exams.append(f"## {frontmatter(files[eid]).get('title')} (`{eid}`)\n{exam_without_samples(files[eid])}")
    ans = format_answers({**a, "label": f"Part {a.get('part')} — {a.get('label', '')}"} for a in items)
    prompt = (f"Chấm BÀI THI THỬ IELTS SPEAKING.\n{MOCK_NOTE}\n# ĐỀ PART 2–3\n" + "\n\n".join(exams)
              + f"\n\n# BÀI LÀM CỦA HỌC VIÊN (Part 1 là câu hỏi ngắn bên dưới)\n{ans}\n\n{previous_attempt('MOCK-speaking')}"
              "Chấm đúng format output bắt buộc trong system prompt, kết thúc bằng khối ```json.")
    feedback = run_claude(RUBRIC["speaking"], prompt)
    result = parse_result(feedback)
    save_attempt("MOCK-speaking", "speaking", "mock", ans, feedback, result)
    result["vocab_added"] = harvest(result, "MOCK-speaking", None)
    return {"feedback": feedback, "result": result}


RL_LOG = ATTEMPTS / "_rl" / "log.jsonl"


def save_rl(entry):
    """Một lần làm Reading (đáp án chấm ở trình duyệt)."""
    if entry.get("skill") != "reading":
        raise ValueError("chỉ lưu kết quả Reading")
    append_jsonl(RL_LOG, [{k: entry.get(k) for k in ("skill", "source", "raw", "keyed", "band", "rows", "test", "part")}])
    return {"ok": True}


def reading_tests():
    """Đề Reading làm trên web (reading/de/*.json): chỉ trả mục lục, đề đầy đủ tải tĩnh từ /reading/de/<id>.json."""
    out = []
    for p in sorted((ROOT / "reading/de").glob("*.json")):
        t = json.loads(p.read_text())
        out.append({"id": t["id"], "title": t["title"], "passages": [x["title"] for x in t["passages"]],
                    "types": [sorted({g["type"] for g in x["groups"]}) for x in t["passages"]]})
    return out


def list_attempts():
    out = []
    for p in sorted(ATTEMPTS.glob("*/*.md")):
        if p.parent.name.startswith("_"):
            continue
        m = frontmatter(p) or {}
        out.append({k: m.get(k) for k in ("id", "skill", "part", "date", "band", "raw", "criteria", "errors")}
                   | {"file": p.relative_to(ROOT).as_posix()})
    return out


def clean_errors(errors):
    """Nhãn lỗi máy chấm trả về → chỉ giữ các khoá đã định, giá trị là số nguyên ≥ 0."""
    errors = errors if isinstance(errors, dict) else {}
    out = {}
    for k in ERROR_KEYS:
        try:
            out[k] = max(0, int(errors.get(k) or 0))
        except (TypeError, ValueError):
            out[k] = 0
    return out


# ---------- giờ học & check-in ----------
def today():
    return date.today().isoformat()


def add_study(skill, sec, manual=False, day=None):
    if skill not in STUDY_SKILLS:
        raise ValueError("kỹ năng không hợp lệ")
    sec = int(sec)
    if not 0 < sec <= 4 * 3600:
        raise ValueError("số giây không hợp lệ")
    day = day or today()
    date.fromisoformat(day)  # sai định dạng → lỗi
    with LOCK:
        append_jsonl(STUDY_LOG, [{"d": day, "skill": skill, "sec": sec, "manual": bool(manual)}])
    return {"ok": True}


def study_days():
    """{ngày: {kỹ năng: giây}}"""
    out = {}
    for e in read_jsonl(STUDY_LOG):
        day = out.setdefault(e["d"], {})
        day[e["skill"]] = day.get(e["skill"], 0) + int(e["sec"])
    return out


DEFAULT_SETTINGS = {"daily_min": 75, "min_day": 15, "week_goal_h": 10, "exam_date": "", "start_date": "2026-10-05",
                    "freeze_per_month": 2, "new_words_per_day": 10}


def read_state():
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    st["settings"] = {**DEFAULT_SETTINGS, **st.get("settings", {})}
    st.setdefault("checks", {})
    st.setdefault("freezes", [])
    st.setdefault("lessons", {})
    return st


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def update_state(data):
    with LOCK:
        st = read_state()
        if isinstance(data.get("settings"), dict):
            for k, v in data["settings"].items():
                if k in DEFAULT_SETTINGS:
                    st["settings"][k] = v
        if "check" in data:  # {"date", "key", "done"}
            c = data["check"]
            date.fromisoformat(c["date"])
            keys = set(st["checks"].get(c["date"], []))
            keys.add(c["key"]) if c.get("done") else keys.discard(c["key"])
            st["checks"][c["date"]] = sorted(keys)
        if "lesson" in data:  # {"id", "done", "quiz"}: đánh dấu đã học bài, điểm kiểm tra nhanh
            ls = data["lesson"]
            if not re.fullmatch(r"[a-z0-9-]+", str(ls.get("id"))) or not (ROOT / "hoc/bai" / f"{ls.get('id')}.md").exists() and not (ROOT / "hoc/chu-de" / f"{ls.get('id')}.md").exists():
                raise ValueError("không có bài học này")
            lessons = st.setdefault("lessons", {})
            if ls.get("done") is False:
                lessons.pop(ls["id"], None)
            else:
                cur = lessons.get(ls["id"], {})
                lessons[ls["id"]] = {"date": cur.get("date") or today(), "quiz": ls.get("quiz", cur.get("quiz", ""))}
        if "freeze" in data:  # {"date", "on"}
            d = data["freeze"]["date"]
            date.fromisoformat(d)
            fz = set(st["freezes"])
            if data["freeze"].get("on"):
                used = sum(1 for x in fz if x[:7] == d[:7])
                if d not in fz and used >= int(st["settings"]["freeze_per_month"]):
                    raise ValueError(f"tháng này đã dùng hết {used} ngày nghỉ phép")
                fz.add(d)
            else:
                fz.discard(d)
            st["freezes"] = sorted(fz)
        write_json(STATE, st)
        return st


# ---------- từ vựng chủ động ----------
def norm_phrase(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' /-]", "", str(s or "").lower())).strip()


def read_vocab():
    return json.loads(VOCAB.read_text(encoding="utf-8")) if VOCAB.exists() else []


def stage(card):
    uses = len({u["id"] for u in card.get("uses", []) if u.get("ok")})
    if uses >= ACTIVE_USES:
        return "active"
    if uses:
        return "used"
    return "recall" if card.get("box", 0) >= 3 else "new"


def add_cards(items, src_id, theme):
    """Thêm cụm mới (bỏ trùng). Trả về số cụm thêm được."""
    cards, added = read_vocab(), 0
    seen = {norm_phrase(c["en"]) for c in cards}
    for it in items or []:
        en = str(it.get("en") or "").strip()
        if not en or norm_phrase(en) in seen or len(en) > 80:
            continue
        seen.add(norm_phrase(en))
        cards.append({"id": f"v{int(datetime.now().timestamp() * 1000)}{added}", "en": en,
                      "vi": str(it.get("vi") or "").strip(), "ex": str(it.get("ex") or "").strip(),
                      "from": str(it.get("from") or "").strip(), "src": src_id or "", "theme": theme or "",
                      "added": today(), "box": 0, "due": today(), "reviews": 0, "lapses": 0, "uses": []})
        added += 1
    write_json(VOCAB, cards)
    return added


def harvest(result, src_id, theme):
    """Sau mỗi lần chấm: lấy cụm nên học vào kho, ghi nhận từ đích đã dùng đúng."""
    with LOCK:
        added = add_cards(result.get("vocab"), src_id, theme)
        cards = read_vocab()
        by = {norm_phrase(c["en"]): c for c in cards}
        for t in result.get("targets") or []:
            c = by.get(norm_phrase(t.get("en")))
            if c and t.get("used"):
                was_active = stage(c) == "active"
                c["uses"] = [u for u in c["uses"] if u["id"] != src_id] + [{"id": src_id, "date": today(), "ok": bool(t.get("ok"))}]
                if stage(c) == "active" and not was_active:
                    c["due"] = (date.today() + timedelta(days=30)).isoformat()
        write_json(VOCAB, cards)
        return added


def review_card(card, ok, day=None):
    """Leitner: đúng → lên 1 hộp, chờ LEITNER[hộp] ngày; sai → về hộp 1, ôn lại ngày mai. Từ chủ động: 30 ngày."""
    d = date.fromisoformat(day or today())
    card["prev"] = {k: card.get(k) for k in ("box", "due", "reviews", "lapses", "last")}  # để "Tôi đúng, chỉ khác cách viết" hoàn tác lần chấm sai
    card["reviews"] = card.get("reviews", 0) + 1
    card["last"] = d.isoformat()
    if ok:
        card["box"] = min(5, card.get("box", 0) + 1)
        wait = 30 if stage(card) == "active" else LEITNER[card["box"]]
    else:
        card["box"], card["lapses"], wait = 1, card.get("lapses", 0) + 1, 1
    card["due"] = (d + timedelta(days=wait)).isoformat()
    return card


def vocab_action(data):
    with LOCK:
        a = data.get("action")
        if a == "add":
            n = add_cards([data], data.get("src") or "manual", data.get("theme"))
            if not n:
                raise ValueError("cụm trống hoặc đã có trong kho")
            return {"ok": True}
        cards = read_vocab()
        card = next((c for c in cards if c["id"] == data.get("id")), None)
        if not card:
            raise ValueError("không thấy cụm từ")
        if a == "review":
            if data.get("undo") and card.get("prev"):
                card.update(card.pop("prev"))
            review_card(card, bool(data.get("ok")))
        elif a == "edit":
            for k in ("en", "vi", "ex"):
                if k in data:
                    card[k] = str(data[k]).strip()
        elif a == "delete":
            cards.remove(card)
        else:
            raise ValueError("action sai")
        write_json(VOCAB, cards)
        return {"ok": True, "card": card}


VOCAB_RUBRIC = ROOT / "cham-diem/rubric-tu.md"


def check_sentence(phrases, sentence):
    """Chấm nhanh câu tự đặt có dùng cụm đích (model nhỏ cho nhanh)."""
    prompt = (f"Cụm đích: {'; '.join(f'`{p}`' for p in phrases)}\n\nCâu của học viên:\n{sentence.strip()}\n\n"
              "Trả lời đúng format trong system prompt.")
    out = parse_json_block(run_claude(VOCAB_RUBRIC, prompt, model="haiku"))
    if "ok" not in out:
        raise RuntimeError("Không đọc được kết quả chấm câu")
    return out


def lesson_list():
    out = []
    for d in ("hoc/bai", "hoc/chu-de"):
        for p in sorted((ROOT / d).glob("*.md")):
            m = frontmatter(p) or {}
            out.append({**m, "id": p.stem, "path": p.relative_to(ROOT).as_posix(), "kind": m.get("kind") or "lesson"})
    return out


def vocab_list():
    cards = read_vocab()
    for c in cards:
        c["stage"] = stage(c)
    return cards


PASS_FILE = ROOT / ".matkhau"


def authorized(headers):
    """Máy mình (localhost) vào thẳng; qua Cloudflare Tunnel (có Cf-Connecting-IP) phải nhập mật khẩu trong .matkhau."""
    if "Cf-Connecting-IP" not in headers:
        return True
    pw = PASS_FILE.read_text().strip() if PASS_FILE.exists() else ""
    if not pw:
        return False
    try:
        given = base64.b64decode(headers.get("Authorization", "")[6:]).decode().split(":", 1)[1]
    except Exception:
        return False
    return hmac.compare_digest(given.encode(), pw.encode())


class Handler(SimpleHTTPRequestHandler):
    def parse_request(self):
        if not super().parse_request():
            return False
        if authorized(self.headers):
            return True
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="IELTS"')
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/web/")
            self.end_headers()
        elif self.path == "/api/items":
            items = []
            for stem, p in exam_files().items():
                m = frontmatter(p) or {}
                items.append({**m, "id": stem, "path": p.relative_to(ROOT).as_posix()})
            self.send_json(items)
        elif self.path == "/api/attempts":
            self.send_json(list_attempts())
        elif self.path == "/api/rl":
            self.send_json(read_jsonl(RL_LOG))
        elif self.path == "/api/study":
            self.send_json(study_days())
        elif self.path == "/api/state":
            self.send_json(read_state())
        elif self.path == "/api/vocab":
            self.send_json(vocab_list())
        elif self.path == "/api/lessons":
            self.send_json(lesson_list())
        elif self.path == "/api/reading":
            self.send_json(reading_tests())
        else:
            super().do_GET()

    def do_POST(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or "{}")
            if self.path == "/api/mock-grade":
                return self.send_json(grade_mock(data.get("items", [])[:30]))
            if self.path == "/api/rl":
                return self.send_json(save_rl(data))
            if self.path == "/api/study":
                return self.send_json(add_study(data.get("skill"), data.get("sec", 0), data.get("manual"), data.get("date")))
            if self.path == "/api/state":
                return self.send_json(update_state(data))
            if self.path == "/api/vocab":
                return self.send_json(vocab_action(data))
            if self.path == "/api/vocab-check":
                phrases = [str(p) for p in data.get("phrases", [])][:3]
                if not phrases or not str(data.get("sentence", "")).strip():
                    return self.send_json({"error": "thiếu cụm hoặc câu"}, 400)
                return self.send_json(check_sentence(phrases, str(data["sentence"])[:600]))
            files = exam_files()
            if data.get("id") not in files:
                return self.send_json({"error": "id không tồn tại"}, 404)
            if self.path == "/api/grade":
                self.send_json(grade(data["id"], data.get("answers", []), [str(t) for t in data.get("targets", [])][:6]))
            elif self.path == "/api/status":
                if data.get("status") not in ("todo", "doing", "done"):
                    return self.send_json({"error": "status sai"}, 400)
                set_fields(files[data["id"]], status=data["status"])
                build_index()
                self.send_json({"ok": True})
            else:
                self.send_json({"error": "not found"}, 404)
        except ValueError as e:
            self.send_json({"error": str(e)}, 400)
        except subprocess.TimeoutExpired:
            self.send_json({"error": "Claude chấm quá lâu (timeout)"}, 504)
        except Exception as e:  # trả lỗi về UI thay vì treo request
            self.send_json({"error": str(e)}, 500)


if __name__ == "__main__":
    print(f"Mở http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(ROOT))).serve_forever()
