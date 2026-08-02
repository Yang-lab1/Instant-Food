import { createBottomNav } from "./bottom-nav.js";
import { createTopBar } from "./top-bar.js";
import { clearNode, createElement } from "../../utils/dom.js";

export function createAppShell({ appName, routes }) {
  const root = createElement("div", { className: "miro-app-shell" });
  const topBar = createTopBar(appName);
  const content = createElement("main", {
    className: "miro-app-content",
    attributes: {
      id: "miro-app-content"
    }
  });
  const bottomNav = createBottomNav(routes);
  let currentContent = null;

  root.append(topBar.root, content, bottomNav.root);

  function clearContent() {
    if (currentContent && typeof currentContent.__miroDispose === "function") {
      currentContent.__miroDispose();
    }
    clearNode(content);
    currentContent = null;
  }

  return {
    root,
    clearContent,
    setLayout(layout) {
      root.dataset.layout = layout || "default";
    },
    setChrome({ showTopBar = true, showBottomNav = true }) {
      root.dataset.showTopBar = showTopBar ? "true" : "false";
      root.dataset.showBottomNav = showBottomNav ? "true" : "false";
    },
    setHeader(title, description) {
      topBar.setRouteMeta(title, description);
    },
    setContent(nextContent) {
      clearContent();
      content.append(nextContent);
      currentContent = nextContent;
    },
    setActiveRoute(path) {
      bottomNav.setActive(path);
    }
  };
}
