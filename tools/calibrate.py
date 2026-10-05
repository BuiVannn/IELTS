"""Hiệu chỉnh máy chấm Writing: chấm các bài mẫu có band chính thức trong calibration/, so sánh với band giám khảo.
Chạy: python3 tools/calibrate.py            (chấm song song, ~2–3 phút)
      python3 tools/calibrate.py --report   (chỉ in lại kết quả lần trước)
Kết quả lưu ở calibration/_results.json (không đưa vào git)."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import server  # noqa: E402
from build_index import frontmatter  # noqa: E402

CAL = ROOT / "calibration"
OUT = CAL / "_results.json"


def grade_one(p):
    meta = frontmatter(p)
    body = p.read_text(encoding="utf-8").split("---", 2)[2]
    prompt_part = body.split("## Bài", 1)[0]
    script = body.split("## Bài", 1)[1].split("## Nhận xét giám khảo")[0].strip()
    prompt = (f"Chấm bài IELTS Academic Writing Task {meta['task']}.\n\n# ĐỀ\n{prompt_part}\n\n"
              f"# BÀI LÀM CỦA HỌC VIÊN\n**Số từ:** {len(script.split())}\n{script}\n\n"
              "Chấm đúng format output bắt buộc trong system prompt, kết thúc bằng khối ```json.")
    res = server.parse_result(server.run_claude(server.RUBRIC["writing"], prompt))
    return {"file": p.name, "task": meta["task"], "official": float(meta["official_band"]),
            "official_criteria": meta.get("criteria"), "band": res.get("band"), "raw": res.get("raw"), "criteria": res.get("criteria")}


def report(rows):
    print(f"{'file':34} {'task':>4} {'chính thức':>10} {'máy':>5} {'lệch':>6}  tiêu chí máy chấm")
    diffs = []
    for r in sorted(rows, key=lambda r: (r["task"], r["official"])):
        d = None if r["band"] is None else r["band"] - r["official"]
        diffs.append(d)
        print(f"{r['file']:34} {r['task']:>4} {r['official']:>10} {str(r['band']):>5} {'' if d is None else f'{d:+.1f}':>6}  {r['criteria']}")
    ds = [d for d in diffs if d is not None]
    if ds:
        print(f"\nLệch trung bình {sum(ds) / len(ds):+.2f} band · lệch tuyệt đối TB {sum(map(abs, ds)) / len(ds):.2f} · "
              f"trong ±0.5: {sum(abs(d) <= 0.5 for d in ds)}/{len(ds)}")


if __name__ == "__main__":
    if "--report" not in sys.argv:
        files = sorted(CAL.glob("cal-*.md"))
        with ThreadPoolExecutor(max_workers=4) as ex:
            rows = list(ex.map(grade_one, files))
        OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    report(json.loads(OUT.read_text(encoding="utf-8")))
