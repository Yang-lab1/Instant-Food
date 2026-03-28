import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchRecipe } from "../lib/api";

export function RecipeDetailPage() {
  const { recipeId } = useParams();
  const [state, setState] = useState({
    loading: true,
    error: "",
    recipe: null
  });

  useEffect(() => {
    let alive = true;
    fetchRecipe(recipeId)
      .then((payload) => {
        if (!alive) {
          return;
        }
        setState({
          loading: false,
          error: "",
          recipe: payload.recipe || null
        });
      })
      .catch((error) => {
        if (!alive) {
          return;
        }
        setState({
          loading: false,
          error: error.message,
          recipe: null
        });
      });
    return () => {
      alive = false;
    };
  }, [recipeId]);

  if (state.loading) {
    return <div className="message-panel">正在加载食谱详情...</div>;
  }

  if (state.error) {
    return (
      <div className="page-stack">
        <Link to="/" className="secondary-link">
          返回列表
        </Link>
        <div className="message-panel message-panel-error">
          <strong>详情页加载失败</strong>
          <p>{state.error}</p>
        </div>
      </div>
    );
  }

  const recipe = state.recipe;

  return (
    <section className="page-stack">
      <header className="detail-hero detail-hero-rich">
        <div className="detail-hero-main">
          <Link to="/" className="secondary-link detail-back-link">
            返回食谱列表
          </Link>
          <p className="eyebrow">Recipe Detail</p>
          <h2>{recipe.title_zh || recipe.title}</h2>
          <p>{recipe.description_zh || recipe.description || "暂无简介"}</p>
          <div className="hero-chip-row">
            <span className="hero-chip">{recipe.cuisine_type || "未分类"}</span>
            <span className="hero-chip">{recipe.meal_type || "待分类"}</span>
            <span className="hero-chip">{recipe.calories_per_serving || "--"} kcal</span>
          </div>
        </div>
        <div className="detail-stats">
          <Stat label="难度" value={recipe.difficulty || "medium"} />
          <Stat
            label="时间"
            value={`${recipe.prep_time_minutes || 0} + ${recipe.cook_time_minutes || 0} 分钟`}
          />
          <Stat label="份量" value={`${recipe.servings || 1} 人份`} />
        </div>
      </header>

      <div className="detail-columns">
        <section className="detail-panel">
          <h3>食材</h3>
          <ul className="list-block">
            {(recipe.ingredients || []).map((item) => (
              <li key={item.id}>
                <span>{item.ingredient_name}</span>
                <span>
                  {item.quantity}
                  {item.unit}
                </span>
              </li>
            ))}
          </ul>
        </section>
        <section className="detail-panel">
          <h3>步骤</h3>
          <ol className="step-list">
            {(recipe.steps || []).map((step) => (
              <li key={step.id}>
                <strong>步骤 {step.step_number}</strong>
                <p>{step.instruction_zh || step.instruction}</p>
                {step.tips ? <span>提示：{step.tips}</span> : null}
              </li>
            ))}
          </ol>
        </section>
      </div>
    </section>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat-chip">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
