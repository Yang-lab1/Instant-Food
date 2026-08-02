import { createElement } from "./dom.js";
import { applyLegacyVisualUnification } from "./visual-unification.js";

function decodeName(value) {
  return decodeURIComponent(value);
}

const fileToRoute = new Map([
  [decodeName("%E5%BC%95%E5%AF%BC%E9%A1%B51.html"), "/onboarding/1"],
  [decodeName("%E5%BC%95%E5%AF%BC%E9%A1%B52.html"), "/onboarding/2"],
  [decodeName("%E5%BC%95%E5%AF%BC%E9%A1%B53.html"), "/onboarding/3"],
  [decodeName("%E8%BA%AB%E4%BB%BD%E9%AA%8C%E8%AF%81.html"), "/auth"],
  ["Nexus.html", "/nexus"],
  [decodeName("%E7%A4%BE%E5%8C%BA.html"), "/community"],
  [decodeName("%E6%8B%8D%E6%91%84.html"), "/capture"],
  [decodeName("%E9%A3%8E%E5%91%B3%E6%A1%A3%E6%A1%88%E9%A6%86.html"), "/archive"],
  [decodeName("%E7%AD%96%E5%B1%95%E4%BA%BA%E8%AE%BE%E7%BD%AE.html"), "/settings"],
  [decodeName("%E5%88%86%E5%AD%90%E9%87%8D%E6%9E%84%E5%8F%B0.html"), "/workbench"],
  [decodeName("%E5%8A%A0%E8%BD%BD%E8%BF%87%E6%B8%A1.html"), "/generation"],
  [decodeName("%E8%89%BA%E6%9C%AF%E7%9A%84%E8%AF%9E%E7%94%9F.html"), "/result"]
]);

const loadedLinks = new Set();
const loadedScripts = new Map();
const tailwindCompatPageIds = new Set(["archive", "settings", "workbench", "result"]);
const appBaseUrl = new URL(import.meta.env.BASE_URL || "./", window.location.href);
const demoGenerationImage = resolveLegacyAssetUrl("../../assets/backgrounds/cd6773b8370a4aeb11f456bd974ed96c.jpg");
const legacyRemoteImageFallback = resolveLegacyAssetUrl("../../assets/backgrounds/95dc01ddadd7c54292be548b216e61d8.jpg");
const beijingTimeZone = "Asia/Shanghai";

function normalizeAssetUrl(value) {
  if (!value) {
    return "";
  }

  if (
    value.startsWith("http://") ||
    value.startsWith("https://") ||
    value.startsWith("data:") ||
    value.startsWith("blob:")
  ) {
    return value;
  }

  if (value.startsWith("/")) {
    return new URL(value.replace(/^\/+/, ""), appBaseUrl).toString();
  }

  return new URL(`runtime-pages/${value}`, appBaseUrl).toString();
}

export function resolveLegacyAssetUrl(value) {
  const rawValue = String(value || "").trim();
  if (!rawValue) {
    return "";
  }

  if (
    rawValue.startsWith("http://") ||
    rawValue.startsWith("https://") ||
    rawValue.startsWith("data:") ||
    rawValue.startsWith("blob:")
  ) {
    return rawValue;
  }

  const cleaned = rawValue.replace(/^(\.\/)?(\.\.\/)+/, "").replace(/^\.\//, "");
  return new URL(cleaned.replace(/^\/+/, ""), appBaseUrl).toString();
}

function rewriteLegacyAssetText(value) {
  return String(value || "").replace(/((?:\.\.\/)+assets\/[^)"'\s]+)/g, (match) => resolveLegacyAssetUrl(match));
}

function rewriteLegacyAssetReferences(root) {
  root.querySelectorAll("[src], [poster]").forEach((node) => {
    ["src", "poster"].forEach((attribute) => {
      const value = node.getAttribute(attribute);
      if (value && value.includes("assets/")) {
        node.setAttribute(attribute, resolveLegacyAssetUrl(value));
      }
    });
  });

  root.querySelectorAll("[style]").forEach((node) => {
    const value = node.getAttribute("style") || "";
    if (value.includes("assets/")) {
      node.setAttribute("style", rewriteLegacyAssetText(value));
    }
  });

  root.querySelectorAll("style").forEach((styleNode) => {
    if (styleNode.textContent && styleNode.textContent.includes("assets/")) {
      styleNode.textContent = rewriteLegacyAssetText(styleNode.textContent);
    }
  });
}

function installLegacyImageFallbacks(root) {
  root.querySelectorAll("img").forEach((image) => {
    const originalSrc = image.getAttribute("src") || "";
    if (!originalSrc.includes("lh3.googleusercontent.com")) {
      return;
    }

    const applyFallback = () => {
      if (image.src !== legacyRemoteImageFallback) {
        image.src = legacyRemoteImageFallback;
      }
    };

    image.addEventListener("error", applyFallback);
    if (image.complete && image.naturalWidth === 0) {
      applyFallback();
    }
  });
}

function isMaterialIconFontUsable() {
  if (!document.body) {
    return false;
  }

  const probe = document.createElement("span");
  probe.className = "material-symbols-outlined";
  probe.textContent = "arrow_back_ios_new";
  probe.setAttribute("aria-hidden", "true");
  Object.assign(probe.style, {
    position: "fixed",
    left: "-9999px",
    top: "-9999px",
    display: "inline-block",
    fontSize: "20px",
    lineHeight: "1",
    visibility: "hidden"
  });
  document.body.append(probe);
  const width = probe.getBoundingClientRect().width;
  probe.remove();

  return width > 0 && width < 48;
}

function installMaterialIconGuard(root) {
  if (!root.querySelector(".material-symbols-outlined, .material-icons")) {
    return () => {};
  }

  let disposed = false;
  const html = document.documentElement;
  html.dataset.p2IconFont = "loading";

  const settle = () => {
    if (disposed) {
      return;
    }

    if (isMaterialIconFontUsable()) {
      if (html.dataset.p2IconFont === "loading" || html.dataset.p2IconFont === "unavailable") {
        delete html.dataset.p2IconFont;
      }
      return;
    }

    html.dataset.p2IconFont = "unavailable";
  };

  const timers = [
    window.setTimeout(settle, 120),
    window.setTimeout(settle, 800)
  ];

  if (document.fonts?.ready) {
    document.fonts.ready.then(settle).catch(settle);
  }

  return () => {
    disposed = true;
    timers.forEach((timer) => window.clearTimeout(timer));
  };
}

function getBeijingDateParts() {
  const now = new Date();
  const time = new Intl.DateTimeFormat("en-GB", {
    timeZone: beijingTimeZone,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    hourCycle: "h23"
  }).format(now);
  const weekday = new Intl.DateTimeFormat("zh-CN", {
    timeZone: beijingTimeZone,
    weekday: "short"
  }).format(now);
  const month = new Intl.DateTimeFormat("zh-CN", {
    timeZone: beijingTimeZone,
    month: "numeric"
  })
    .format(now)
    .replace(/\D/g, "");
  const day = new Intl.DateTimeFormat("zh-CN", {
    timeZone: beijingTimeZone,
    day: "numeric"
  })
    .format(now)
    .replace(/\D/g, "");

  return {
    time,
    date: `${weekday}\uff0c${month} \u6708 ${day} \u65e5`
  };
}

function updateBeijingClock(root) {
  const { time, date } = getBeijingDateParts();
  root.querySelectorAll("span").forEach((node) => {
    const text = (node.textContent || "").trim();
    const isStatusTime = /^\d{1,2}:\d{2}$/.test(text);
    const isStatusScope = node.closest(".status-bar, .status, .auth-status-bar, .h-12");
    if (isStatusTime && isStatusScope) {
      node.textContent = time;
    }
  });

  root.querySelectorAll(".topbar-copy p").forEach((node) => {
    const text = (node.textContent || "").trim();
    if (/^\S+\uff0c?\d+\s*\u6708\s*\d+\s*\u65e5$/.test(text)) {
      node.textContent = date;
    }
  });
}

function installBeijingClock(root) {
  updateBeijingClock(root);
  const interval = window.setInterval(() => updateBeijingClock(root), 30_000);
  return () => window.clearInterval(interval);
}

function ensureLink(href) {
  const normalizedHref = normalizeAssetUrl(href);
  if (!normalizedHref || loadedLinks.has(normalizedHref)) {
    return;
  }

  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = normalizedHref;
  link.dataset.legacyAsset = normalizedHref;
  document.head.append(link);
  loadedLinks.add(normalizedHref);
}

function ensureScript(src) {
  const normalizedSrc = normalizeAssetUrl(src);
  if (!normalizedSrc) {
    return Promise.resolve();
  }

  if (loadedScripts.has(normalizedSrc)) {
    return loadedScripts.get(normalizedSrc);
  }

  const promise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = normalizedSrc;
    script.async = false;
    script.dataset.legacyAsset = normalizedSrc;
    script.addEventListener(
      "load",
      () => {
        if (normalizedSrc.endsWith("/runtime-pages/instant-food-api-bridge.js")) {
          installInstantFoodDemoFallback();
        }
        resolve();
      },
      { once: true }
    );
    script.addEventListener("error", reject, { once: true });
    document.head.append(script);
  });

  loadedScripts.set(normalizedSrc, promise);
  return promise;
}

function createDemoGenerationResult() {
  return {
    title: "扇贝失控现场",
    summary: "焦香主角、干净留白和一点鲜绿色，把普通食材压成一盘可发布的成品。",
    imageUrl: demoGenerationImage,
    boardPreview: demoGenerationImage,
    recognition: {
      cooking_method: "煎封"
    },
    recipe: {
      title_zh: "黄油焦香扇贝盘",
      description: "用高温快速定色，保留中心的柔软口感，最后用绿色点缀收住盘面。",
      tips: "先把盘面留白想清楚，再下主菜，避免所有配料堆在同一侧。",
      ingredients: [
        { name: "扇贝", count: 6, unit: "颗" },
        { name: "黄油", count: 12, unit: "克" },
        { name: "香草", count: 1, unit: "小把" }
      ]
    },
    steps: [
      {
        title: "冷盘打底",
        duration_minutes: 2,
        temperature: "低温",
        visual_cue: "盘面保持干净留白",
        plating: "主菜预留偏心位置",
        instruction: "先擦干盘面和扇贝表面，把装饰食材切到同一尺寸。"
      },
      {
        title: "热锅定色",
        duration_minutes: 4,
        temperature: "190°C",
        visual_cue: "边缘浅榛色",
        plating: "扇贝沿弧线排布",
        instruction: "黄油起泡后放入扇贝，两面快速煎到焦香但中心不发硬。"
      },
      {
        title: "偏心收尾",
        duration_minutes: 1,
        temperature: "离火",
        visual_cue: "绿色点缀压住油光",
        plating: "盘边留白",
        instruction: "把主菜放到偏心位置，最后加香草和少量锅底黄油。"
      }
    ]
  };
}

function createDemoSelection() {
  return {
    ingredients: [
      { name: "扇贝", count: 6, unit: "颗", included: true },
      { name: "黄油", count: 12, unit: "克", included: true },
      { name: "香草", count: 1, unit: "小把", included: true }
    ],
    technique: "煎封",
    tastes: ["焦香", "清爽"],
    tools: ["平底锅", "白瓷盘"]
  };
}

function installInstantFoodDemoFallback() {
  const bridge = window.InstantFoodApiBridge;
  if (!bridge || bridge.__miroDemoFallbackInstalled) {
    return;
  }

  const originalFetchJson = typeof bridge.fetchJson === "function" ? bridge.fetchJson.bind(bridge) : null;
  const originalReadSelection = typeof bridge.readSelection === "function" ? bridge.readSelection.bind(bridge) : null;

  if (originalReadSelection) {
    bridge.readSelection = (view) => {
      const selection = originalReadSelection(view);
      const apiBase = typeof bridge.getApiBaseUrl === "function" ? bridge.getApiBaseUrl(view || window) : "";
      const routeHash = String((view || window).location?.hash || "");
      return selection || (!apiBase && routeHash === "#/generation" ? createDemoSelection() : null);
    };
  }

  bridge.fetchJson = async (url, options) => {
    const apiBase = typeof bridge.getApiBaseUrl === "function" ? bridge.getApiBaseUrl(window) : "";
    const target = String(url || "");
    if (!apiBase && target.includes("/api/v1/generate/")) {
      const result = createDemoGenerationResult(options);
      if (typeof bridge.writeGenerationResult === "function") {
        bridge.writeGenerationResult(result, window);
      }
      return result;
    }

    if (originalFetchJson) {
      return originalFetchJson(url, options);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  };

  bridge.__miroDemoFallbackInstalled = true;
}

function patchScript(code) {
  return rewriteLegacyAssetText(String(code || ""))
    .replace(
      /window\.parent\.postMessage\(\s*\{\s*type:\s*["']stage2-route["']\s*,\s*route:\s*([^}]+?)\s*\}\s*,\s*["']\*["']\s*\);/g,
      "window.__MIRO_ROUTE__($1);"
    )
    .replace(/window\.location\.replace\(\s*([^)]+?)\s*\);/g, "window.__MIRO_SET_LOCATION__($1);")
    .replace(/window\.location\.href\s*=\s*([^;]+);/g, "window.__MIRO_SET_LOCATION__($1);")
    .replace(/(^|[^.\w])location\.href\s*=\s*([^;]+);/g, "$1window.__MIRO_SET_LOCATION__($2);");
}

export function resolveRouteTarget(target) {
  const cleaned = String(target || "").trim().replace(/^['"]|['"]$/g, "");
  if (!cleaned) {
    return "";
  }

  if (fileToRoute.has(cleaned)) {
    return fileToRoute.get(cleaned);
  }

  const basename = cleaned.split("/").pop() || "";
  return fileToRoute.get(decodeURIComponent(basename)) || "";
}

function navigateTarget(target, router) {
  const cleaned = String(target || "").trim().replace(/^['"]|['"]$/g, "");
  const route = resolveRouteTarget(cleaned);
  if (route) {
    router.navigate(route);
    return;
  }

  if (!cleaned || cleaned === "#") {
    return;
  }

  window.location.href = cleaned;
}

function rewriteAnchors(root, router) {
  root.querySelectorAll("a[href]").forEach((anchor) => {
    const href = anchor.getAttribute("href") || "";
    const route = resolveRouteTarget(href);
    if (!route) {
      return;
    }

    anchor.setAttribute("href", `#${route}`);
    anchor.addEventListener("click", (event) => {
      event.preventDefault();
      router.navigate(route);
    });
  });
}

function bindLegacyNavigation(router) {
  const previousRoute = window.__MIRO_ROUTE__;
  const previousLocation = window.__MIRO_SET_LOCATION__;

  window.__MIRO_ROUTE__ = (target) => navigateTarget(target, router);
  window.__MIRO_SET_LOCATION__ = (target) => navigateTarget(target, router);

  return () => {
    if (typeof previousRoute === "undefined") {
      delete window.__MIRO_ROUTE__;
    } else {
      window.__MIRO_ROUTE__ = previousRoute;
    }

    if (typeof previousLocation === "undefined") {
      delete window.__MIRO_SET_LOCATION__;
    } else {
      window.__MIRO_SET_LOCATION__ = previousLocation;
    }
  };
}

function trackGlobals() {
  const timers = [];
  const intervals = [];
  const observers = [];
  const windowListeners = [];
  const documentListeners = [];

  const originalWindowAdd = window.addEventListener.bind(window);
  const originalDocumentAdd = document.addEventListener.bind(document);
  const originalSetTimeout = window.setTimeout.bind(window);
  const originalSetInterval = window.setInterval.bind(window);
  const OriginalMutationObserver = window.MutationObserver;

  window.addEventListener = (type, listener, options) => {
    windowListeners.push([type, listener, options]);
    return originalWindowAdd(type, listener, options);
  };

  document.addEventListener = (type, listener, options) => {
    documentListeners.push([type, listener, options]);
    return originalDocumentAdd(type, listener, options);
  };

  window.setTimeout = (handler, timeout, ...args) => {
    const id = originalSetTimeout(handler, timeout, ...args);
    timers.push(id);
    return id;
  };

  window.setInterval = (handler, timeout, ...args) => {
    const id = originalSetInterval(handler, timeout, ...args);
    intervals.push(id);
    return id;
  };

  window.MutationObserver = class extends OriginalMutationObserver {
    constructor(callback) {
      super(callback);
      observers.push(this);
    }
  };

  function restore() {
    window.addEventListener = originalWindowAdd;
    document.addEventListener = originalDocumentAdd;
    window.setTimeout = originalSetTimeout;
    window.setInterval = originalSetInterval;
    window.MutationObserver = OriginalMutationObserver;
  }

  return {
    restore,
    dispose() {
      restore();
      windowListeners.forEach(([type, listener, options]) => {
        window.removeEventListener(type, listener, options);
      });
      documentListeners.forEach(([type, listener, options]) => {
        document.removeEventListener(type, listener, options);
      });
      timers.forEach((id) => window.clearTimeout(id));
      intervals.forEach((id) => window.clearInterval(id));
      observers.forEach((observer) => observer.disconnect());
    }
  };
}

function getTemplateScripts(html) {
  const parser = new DOMParser();
  const normalizedHtml = String(html || "").replace(/^\uFEFF/, "");
  const documentNode = parser.parseFromString(normalizedHtml, "text/html");
  return [
    ...Array.from(documentNode.head.querySelectorAll("script")),
    ...Array.from(documentNode.body.querySelectorAll("script"))
  ];
}

function shouldSkipTailwindScript(root, scriptNode) {
  const pageId = root?.dataset?.pageId || "";
  if (!tailwindCompatPageIds.has(pageId)) {
    return false;
  }

  const src = scriptNode.getAttribute("src") || "";
  if (src.includes("cdn.tailwindcss.com")) {
    return true;
  }

  return /^\s*tailwind\.config\s*=/.test(scriptNode.textContent || "");
}

async function runScriptNodes(
  scriptNodes,
  { router, shouldRunScript = () => true, isDisposed = () => false, onCleanup = () => {} }
) {
  for (let index = 0; index < scriptNodes.length; index += 1) {
    const scriptNode = scriptNodes[index];
    if (isDisposed()) {
      return;
    }
    if (!shouldRunScript(scriptNode, index)) {
      continue;
    }

    const src = scriptNode.getAttribute("src");
    if (src) {
      await ensureScript(src);
      continue;
    }

    const tracker = trackGlobals();
    try {
      new Function(patchScript(scriptNode.textContent || ""))();
    } finally {
      tracker.restore();
      onCleanup(() => tracker.dispose());
    }
  }
}

export function mountTemplateScripts(root, { html, router, shouldRunScript }) {
  const cleanup = [];
  let disposed = false;
  const scriptNodes = getTemplateScripts(html);
  cleanup.push(bindLegacyNavigation(router));

  queueMicrotask(() => {
    void runScriptNodes(scriptNodes, {
      router,
      shouldRunScript: (scriptNode, index) => {
        if (shouldSkipTailwindScript(root, scriptNode)) {
          return false;
        }
        return typeof shouldRunScript === "function" ? shouldRunScript(scriptNode, index) : true;
      },
      isDisposed: () => disposed,
      onCleanup(dispose) {
        cleanup.push(dispose);
      }
    });
  });

  return () => {
    disposed = true;
    while (cleanup.length) {
      const dispose = cleanup.pop();
      dispose();
    }
  };
}

function mountLegacyPage(root, { path, html, router, runScripts = true, onMount }) {
  const parser = new DOMParser();
  const normalizedHtml = String(html || "").replace(/^\uFEFF/, "");
  const documentNode = parser.parseFromString(normalizedHtml, "text/html");
  const cleanup = [];
  let disposed = false;
  let onMountFrame = 0;
  cleanup.push(bindLegacyNavigation(router));

  const previousHtmlClass = document.documentElement.className;
  const previousBodyClass = document.body.className;
  const previousBodyRuntime = document.body.dataset.p2Runtime;
  const previousBodyPageId = document.body.dataset.p2PageId;
  document.documentElement.className = documentNode.documentElement.className;
  document.body.className = documentNode.body.className;
  document.body.dataset.p2Runtime = "true";
  document.body.dataset.p2PageId = path.replace(/^\//, "").replace(/\//g, "-");
  cleanup.push(() => {
    document.documentElement.className = previousHtmlClass;
    document.body.className = previousBodyClass;
    if (typeof previousBodyRuntime === "undefined") {
      delete document.body.dataset.p2Runtime;
    } else {
      document.body.dataset.p2Runtime = previousBodyRuntime;
    }
    if (typeof previousBodyPageId === "undefined") {
      delete document.body.dataset.p2PageId;
    } else {
      document.body.dataset.p2PageId = previousBodyPageId;
    }
  });

  documentNode.head.querySelectorAll('link[rel="stylesheet"][href]').forEach((link) => {
    ensureLink(link.getAttribute("href") || "");
  });

  root.replaceChildren();

  documentNode.head.querySelectorAll("style").forEach((styleNode) => {
    const style = document.createElement("style");
    style.textContent = styleNode.textContent || "";
    root.append(style);
  });

  Array.from(documentNode.body.childNodes).forEach((node) => {
    if (node.nodeType === Node.ELEMENT_NODE && node.tagName.toLowerCase() === "script") {
      return;
    }
    root.append(document.importNode(node, true));
  });

  rewriteLegacyAssetReferences(root);
  installLegacyImageFallbacks(root);
  cleanup.push(installMaterialIconGuard(root));
  applyLegacyVisualUnification(root, { path });
  cleanup.push(installBeijingClock(root));
  rewriteAnchors(root, router);

  root.__miroDispose = () => {
    disposed = true;
    if (onMountFrame) {
      window.cancelAnimationFrame(onMountFrame);
    }
    while (cleanup.length) {
      const dispose = cleanup.pop();
      dispose();
    }
  };

  if (typeof onMount === "function") {
    onMountFrame = window.requestAnimationFrame(() => {
      onMountFrame = 0;
      if (disposed) {
        return;
      }

      const dispose = onMount(root, { router });
      if (typeof dispose === "function") {
        cleanup.push(dispose);
      }
    });
  }

  if (!runScripts) {
    return;
  }

  const pendingScripts = getTemplateScripts(html);

  queueMicrotask(() => {
    void runScriptNodes(pendingScripts, {
      router,
      isDisposed: () => disposed,
      onCleanup(dispose) {
        cleanup.push(dispose);
      }
    });
  });
}

export function createLegacyTemplateRoute({
  path,
  title,
  html,
  description = "",
  layout = "runtime",
  showTopBar = false,
  showBottomNav = false,
  runScripts = true,
  onMount
}) {
  return {
    path,
    title,
    description,
    layout,
    showTopBar,
    showBottomNav,
    render({ router }) {
      const root = createElement("section", {
        className: "legacy-inline-page",
        attributes: {
          "data-legacy-path": path
        }
      });

      void mountLegacyPage(root, { path, html, router, runScripts, onMount });

      return root;
    }
  };
}
