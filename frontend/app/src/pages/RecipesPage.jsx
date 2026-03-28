import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchRecipes } from "../lib/api";

export function RecipesPage() {
  const [state, setState] = useState({
    loading: true,
    error: "",
    recipes: []
  });

  useEffect(() => {
    let alive = true;
    fetchRecipes()
      .then((payload) => {
        if (!alive) {
          return;
        }
        setState({
          loading: false,
          error: "",
          recipes: payload.recipes || []
        });
      })
      .catch((error) => {
        if (!alive) {
          return;
        }
        setState({
          loading: false,
          error: error.message,
          recipes: []
        });
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <section className="page-stack">
      <header className="hero-panel recipe-hero">
        <div className="hero-copy-block">
          <p className="eyebrow">Recipes</p>
          <h2>食谱列表</h2>
          <p className="hero-copy">
            从 Supabase 读取真实食谱数据，把原型里的“中枢主页 / 档案馆”氛围转成可运行的正式界面。
          </p>
          <div className="hero-chip-row">
            <span className="hero-chip">实时数据库</span>
            <span className="hero-chip">玻璃卡片</span>
            <span className="hero-chip">原型同风格</span>
          </div>
        </div>
        <div className="hero-side-stat">
          <strong>{state.recipes.length}</strong>
          <span>当前公开菜谱</span>
          <Link to="/capture" className="primary-link">
            去生成新食谱
          </Link>
        </div>
      </header>

      {state.loading ? <LoadingPanel label="正在加载食谱..." /> : null}
      {state.error ? (
        <MessagePanel
          variant="error"
          title="食谱列表加载失败"
          body={state.error}
        />
      ) : null}
      {!state.loading && !state.error && state.recipes.length === 0 ? (
        <MessagePanel
          variant="empty"
          title="还没有公开食谱"
          body="数据库已接通，但当前没有更多已发布内容。你可以先去“拍摄 / 生成”页试生成或保存一条。"
        />
      ) : null}

      <div className="recipe-grid">
        {state.recipes.map((recipe) => (
          <article key={recipe.id} className="recipe-card">
            <div className="recipe-card-media">
              <div className="recipe-card-media-overlay" />
              <span>{recipe.title_zh?.slice(0, 2) || "菜谱"}</span>
            </div>
            <div className="recipe-card-body">
              <div className="card-meta-row">
                <span>{recipe.cuisine_type || "未分类"}</span>
                <span>{recipe.difficulty || "medium"}</span>
              </div>
              <h3>{recipe.title_zh || recipe.title}</h3>
              <p>{recipe.description_zh || recipe.description || "暂无简介"}</p>
              <div className="recipe-card-tags">
                <span>{recipe.meal_type || "待分类"}</span>
                <span>{recipe.servings || 1} 人份</span>
              </div>
              <div className="card-footer">
                <span>{recipe.cook_time_minutes || 0} 分钟</span>
                <Link to={`/recipes/${recipe.id}`}>查看详情</Link>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function LoadingPanel({ label }) {
  return <div className="message-panel">{label}</div>;
}

function MessagePanel({ title, body, variant }) {
  return (
    <div className={`message-panel message-panel-${variant}`}>
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}
