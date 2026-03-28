import { Navigate, Route, Routes } from "react-router-dom";
import { useMemo, useState } from "react";
import { GenerationResultPage } from "./pages/GenerationResultPage";
import { LoginPage } from "./pages/LoginPage";
import { TextGeneratePage } from "./pages/TextGeneratePage";

const SESSION_KEY = "instant-food-user";

function readSessionUser() {
  if (typeof window === "undefined") {
    return "";
  }
  return window.sessionStorage.getItem(SESSION_KEY) || "";
}

export default function App() {
  const [userName, setUserName] = useState(readSessionUser);

  function handleLogin(nextName) {
    const safeName = nextName.trim();
    window.sessionStorage.setItem(SESSION_KEY, safeName);
    setUserName(safeName);
  }

  function handleLogout() {
    window.sessionStorage.removeItem(SESSION_KEY);
    setUserName("");
  }

  const authContext = useMemo(
    () => ({
      userName,
      handleLogin,
      handleLogout
    }),
    [userName]
  );

  return (
    <div className="flow-shell">
      <Routes>
        <Route
          path="/"
          element={<Navigate to={userName ? "/generate" : "/login"} replace />}
        />
        <Route
          path="/login"
          element={
            <LoginPage
              userName={authContext.userName}
              onLogin={authContext.handleLogin}
            />
          }
        />
        <Route
          path="/generate"
          element={
            userName ? (
              <TextGeneratePage
                userName={authContext.userName}
                onLogout={authContext.handleLogout}
              />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
        <Route
          path="/result/:logId"
          element={
            userName ? (
              <GenerationResultPage
                userName={authContext.userName}
                onLogout={authContext.handleLogout}
              />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </div>
  );
}
