import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { generateRecipe } from "../lib/api";

const defaultForm = {
  ingredients: "鸡蛋, 鸡蛋, 鸡蛋, 番茄, 番茄, 葱",
  cooking_technique: "炒",
  flavor_profile: "家常",
  spice_level: 1,
  max_time: 15,
  equipment: "炒锅, 锅铲"
};

export function TextGeneratePage({ userName, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const restoredForm = location.state?.draftForm;
  const [form, setForm] = useState(restoredForm || defaultForm);
  const [status, setStatus] = useState({ loading: false, error: "" });

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus({ loading: true, error: "" });
    try {
      const payload = await generateRecipe({
        ingredients: form.ingredients
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        cooking_technique: form.cooking_technique,
        flavor_profile: form.flavor_profile,
        spice_level: Number(form.spice_level),
        max_time: Number(form.max_time),
        equipment: form.equipment
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      });

      navigate(`/result/${payload.generation_log_id || "preview"}`, {
        state: {
          recipe: payload.recipe,
          generationLogId: payload.generation_log_id || null,
          draftForm: form
        }
      });
    } catch (error) {
      setStatus({ loading: false, error: error.message });
    }
  }

  return (
    <section className="flow-page">
      <div className="flow-card">
        <header className="flow-header">
          <div>
            <p className="eyebrow">Step 2 / 3</p>
            <h1>输入文字食材</h1>
            <p className="flow-copy">
              {userName}，这里会调用后端生成菜谱，并把结构化结果写入 Supabase 的
              `generation_logs`。
            </p>
          </div>
          <div className="flow-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={() => navigate("/login")}
            >
              返回登录
            </button>
            <button type="button" className="ghost-button" onClick={onLogout}>
              退出
            </button>
          </div>
        </header>

        <form className="text-generate-form" onSubmit={handleSubmit}>
          <label>
            食材
            <textarea
              rows={5}
              value={form.ingredients}
              onChange={(event) =>
                setForm({ ...form, ingredients: event.target.value })
              }
              placeholder="鸡蛋, 番茄, 葱"
            />
          </label>

          <div className="form-grid">
            <label>
              烹饪方式
              <input
                value={form.cooking_technique}
                onChange={(event) =>
                  setForm({ ...form, cooking_technique: event.target.value })
                }
              />
            </label>
            <label>
              风味
              <input
                value={form.flavor_profile}
                onChange={(event) =>
                  setForm({ ...form, flavor_profile: event.target.value })
                }
              />
            </label>
            <label>
              辣度
              <input
                type="number"
                min="1"
                max="5"
                value={form.spice_level}
                onChange={(event) =>
                  setForm({ ...form, spice_level: event.target.value })
                }
              />
            </label>
            <label>
              最长时长
              <input
                type="number"
                min="5"
                max="180"
                value={form.max_time}
                onChange={(event) =>
                  setForm({ ...form, max_time: event.target.value })
                }
              />
            </label>
          </div>

          <label>
            厨具
            <input
              value={form.equipment}
              onChange={(event) =>
                setForm({ ...form, equipment: event.target.value })
              }
            />
          </label>

          {status.error ? (
            <div className="message-panel message-panel-error">
              <strong>生成失败</strong>
              <p>{status.error}</p>
            </div>
          ) : null}

          <div className="button-row">
            <button type="submit" disabled={status.loading}>
              {status.loading ? "生成中..." : "生成菜谱与流程"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}
