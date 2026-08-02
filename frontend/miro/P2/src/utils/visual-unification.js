const PAGE_IDS = new Set([
  "onboarding-1",
  "onboarding-2",
  "onboarding-3",
  "auth",
  "nexus",
  "community",
  "capture",
  "archive",
  "settings",
  "workbench",
  "generation",
  "result"
]);

const TOPBAR_SELECTORS = [
  ".camera-topbar",
  ".archive-topbar",
  ".settings-topbar",
  ".workbench-topbar",
  ".loading-topbar",
  ".result-topbar",
  ".topbar"
];

const STATUS_SELECTORS = [
  ".status-bar",
  ".status",
  ".auth-status-bar"
];

const ICON_BUTTON_SELECTORS = [
  ".icon",
  ".icon-button",
  ".auth-icon-circle",
  ".archive-icon-btn",
  ".settings-icon-button",
  ".settings-topbar > a",
  ".settings-topbar > button",
  ".workbench-topbar > a",
  ".workbench-topbar > button",
  ".result-topbar > button",
  ".topbar > a",
  ".topbar > button"
];

const TOPBAR_ICON_SELECTORS = [
  ".p2-unified-icon-button .material-symbols-outlined",
  ".p2-unified-icon-button .material-icons"
];

const CARD_SELECTORS = [
  ".auth-login-sheet",
  ".auth-brand-badge",
  ".auth-capsule-menu",
  ".panel",
  ".card",
  ".sheet",
  ".task-card",
  ".mini-link-card",
  ".archive-card",
  ".stat-card",
  ".teaser",
  ".cat",
  ".stat",
  ".detail-box",
  ".decision-sheet",
  ".market",
  ".settings-list",
  ".settings-balance-card",
  ".settings-kpi-card",
  ".liquid-glass",
  ".ingredient-card",
  ".stage-frame",
  ".recipe-step-content",
  ".result-fallback-card",
  ".masonry-item",
  ".gallery-panel",
  ".camera-fallback",
  ".upload-tile",
  ".stack-tile"
];

const CHIP_SELECTORS = [
  ".hero-tab",
  ".cat",
  ".chip",
  ".score",
  ".tag",
  ".meta-chip",
  ".settings-member-chip",
  ".selection-chip",
  ".archive-filter",
  ".gallery-pill",
  ".button",
  ".mode-pill",
  ".recipe-step-chip"
];

const CTA_SELECTORS = [
  ".auth-button-primary",
  ".cta",
  ".direct",
  ".settings-recharge-link",
  "#startGenerateButton",
  "#bottomConfirm",
  ".button-primary",
  ".absolute.bottom-0 button"
];

const DOCK_SELECTORS = [
  ".bottom-dock",
  ".dock",
  "nav.bottom-dock"
];

const NAV_ITEM_SELECTORS = [
  ".bottom-nav-item",
  ".nav-item"
];

const TYPE_SELECTOR_GROUPS = [
  {
    selectors: [
      ".camera-topbar h1",
      ".archive-topbar h1",
      ".settings-topbar h1",
      ".workbench-topbar h1",
      ".loading-topbar h1",
      ".result-topbar h1",
      ".topbar .title h1"
    ],
    className: "p2-type-page-title"
  },
  {
    selectors: [
      ".section-head h2",
      ".section-head h3",
      ".settings-group-title",
      ".detail-box small"
    ],
    className: "p2-type-section-title"
  },
  {
    selectors: [
      ".settings-row-title",
      ".archive-copy h4",
      ".task-feature-content h3",
      ".task-mini-content h3",
      ".copy h4"
    ],
    className: "p2-type-row-title"
  },
  {
    selectors: [
      ".settings-row-subtitle",
      ".settings-row-side",
      ".section-link",
      ".archive-copy p",
      ".task-feature-content p",
      ".task-mini-content p",
      ".copy p"
    ],
    className: "p2-type-row-meta"
  },
  {
    selectors: [
      ".hero-tab",
      ".archive-filter",
      ".selection-chip",
      ".meta-chip",
      ".tag",
      ".score",
      ".chip",
      ".cat strong",
      ".mode-pill",
      ".gallery-pill"
    ],
    className: "p2-type-control-sm"
  },
  {
    selectors: [
      ".p2-unified-cta",
      ".direct",
      ".secondary",
      ".settings-recharge-link",
      "#startGenerateButton",
      "#confirmCaptureButton"
    ],
    className: "p2-type-cta"
  }
];

function pathToPageId(path) {
  return String(path || "").replace(/^\//, "").replace(/\//g, "-");
}

function addClass(root, selectors, className) {
  root.querySelectorAll(selectors.join(", ")).forEach((node) => {
    node.classList.add(className);
  });
}

function normalizeTopbarIcons(root) {
  root.querySelectorAll(TOPBAR_ICON_SELECTORS.join(", ")).forEach((node) => {
    const iconName = (node.textContent || "").trim();
    if (iconName === "arrow_back_ios") {
      node.textContent = "arrow_back_ios_new";
      node.dataset.p2NormalizedIcon = "true";
    }
  });
}

export function applyLegacyVisualUnification(root, { path }) {
  const pageId = pathToPageId(path);
  root.dataset.pageId = pageId;

  if (!PAGE_IDS.has(pageId)) {
    return;
  }

  root.classList.add("p2-legacy-page", `p2-page-${pageId}`);

  const deviceShell = root.querySelector(".nexus-shell-device, .device, .phone-shell");
  if (deviceShell) {
    deviceShell.classList.add("p2-device-shell");
  }

  const deviceScreen =
    deviceShell?.querySelector(".nexus-shell-screen, .screen, .phone-screen, .auth-screen") ||
    root.querySelector(".nexus-shell-screen, .screen, .phone-screen, .auth-screen");
  if (deviceScreen) {
    deviceScreen.classList.add("p2-device-screen");
  }

  addClass(root, TOPBAR_SELECTORS, "p2-unified-topbar");
  addClass(root, STATUS_SELECTORS, "p2-unified-status");
  addClass(root, ICON_BUTTON_SELECTORS, "p2-unified-icon-button");
  normalizeTopbarIcons(root);
  addClass(root, CARD_SELECTORS, "p2-unified-card");
  addClass(root, CHIP_SELECTORS, "p2-unified-chip");
  addClass(root, CTA_SELECTORS, "p2-unified-cta");
  addClass(root, DOCK_SELECTORS, "p2-unified-dock");
  addClass(root, NAV_ITEM_SELECTORS, "p2-unified-nav-item");
  TYPE_SELECTOR_GROUPS.forEach(({ selectors, className }) => addClass(root, selectors, className));
}
