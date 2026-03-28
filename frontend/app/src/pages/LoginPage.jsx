import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function LoginPage({ userName, onLogin }) {
  const navigate = useNavigate();
  const [name, setName] = useState(userName || "");

  function handleSubmit(event) {
    event.preventDefault();
    const nextName = name.trim() || "本地体验用户";
    onLogin(nextName);
    navigate("/generate");
  }

  return (
    <section className="flow-page">
      <div className="flow-card auth-card">
        <p className="eyebrow">Step 1 / 3</p>
        <h1>登录拍立食</h1>
        <p className="flow-copy">
          先进入本地体验流程。这里先使用轻量登录占位，不拦你试核心功能。
        </p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            用户名
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="例如 Erzhuonie"
            />
          </label>
          <button type="submit">进入食材生成流程</button>
        </form>
      </div>
    </section>
  );
}
