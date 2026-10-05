"""Web luyện IELTS Academic — chạy: python3 server.py  → mở http://localhost:8766
Stdlib only. Chấm Writing/Speaking bằng Claude Code CLI local (`claude -p`)."""
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from build_index import frontmatter, main as build_index  # noqa: E402

PORT = 8766
EXAM_DIRS = ["writing/task1", "writing/task2", "speaking/part1", "speaking/part2"]
ATTEMPTS = ROOT / "attempts"
RUBRIC = {"writing": ROOT / "cham-diem/rubric-writing.md", "speaking": ROOT / "cham-diem/rubric-speaking.md"}
CLAUDE_TIMEOUT = 900


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


def grade(item_id, answers):
    path = exam_files()[item_id]
    meta = frontmatter(path)
    skill, part = meta["skill"], meta.get("part")
    what = f"IELTS Academic Writing Task {part}" if skill == "writing" else \
        f"IELTS Speaking {'Part 1' if part == '1' else 'Part 2 (cue card) + Part 3'}"
    ans = format_answers(answers)
    prompt = (f"Chấm bài {what} — đề `{item_id}`.\n\n"
              f"# ĐỀ\n{exam_without_samples(path)}\n\n# BÀI LÀM CỦA HỌC VIÊN\n{ans}\n\n{previous_attempt(item_id)}"
              "Chấm đúng format output bắt buộc trong system prompt, kết thúc bằng khối ```json.")
    feedback = run_claude(RUBRIC[skill], prompt)
    result = parse_result(feedback)
    save_attempt(meta["id"], skill, part, ans, feedback, result, path)
    return {"feedback": feedback, "result": result}


def save_attempt(item_id, skill, part, ans, feedback, result, path=None):
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    d = ATTEMPTS / item_id
    d.mkdir(parents=True, exist_ok=True)
    band, raw = result.get("band"), result.get("raw")
    (d / f"{ts}.md").write_text(
        f"---\nid: {item_id}\nskill: {skill}\npart: {part}\ndate: {ts}\nband: {'' if band is None else band}\n"
        f"raw: {'' if raw is None else round(raw, 2)}\ncriteria: {json.dumps(result.get('criteria', {}))}\n---\n\n"
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
    return {"feedback": feedback, "result": result}


RL_LOG = ATTEMPTS / "_rl" / "log.jsonl"


def save_rl(entry):
    """Một lần làm Reading (đáp án chấm ở trình duyệt)."""
    if entry.get("skill") != "reading":
        raise ValueError("chỉ lưu kết quả Reading")
    append_jsonl(RL_LOG, [{k: entry.get(k) for k in ("skill", "source", "raw", "band", "rows")}])
    return {"ok": True}


def list_attempts():
    out = []
    for p in sorted(ATTEMPTS.glob("*/*.md")):
        if p.parent.name.startswith("_"):
            continue
        m = frontmatter(p) or {}
        out.append({k: m.get(k) for k in ("id", "skill", "part", "date", "band", "raw", "criteria")}
                   | {"file": p.relative_to(ROOT).as_posix()})
    return out


class Handler(SimpleHTTPRequestHandler):
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
        else:
            super().do_GET()

    def do_POST(self):
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or "{}")
            if self.path == "/api/mock-grade":
                return self.send_json(grade_mock(data.get("items", [])[:30]))
            if self.path == "/api/rl":
                return self.send_json(save_rl(data))
            files = exam_files()
            if data.get("id") not in files:
                return self.send_json({"error": "id không tồn tại"}, 404)
            if self.path == "/api/grade":
                self.send_json(grade(data["id"], data.get("answers", [])))
            elif self.path == "/api/status":
                if data.get("status") not in ("todo", "doing", "done"):
                    return self.send_json({"error": "status sai"}, 400)
                set_fields(files[data["id"]], status=data["status"])
                build_index()
                self.send_json({"ok": True})
            else:
                self.send_json({"error": "not found"}, 404)
        except subprocess.TimeoutExpired:
            self.send_json({"error": "Claude chấm quá lâu (timeout)"}, 504)
        except Exception as e:  # trả lỗi về UI thay vì treo request
            self.send_json({"error": str(e)}, 500)


if __name__ == "__main__":
    print(f"Mở http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(ROOT))).serve_forever()
