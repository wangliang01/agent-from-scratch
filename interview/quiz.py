#!/usr/bin/env python3
"""面试题库 CLI：抽题、看题、标记掌握度、统计进度。

用法见 interview/README.md，或运行 `uv run python interview/quiz.py -h`。
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
QUESTIONS_DIR = BASE / "questions"
PROGRESS_FILE = BASE / "progress.json"

STATUS_LABEL = {
    "solid": "✅",
    "shaky": "⚠️",
    "miss": "❌",
}

WEEK_LABEL = {0: "第0周", 1: "第1周", 2: "第2周", 3: "第3周", 4: "第4周", 5: "综合"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_questions() -> list[dict]:
    if not QUESTIONS_DIR.exists():
        sys.exit(f"题库目录不存在: {QUESTIONS_DIR}")

    questions: list[dict] = []
    seen: set[str] = set()
    for path in sorted(QUESTIONS_DIR.glob("*.jsonl")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                q = json.loads(line)
            except json.JSONDecodeError as exc:
                sys.exit(f"{path.name}:{lineno} JSON 解析失败: {exc}")
            for key in ("id", "week", "level", "q"):
                if key not in q:
                    sys.exit(f"{path.name}:{lineno} 缺少字段: {key}")
            if q["id"] in seen:
                sys.exit(f"{path.name}:{lineno} 题目 id 重复: {q['id']}")
            seen.add(q["id"])
            q.setdefault("tags", [])
            q.setdefault("probe", [])
            q.setdefault("strong", [])
            q.setdefault("weak", [])
            q.setdefault("anchor", "")
            questions.append(q)
    return questions


def load_progress() -> dict:
    if not PROGRESS_FILE.exists():
        return {}
    return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))


def save_progress(progress: dict) -> None:
    PROGRESS_FILE.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def filter_questions(questions: list[dict], args) -> list[dict]:
    progress = load_progress()
    result = questions

    week = getattr(args, "week", None)
    if week is not None:
        result = [q for q in result if q.get("week") == week]

    tag = getattr(args, "tag", None)
    if tag:
        result = [q for q in result if tag in q.get("tags", [])]

    level = getattr(args, "level", None)
    if level:
        result = [q for q in result if q.get("level") == level]

    if getattr(args, "unseen", False):
        result = [q for q in result if q["id"] not in progress]

    if getattr(args, "weak", False):
        result = [
            q for q in result
            if progress.get(q["id"], {}).get("status") in ("shaky", "miss")
        ]

    return result


def print_question(q: dict) -> None:
    tags = ", ".join(q.get("tags", []))
    week = WEEK_LABEL.get(q.get("week", 5), "综合")
    print(f"[{q['id']}] {week} · {q['level']}" + (f" · {tags}" if tags else ""))
    print()
    print(f"  {q['q']}")
    print()
    if q["probe"]:
        print("  面试官会继续追：")
        for i, p in enumerate(q["probe"], 1):
            print(f"    {i}. {p}")
        print()
    if q.get("anchor"):
        print(f"  锚点: {q['anchor']}")
        print()
    print(f"  （看答案要点：uv run python interview/quiz.py reveal {q['id']}）")


def cmd_list(args, questions: list[dict]) -> None:
    pool = filter_questions(questions, args)
    if not pool:
        print("没有符合条件的题目。")
        return
    progress = load_progress()
    for q in pool:
        status = progress.get(q["id"], {}).get("status", "")
        mark = STATUS_LABEL.get(status, "·")
        week = WEEK_LABEL.get(q.get("week", 5), "综合")
        print(f"{mark} {q['id']:<12} {week:<5} {q['level']:<3} {q['q']}")
    print(f"\n共 {len(pool)} 题")


def cmd_show(args, questions: list[dict]) -> None:
    q = next((x for x in questions if x["id"] == args.id), None)
    if q is None:
        sys.exit(f"没有这道题: {args.id}")
    print_question(q)


def cmd_reveal(args, questions: list[dict]) -> None:
    q = next((x for x in questions if x["id"] == args.id), None)
    if q is None:
        sys.exit(f"没有这道题: {args.id}")

    print(f"[{q['id']}] {q['q']}\n")
    if q["strong"]:
        print("强答案要点：")
        for s in q["strong"]:
            print(f"  ✓ {s}")
        print()
    if q["weak"]:
        print("常见弱答案（对照自己有没有踩）：")
        for w in q["weak"]:
            print(f"  ✗ {w}")
        print()
    if q.get("anchor"):
        print(f"锚点: {q['anchor']}")


def cmd_draw(args, questions: list[dict]) -> None:
    pool = filter_questions(questions, args)
    if not pool:
        sys.exit("没有符合条件的题目。")

    if args.seed is not None:
        random.seed(args.seed)
    picked = random.sample(pool, min(args.n, len(pool)))

    for i, q in enumerate(picked):
        if i:
            print("\n" + "─" * 60 + "\n")
        print_question(q)

    print(f"\n抽了 {len(picked)} 题，共 {len(pool)} 题符合条件。")


def cmd_mark(args, questions: list[dict]) -> None:
    if not any(q["id"] == args.id for q in questions):
        sys.exit(f"没有这道题: {args.id}")

    progress = load_progress()
    entry = progress.get(args.id, {"attempts": 0})
    entry["status"] = args.status
    entry["attempts"] = entry.get("attempts", 0) + 1
    entry["last"] = date.today().isoformat()
    progress[args.id] = entry
    save_progress(progress)
    print(f"{args.id} → {STATUS_LABEL[args.status]} {args.status}")


def cmd_stats(args, questions: list[dict]) -> None:
    progress = load_progress()
    by_week: dict[int, list[dict]] = {}
    for q in questions:
        by_week.setdefault(q.get("week", 5), []).append(q)

    print(f"{'周次':<6}{'题数':>4}{'✅':>4}{'⚠️':>4}{'❌':>4}{'未做':>5}")
    total_solid = 0
    for week in sorted(by_week):
        qs = by_week[week]
        counts = {"solid": 0, "shaky": 0, "miss": 0}
        unseen = 0
        for q in qs:
            status = progress.get(q["id"], {}).get("status")
            if status in counts:
                counts[status] += 1
            else:
                unseen += 1
        total_solid += counts["solid"]
        label = WEEK_LABEL.get(week, "综合")
        print(
            f"{label:<6}{len(qs):>4}{counts['solid']:>4}"
            f"{counts['shaky']:>4}{counts['miss']:>4}{unseen:>5}"
        )

    n = len(questions)
    pct = total_solid / n * 100 if n else 0
    print(f"\n掌握度: {total_solid}/{n} ({pct:.0f}%)   （只有 solid 算掌握）")


def cmd_review(args, questions: list[dict]) -> None:
    progress = load_progress()
    weak = [
        q for q in questions
        if progress.get(q["id"], {}).get("status") in ("shaky", "miss")
    ]
    if not weak:
        print("没有需要复习的题。")
        return

    weak.sort(key=lambda q: (q.get("week", 5), q["id"]))
    for q in weak:
        status = progress[q["id"]]["status"]
        print(f"{STATUS_LABEL[status]} [{q['id']}] {q['q']}")
    print(f"\n共 {len(weak)} 题需要复习。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="面试题库 CLI：抽题、看答案、记录掌握度。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  uv run python interview/quiz.py draw --week 1 -n 3\n"
            "  uv run python interview/quiz.py reveal tools-003\n"
            "  uv run python interview/quiz.py mark tools-003 shaky\n"
            "  uv run python interview/quiz.py stats\n"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_filters(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--week", type=int, help="按周次过滤（0-4，5 为综合）")
        sp.add_argument("--tag", help="按标签过滤，如 retrieval")
        sp.add_argument("--level", choices=["L1", "L2", "L3", "L4", "L5"], help="按追问层级过滤")

    sp = sub.add_parser("list", help="列出题目")
    add_filters(sp)
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("show", help="看一道题（题面 + 追问链，不含答案）")
    sp.add_argument("id")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("reveal", help="看答案要点")
    sp.add_argument("id")
    sp.set_defaults(func=cmd_reveal)

    sp = sub.add_parser("draw", help="随机抽题")
    add_filters(sp)
    sp.add_argument("-n", type=int, default=3, help="抽几题，默认 3")
    sp.add_argument("--unseen", action="store_true", help="只抽没做过的")
    sp.add_argument("--weak", action="store_true", help="只抽含糊/不会的")
    sp.add_argument("--seed", type=int, help="固定随机种子，便于复现")
    sp.set_defaults(func=cmd_draw)

    sp = sub.add_parser("mark", help="标记掌握度")
    sp.add_argument("id")
    sp.add_argument("status", choices=["solid", "shaky", "miss"])
    sp.set_defaults(func=cmd_mark)

    sp = sub.add_parser("stats", help="按周统计掌握度")
    sp.set_defaults(func=cmd_stats)

    sp = sub.add_parser("review", help="列出需要复习的题")
    sp.set_defaults(func=cmd_review)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    questions = load_questions()
    args.func(args, questions)


if __name__ == "__main__":
    main()
