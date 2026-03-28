import csv
import sys
import time
from pathlib import Path

from supabase import create_client

from config import settings


PROMPT_TEMPLATE = (
    "你是一名中餐食谱检索与生成助手。"
    "请优先基于提供的菜谱检索文本理解菜品名称、食材、口味、步骤和关键词，"
    "再输出结构化、准确且简洁的结果。"
)


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def load_rows(csv_path: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_recipe_id = (row.get("recipe_id") or "").strip()
            dish_name = (row.get("dish_name") or "").strip()
            retrieval_text = (row.get("retrieval_text") or "").strip()

            if not retrieval_text:
                continue

            rows.append(
                {
                    "recipe_id": None,
                    "prompt_template": PROMPT_TEMPLATE,
                    "input_description": retrieval_text,
                    "expected_output": dish_name or None,
                    "metadata": {
                        "source_recipe_id": source_recipe_id or None,
                        "dish_name": dish_name or None,
                        "source_file": str(csv_path),
                        "import_type": "recipe_retrieval_docs",
                    },
                    "quality_score": 0.8,
                    "usage_count": 0,
                    "is_validated": False,
                }
            )
    return rows


def main():
    if len(sys.argv) != 2:
        print("Usage: python import_ai_training_data.py <csv_path>")
        raise SystemExit(1)

    csv_path = Path(sys.argv[1]).expanduser().resolve()
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        raise SystemExit(1)

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    rows = load_rows(csv_path)

    if not rows:
        print("No rows to import.")
        return

    imported = 0
    for batch in chunked(rows, 10):
        try:
            client.table("ai_training_data").insert(batch).execute()
            imported += len(batch)
        except Exception:
            # Some network/proxy paths are flaky on larger payloads. Fall back to row-by-row.
            for row in batch:
                client.table("ai_training_data").insert(row).execute()
                imported += 1
                time.sleep(0.05)

    print(f"Imported {imported} rows from {csv_path}")


if __name__ == "__main__":
    main()
