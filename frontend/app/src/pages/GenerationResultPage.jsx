import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { fetchGenerationLog, generateDishImage } from "../lib/api";

export function GenerationResultPage({ userName, onLogout }) {
  const { logId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [state, setState] = useState({
    loading: logId !== "preview",
    error: "",
    log: null,
    recipe: location.state?.recipe || null,
    imageGenerating: false,
    generatedImage: "",
    generatedImageUrl: ""
  });

  const draftForm = location.state?.draftForm || null;

  useEffect(() => {
    if (!logId || logId === "preview") {
      return;
    }

    let alive = true;
    fetchGenerationLog(logId)
      .then((payload) => {
        if (!alive) {
          return;
        }
        setState((current) => ({
          ...current,
          loading: false,
          error: "",
          log: payload.log || null,
          recipe: payload.log?.generated_recipe || current.recipe
        }));
      })
      .catch((error) => {
        if (!alive) {
          return;
        }
        setState((current) => ({
          ...current,
          loading: false,
          error: error.message
        }));
      });

    return () => {
      alive = false;
    };
  }, [logId]);

  async function handleGenerateImage() {
    if (!recipe) {
      return;
    }
    setState((current) => ({
      ...current,
      imageGenerating: true,
      error: ""
    }));
    try {
      const payload = await generateDishImage({
        recipe_title: recipe.title_zh || recipe.title,
        recipe_description: recipe.description,
        ingredients: (recipe.ingredients || []).map((item) => item.name),
        generation_log_id: state.log?.id || null
      });
      const image = payload.image;
      const dataUrl = `data:${image.mime_type};base64,${image.image_base64}`;
      setState((current) => ({
        ...current,
        imageGenerating: false,
        generatedImage: dataUrl,
        generatedImageUrl: payload.image_url || ""
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        imageGenerating: false,
        error: error.message
      }));
    }
  }

  const recipe = state.recipe;
  const ingredientAtlas = state.log?.ingredient_atlas || [];
  const teachingSteps = state.log?.teaching_steps || [];
  const teachingSummary = state.log?.teaching_summary || [];
  const flowDescription = buildFlowDescription(
    state.log?.teaching_text,
    teachingSteps,
    recipe?.steps || []
  );

  return (
    <section className="flow-page">
      <div className="flow-card">
        <header className="flow-header">
          <div>
            <p className="eyebrow">Step 3 / 3</p>
            <h1>生成结果与操作流程</h1>
            <p className="flow-copy">
              {userName}，这里展示后端返回的菜谱结果，并支持把菜品正式记录到核心表。
            </p>
          </div>
          <div className="flow-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={() => navigate("/generate", { state: { draftForm } })}
            >
              返回材料输入
            </button>
            <button type="button" className="ghost-button" onClick={onLogout}>
              退出
            </button>
          </div>
        </header>

        {state.loading ? <div className="message-panel">正在读取生成记录...</div> : null}
        {state.error ? (
          <div className="message-panel message-panel-error">
            <strong>结果加载失败</strong>
            <p>{state.error}</p>
          </div>
        ) : null}
        {state.log?.id ? (
          <div className="message-panel message-panel-success">
            <strong>generation_logs 已记录</strong>
            <p>当前生成结果已经自动写入 generation_logs 核心表，日志 ID: {state.log.id}</p>
          </div>
        ) : null}

        {recipe ? (
          <div className="page-stack">
            <section className="detail-panel">
              <div className="result-head">
                <div>
                  <p className="eyebrow">Recipe</p>
                  <h2>{recipe.title_zh || recipe.title}</h2>
                  <p>{recipe.description}</p>
                </div>
                <div className="flow-actions">
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={handleGenerateImage}
                    disabled={state.imageGenerating}
                  >
                    {state.imageGenerating ? "生图中..." : "调用 Nano Banana 生图"}
                  </button>
                  <button type="button" disabled>
                    已存入 generation_logs 库
                  </button>
                </div>
              </div>
            </section>

            {state.generatedImage ? (
              <section className="detail-panel">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Gemini Image</p>
                    <h3>菜品示意图</h3>
                  </div>
                </div>
                <img
                  src={state.generatedImageUrl || state.generatedImage}
                  alt={recipe.title_zh || recipe.title}
                  className="generated-dish-image"
                />
                {state.generatedImageUrl ? (
                  <p className="flow-copy">图片已上传到 Supabase Storage 并回写到 generation_logs。</p>
                ) : null}
              </section>
            ) : null}

            {ingredientAtlas.length ? (
              <section className="detail-panel ingredient-atlas-panel">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Atlas</p>
                    <h3>备菜清单与食材说明</h3>
                  </div>
                </div>
                <div className="ingredient-atlas-grid">
                  {ingredientAtlas.map((item, index) => (
                    <article key={`${item.name}-${index}`} className="ingredient-atlas-card">
                      <div className="ingredient-atlas-top">
                        <span className="ingredient-atlas-index">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        <span className="ingredient-atlas-amount">{item.amount}</span>
                      </div>
                      <strong>{item.name}</strong>
                      <p>{item.intro}</p>
                      <div className="atlas-chip-row">
                        <span>{item.role}</span>
                        <span>{item.action}</span>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}

            <div className="detail-columns">
              <section className="detail-panel">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Checklist</p>
                    <h3>菜谱清单</h3>
                  </div>
                </div>
                <ul className="list-block">
                  {(recipe.ingredients || []).map((item, index) => (
                    <li key={`${item.name}-${index}`}>
                      <span>{item.name}</span>
                      <span>
                        {item.quantity}
                        {item.unit || ""}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>

              <section className="detail-panel">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Flow</p>
                    <h3>操作流程</h3>
                  </div>
                </div>
                <div className="flow-table-wrap">
                  <table className="flow-table">
                    <thead>
                      <tr>
                        <th>食材输入</th>
                        <th>操作流程说明</th>
                        <th>补充提示</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{(recipe.ingredients || []).map((item) => item.name).join("、") || "当前食材"}</td>
                        <td>
                          <strong>AI 生成操作流程</strong>
                          <p>{flowDescription}</p>
                        </td>
                        <td>
                          {state.log?.teaching_text
                            ? "说明已同步写入 generation_logs，可直接用于后续回查。"
                            : "当前按生成结果自动整理为一段可执行的操作说明。"}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            {teachingSummary.length ? (
              <section className="detail-panel teaching-summary-panel">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">Summary</p>
                    <h3>本次生成摘要</h3>
                  </div>
                </div>
                <div className="summary-grid">
                  {teachingSummary.map((item, index) => (
                    <article key={`${item.label}-${index}`} className="summary-card">
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </article>
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function buildFlowDescription(teachingText, teachingSteps, recipeSteps) {
  if (teachingText) {
    return teachingText;
  }

  const sourceSteps = teachingSteps.length
    ? teachingSteps
    : recipeSteps.map((step) => ({
        instruction: step.instruction,
        tip: step.tips || ""
      }));

  if (!sourceSteps.length) {
    return "根据当前食材进行清洗、切配、预处理，再按火候依次下锅、调味和收尾即可。";
  }

  return sourceSteps
    .map((step, index) => {
      const instruction = step.instruction || "";
      const tip = step.tip || step.tips || "";
      return `第${index + 1}步：${instruction}${tip ? `（提示：${tip}）` : ""}`;
    })
    .join(" ");
}
