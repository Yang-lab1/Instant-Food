import time

from config import settings
from supabase import create_client


def with_retry(fn, attempts=4, delay=0.2):
    last_error = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if i == attempts - 1:
                raise
            time.sleep(delay * (i + 1))
    raise last_error


def main():
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    recipes = with_retry(
        lambda: client.table("recipes").select("id,title,title_zh,metadata,source").range(0, 999).execute().data or []
    )
    existing_by_source_id = {}
    for recipe in recipes:
        metadata = recipe.get("metadata") or {}
        source_recipe_id = metadata.get("source_recipe_id")
        if source_recipe_id:
            existing_by_source_id[source_recipe_id] = recipe

    training_rows = with_retry(
        lambda: (
            client.table("ai_training_data")
            .select("id,recipe_id,expected_output,metadata")
            .range(0, 999)
            .execute()
            .data
            or []
        )
    )

    created = 0
    linked = 0

    for row in training_rows:
        if row.get("recipe_id"):
            continue

        metadata = row.get("metadata") or {}
        source_recipe_id = metadata.get("source_recipe_id")
        dish_name = metadata.get("dish_name") or row.get("expected_output") or "Imported Recipe"

        recipe = existing_by_source_id.get(source_recipe_id)
        if recipe is None:
            recipe_payload = {
                "title": dish_name,
                "title_zh": dish_name,
                "description": "Imported from recipe retrieval training corpus.",
                "description_zh": "从食谱检索训练语料导入。",
                "difficulty": "medium",
                "prep_time_minutes": 0,
                "cook_time_minutes": 0,
                "servings": 1,
                "is_published": False,
                "is_ai_generated": False,
                "source": "imported",
                "metadata": {
                    "source_recipe_id": source_recipe_id,
                    "import_type": metadata.get("import_type"),
                    "source_file": metadata.get("source_file"),
                    "linked_from": "ai_training_data",
                },
            }
            recipe_response = with_retry(lambda: client.table("recipes").insert(recipe_payload).execute())
            recipe = recipe_response.data[0]
            existing_by_source_id[source_recipe_id] = recipe
            created += 1

        with_retry(lambda: client.table("ai_training_data").update({"recipe_id": recipe["id"]}).eq("id", row["id"]).execute())
        linked += 1

    print(f"created_recipes={created}")
    print(f"linked_training_rows={linked}")


if __name__ == "__main__":
    main()
