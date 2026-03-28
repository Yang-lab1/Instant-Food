const API_BASE_URL = "http://127.0.0.1:8011/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "string"
        ? payload
        : payload?.detail || payload?.message || "请求失败";
    throw new Error(message);
  }

  return payload;
}

export function fetchRecipes() {
  return request("/recipes?limit=24");
}

export function fetchRecipe(recipeId) {
  return request(`/recipes/${recipeId}`);
}

export function fetchAiStatus() {
  return request("/ai/status");
}

export function generateRecipe(input) {
  return request("/generate/recipe", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function generateDishImage(input) {
  return request("/generate/image", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function fetchGenerationLog(logId) {
  return request(`/generation-logs/${logId}`);
}

export function generateFromImage(input) {
  return request("/generate/from-image", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function saveRecipe(input) {
  return request("/recipes", {
    method: "POST",
    body: JSON.stringify(input)
  });
}
