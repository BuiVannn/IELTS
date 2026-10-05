"""Quét frontmatter các file đề → sinh INDEX.md (checklist tiến độ).
Chạy: python3 tools/build_index.py"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = {"done": "[x]", "doing": "[~]"}
SECTIONS = [("Writing Task 1", "writing/task1"), ("Writing Task 2", "writing/task2"),
            ("Speaking Part 1", "speaking/part1"), ("Speaking Part 2 + 3", "speaking/part2")]


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    meta = {}
    for line in text.split("---", 2)[1].splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split("#")[0].strip()
    return meta


def row(p, m):
    rel = p.relative_to(ROOT).as_posix()
    hot = "· trọng điểm" if m.get("hot") == "true" else ""
    return (f"| {MARK.get(m.get('status'), '[ ]')} | [{m.get('id', p.stem)}]({rel}) | "
            f"{m.get('title', '')} {hot} | {m.get('attempts') or 0} | {m.get('best_score') or ''} |")


def section(title, files):
    items = [(p, m) for p in sorted(files) if (m := frontmatter(p))]
    done = sum(m.get("status") == "done" for _, m in items)
    out = [f"## {title} — {done}/{len(items)} xong", "",
           "| ✓ | ID | Đề | Lần làm | Band cao nhất |", "|---|---|---|---|---|"]
    return out + [row(p, m) for p, m in items] + [""], done, len(items)


def main():
    body, total_done, total = [], 0, 0
    for title, d in SECTIONS:
        lines, done, n = section(title, (ROOT / d).glob("*.md"))
        body += lines
        total_done += done
        total += n
    head = ["# CHECKLIST ĐỀ IELTS (tự sinh — đừng sửa tay, sửa `status` trong từng file)", "",
            f"**Tiến độ: {total_done}/{total}** · [x] xong · [~] đang làm", ""]
    (ROOT / "INDEX.md").write_text("\n".join(head + body), encoding="utf-8")
    print(f"INDEX.md: {total_done}/{total}")


if __name__ == "__main__":
    main()
