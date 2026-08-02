export function createRouter({ routes, defaultPath, onRouteChange }) {
  const knownPaths = new Set(routes.map((route) => route.path));
  const fallbackPath = knownPaths.has(defaultPath) ? defaultPath : routes[0]?.path || "/";

  function normalizeHash(hash) {
    const raw = String(hash || "").replace(/^#/, "").trim();
    if (!raw) {
      return fallbackPath;
    }

    const path = raw.startsWith("/") ? raw : `/${raw}`;
    return knownPaths.has(path) ? path : fallbackPath;
  }

  function navigate(path) {
    const nextPath = knownPaths.has(path) ? path : fallbackPath;
    const nextHash = `#${nextPath}`;
    if (window.location.hash !== nextHash) {
      window.location.hash = nextHash;
      return;
    }
    onRouteChange(nextPath);
  }

  function handleHashChange() {
    onRouteChange(normalizeHash(window.location.hash));
  }

  return {
    start() {
      window.addEventListener("hashchange", handleHashChange);
      if (!window.location.hash) {
        window.location.hash = `#${fallbackPath}`;
        return;
      }
      handleHashChange();
    },
    navigate
  };
}
