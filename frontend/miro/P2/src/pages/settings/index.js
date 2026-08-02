import template from "./template.html?raw";
import { createLegacyTemplateRoute, mountTemplateScripts } from "../../utils/legacy-page.js";

const labels = {
  flavor: "常做风味",
  excludes: "排除食材",
  nutrition: "营养目标",
  unset: "未设置",
  cancel: "取消",
  save: "保存",
  close: "关闭",
  dialog: "设置选择",
  nicknamePlaceholder: "未设置昵称",
  editNickname: "编辑昵称",
  nicknameInput: "输入昵称"
};

const SETTING_OPTIONS = {
  [labels.flavor]: {
    mode: "multi",
    options: ["焦香清爽", "酸辣", "鲜甜", "低脂", "热辣", "家常", "轻食"]
  },
  [labels.excludes]: {
    mode: "multi",
    options: ["香菜", "葱", "蒜", "姜", "辣椒", "洋葱", "青椒", "花椒"]
  },
  [labels.nutrition]: {
    mode: "multi",
    options: ["高蛋白", "低糖", "低盐", "控油", "增肌", "轻断食", "高纤维"]
  }
};

const PROFILE_STORAGE_KEY = "instantFoodProfileConstraints";
const PROFILE_SCHEMA_VERSION = 2;
const USER_PROFILE_STORAGE_KEY = "instantFoodUserProfile";
const USER_PROFILE_SCHEMA_VERSION = 1;
const EMPTY_IMAGE_DATA_URL = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";
const GENERATED_RECIPE_COUNT_KEY = "instantFoodGeneratedRecipeCount";
const SAVED_ARCHIVE_COUNT_KEY = "instantFoodSavedArchiveCount";

const SETTING_KEYS_BY_LABEL = {
  [labels.flavor]: "flavor",
  [labels.excludes]: "excludes",
  [labels.nutrition]: "nutrition"
};

const CONSTRAINT_SETTING_KEYS = ["flavor", "excludes", "nutrition"];
const KPI_LABELS = ["灵感菜谱", "归档记录", "风味准则"];

const DEFAULT_PROFILE_SETTINGS = {
  flavor: [],
  excludes: [],
  nutrition: []
};

function safeReadStorage(key) {
  try {
    return window.localStorage.getItem(key);
  } catch (error) {
    return null;
  }
}

function safeWriteStorage(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch (error) {}
}

function normalizeList(value) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || "").trim()).filter(Boolean);
  }

  return String(value || "")
    .split(/[，,、/]/)
    .map((item) => item.trim())
    .filter((item) => item && item !== labels.unset);
}

function buildGenerationConstraints(settings) {
  return {
    excludeIngredients: normalizeList(settings.excludes),
    nutritionGoals: normalizeList(settings.nutrition),
    flavorPreferences: normalizeList(settings.flavor)
  };
}

function normalizeProfile(rawProfile = {}) {
  const sourceSettings = rawProfile.version === PROFILE_SCHEMA_VERSION
    && rawProfile.settings
    && typeof rawProfile.settings === "object"
    ? rawProfile.settings
    : {};

  const settings = Object.fromEntries(
    Object.entries(DEFAULT_PROFILE_SETTINGS).map(([key, fallback]) => {
      const value = normalizeList(sourceSettings[key]);
      return [key, value.length ? value : fallback.slice()];
    })
  );

  return {
    version: PROFILE_SCHEMA_VERSION,
    updatedAt: rawProfile.updatedAt || new Date().toISOString(),
    settings,
    generationConstraints: buildGenerationConstraints(settings)
  };
}

function readProfile() {
  const raw = safeReadStorage(PROFILE_STORAGE_KEY);
  if (!raw) {
    return normalizeProfile({});
  }

  try {
    return normalizeProfile(JSON.parse(raw));
  } catch (error) {
    return normalizeProfile({});
  }
}

function writeProfile(profile) {
  const normalized = normalizeProfile({
    ...profile,
    updatedAt: new Date().toISOString()
  });
  safeWriteStorage(PROFILE_STORAGE_KEY, JSON.stringify(normalized));
  return normalized;
}

function isImageDataUrl(value) {
  return typeof value === "string" && /^data:image\//.test(value);
}

function normalizeUserProfile(rawProfile = {}) {
  const source = rawProfile && typeof rawProfile === "object" ? rawProfile : {};
  return {
    version: USER_PROFILE_SCHEMA_VERSION,
    updatedAt: source.updatedAt || new Date().toISOString(),
    displayName: String(source.displayName || "").trim().slice(0, 16),
    avatarDataUrl: isImageDataUrl(source.avatarDataUrl) ? source.avatarDataUrl : ""
  };
}

function readUserProfile() {
  const raw = safeReadStorage(USER_PROFILE_STORAGE_KEY);
  if (!raw) {
    return normalizeUserProfile({});
  }

  try {
    return normalizeUserProfile(JSON.parse(raw));
  } catch (error) {
    return normalizeUserProfile({});
  }
}

function writeUserProfile(profile) {
  const normalized = normalizeUserProfile({
    ...profile,
    updatedAt: new Date().toISOString()
  });
  safeWriteStorage(USER_PROFILE_STORAGE_KEY, JSON.stringify(normalized));
  return normalized;
}

function readImageFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    if (!file || !String(file.type || "").startsWith("image/")) {
      reject(new Error("Unsupported image file"));
      return;
    }

    const reader = new FileReader();
    reader.addEventListener("load", () => resolve(String(reader.result || "")));
    reader.addEventListener("error", () => reject(reader.error || new Error("Failed to read image")));
    reader.readAsDataURL(file);
  });
}

function hydrateUserProfile(root, profile) {
  const nameButton = root.querySelector("#settingsNameButton");
  const avatarImage = root.querySelector("#settingsAvatarImage");
  const avatarPlaceholder = root.querySelector("#settingsAvatarPlaceholder");

  if (nameButton) {
    if (profile.displayName) {
      nameButton.textContent = profile.displayName;
      nameButton.classList.remove("is-placeholder");
    } else {
      nameButton.textContent = labels.nicknamePlaceholder;
      nameButton.classList.add("is-placeholder");
    }
  }

  if (avatarImage && avatarPlaceholder) {
    if (profile.avatarDataUrl) {
      avatarImage.src = profile.avatarDataUrl;
      avatarImage.hidden = false;
      avatarPlaceholder.hidden = true;
    } else {
      avatarImage.src = EMPTY_IMAGE_DATA_URL;
      avatarImage.hidden = true;
      avatarPlaceholder.hidden = false;
    }
  }
}

function readCounter(key) {
  const value = Number.parseInt(safeReadStorage(key) || "0", 10);
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function countActiveConstraints(settings) {
  return CONSTRAINT_SETTING_KEYS.reduce((total, key) => total + normalizeList(settings[key]).length, 0);
}

function getSettingTitle(row) {
  return (row.querySelector(".settings-row-title")?.textContent || "").trim();
}

function getSettingValueNode(row) {
  const textNodes = Array.from(row.querySelectorAll(".settings-row-side > span")).filter(
    (node) => !node.classList.contains("material-symbols-outlined")
  );
  return textNodes[0] || null;
}

function hydrateSettingRows(root, profile) {
  root.querySelectorAll('a[href="#"]').forEach((row) => {
    const title = getSettingTitle(row);
    const key = SETTING_KEYS_BY_LABEL[title];
    const valueNode = key ? getSettingValueNode(row) : null;
    if (!valueNode) {
      return;
    }

    const values = normalizeList(profile.settings[key]);
    valueNode.textContent = values.length ? values.join("，") : labels.unset;
  });
}

function hydrateKpis(root, profile) {
  const cards = Array.from(root.querySelectorAll(".settings-kpi-card"));
  const values = [
    readCounter(GENERATED_RECIPE_COUNT_KEY),
    readCounter(SAVED_ARCHIVE_COUNT_KEY),
    countActiveConstraints(profile.settings)
  ];

  cards.forEach((card, index) => {
    const valueNode = card.querySelector("strong");
    const labelNode = card.querySelector("span");
    if (valueNode) {
      valueNode.textContent = String(values[index] || 0);
    }
    if (labelNode && KPI_LABELS[index]) {
      labelNode.textContent = KPI_LABELS[index];
    }
  });
}

function parseSelectedValue(value) {
  return normalizeList(value);
}

function installSettingsPickerStyles() {
  if (document.getElementById("p2-settings-picker-style")) {
    return () => {};
  }

  const style = document.createElement("style");
  style.id = "p2-settings-picker-style";
  style.textContent = `
    .p2-settings-picker {
      position: fixed !important;
      left: 20px;
      top: 20px;
      z-index: 1000;
      width: min(300px, calc(100vw - 40px));
      max-height: calc(100dvh - 36px);
      overflow: hidden;
      border-radius: 22px;
      border: 1px solid rgba(142, 182, 155, 0.18);
      background:
        radial-gradient(circle at 86% 0%, rgba(35, 83, 71, 0.28), rgba(35, 83, 71, 0) 42%),
        linear-gradient(180deg, rgba(22, 22, 24, 0.98), rgba(7, 7, 8, 0.98));
      box-shadow: 0 22px 52px rgba(0, 0, 0, 0.46), inset 0 1px 0 rgba(255, 255, 255, 0.07);
      backdrop-filter: blur(22px);
      -webkit-backdrop-filter: blur(22px);
      padding: 12px;
      opacity: 0;
      pointer-events: none;
      transform: translateY(-4px) scale(0.985);
      transform-origin: top right;
      transition: opacity 160ms cubic-bezier(0.2, 0.8, 0.2, 1), transform 160ms cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    .p2-settings-picker.is-open {
      opacity: 1;
      pointer-events: auto;
      transform: translateY(0) scale(1);
    }
    .p2-settings-picker-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .p2-settings-picker-title {
      margin: 0;
      color: #ffffff;
      font-size: var(--miro-type-row-title-size);
      line-height: var(--miro-type-row-title-line);
      font-weight: var(--miro-font-weight-heavy);
    }
    .p2-settings-picker-close {
      width: 30px;
      height: 30px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 999px;
      color: rgba(255, 255, 255, 0.72);
      background: rgba(255, 255, 255, 0.05);
      font-size: var(--miro-type-icon-chevron-size);
      line-height: var(--miro-type-icon-line);
    }
    .p2-settings-picker-options {
      display: grid;
      grid-template-columns: 1fr;
      gap: 7px;
      margin: 0 0 10px;
      max-height: min(260px, calc(100dvh - 166px));
      overflow-y: auto;
      overscroll-behavior: contain;
      scrollbar-width: none;
      -webkit-overflow-scrolling: touch;
    }
    .p2-settings-picker-options::-webkit-scrollbar {
      display: none;
    }
    .p2-settings-picker-option {
      min-height: 42px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 15px;
      padding: 0 12px;
      color: rgba(255, 255, 255, 0.72);
      background: rgba(255, 255, 255, 0.035);
      font-size: var(--miro-type-control-size);
      line-height: var(--miro-type-control-line);
      font-weight: var(--miro-font-weight-semibold);
      text-align: left;
    }
    .p2-settings-picker-option.is-selected {
      color: #ffffff;
      background: rgba(35, 83, 71, 0.5);
      border-color: rgba(142, 182, 155, 0.36);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }
    .p2-settings-picker-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .p2-settings-picker-action {
      min-height: 40px;
      border: 0;
      border-radius: 14px;
      font-size: var(--miro-type-chip-size);
      line-height: var(--miro-type-chip-line);
      font-weight: var(--miro-font-weight-bold);
    }
    .p2-settings-picker-cancel {
      color: rgba(255, 255, 255, 0.7);
      background: rgba(255, 255, 255, 0.06);
    }
    .p2-settings-picker-confirm {
      color: #fff;
      background: linear-gradient(180deg, rgba(142, 182, 155, 0.96), rgba(35, 83, 71, 0.98));
      box-shadow: 0 10px 22px rgba(35, 83, 71, 0.28);
    }
    .p2-profile-editor {
      position: fixed;
      inset: 0;
      z-index: 1100;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: rgba(0, 0, 0, 0.42);
      opacity: 0;
      pointer-events: none;
      transition: opacity 160ms cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    .p2-profile-editor.is-open {
      opacity: 1;
      pointer-events: auto;
    }
    .p2-profile-editor-card {
      width: min(292px, calc(100vw - 48px));
      border-radius: 24px;
      border: 1px solid rgba(142, 182, 155, 0.18);
      background:
        radial-gradient(circle at 86% 0%, rgba(35, 83, 71, 0.28), rgba(35, 83, 71, 0) 42%),
        linear-gradient(180deg, rgba(22, 22, 24, 0.98), rgba(7, 7, 8, 0.98));
      box-shadow: 0 22px 52px rgba(0, 0, 0, 0.46), inset 0 1px 0 rgba(255, 255, 255, 0.07);
      padding: 16px;
      transform: translateY(8px) scale(0.98);
      transition: transform 160ms cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    .p2-profile-editor.is-open .p2-profile-editor-card {
      transform: translateY(0) scale(1);
    }
    .p2-profile-editor-title {
      margin: 0 0 12px;
      color: #ffffff;
      font-size: var(--miro-type-row-title-size);
      line-height: var(--miro-type-row-title-line);
      font-weight: var(--miro-font-weight-heavy);
    }
    .p2-profile-editor-input {
      width: 100%;
      height: 46px;
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      outline: none;
      padding: 0 12px;
      color: #ffffff;
      background: rgba(255, 255, 255, 0.055);
      font-size: var(--miro-type-body-size);
      line-height: var(--miro-type-body-line);
      font-weight: var(--miro-font-weight-semibold);
    }
    .p2-profile-editor-input:focus {
      border-color: rgba(142, 182, 155, 0.42);
      box-shadow: 0 0 0 3px rgba(35, 83, 71, 0.18);
    }
    .p2-profile-editor-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 12px;
    }
    .p2-profile-editor-action {
      height: 40px;
      border: 0;
      border-radius: 14px;
      font-size: var(--miro-type-chip-size);
      line-height: var(--miro-type-chip-line);
      font-weight: var(--miro-font-weight-bold);
    }
    .p2-profile-editor-cancel {
      color: rgba(255, 255, 255, 0.7);
      background: rgba(255, 255, 255, 0.06);
    }
    .p2-profile-editor-save {
      color: #fff;
      background: linear-gradient(180deg, rgba(142, 182, 155, 0.96), rgba(35, 83, 71, 0.98));
    }
  `;
  document.head.append(style);
  return () => style.remove();
}

function createSettingsPicker({ onSave } = {}) {
  const picker = document.createElement("div");
  picker.className = "p2-settings-picker";
  picker.setAttribute("role", "dialog");
  picker.setAttribute("aria-modal", "false");
  picker.setAttribute("aria-hidden", "true");
  picker.setAttribute("aria-label", labels.dialog);
  picker.innerHTML = `
    <div class="p2-settings-picker-head">
      <h3 class="p2-settings-picker-title"></h3>
      <button class="p2-settings-picker-close" type="button" aria-label="${labels.close}">&times;</button>
    </div>
    <div class="p2-settings-picker-options"></div>
    <div class="p2-settings-picker-actions">
      <button class="p2-settings-picker-action p2-settings-picker-cancel" type="button">${labels.cancel}</button>
      <button class="p2-settings-picker-action p2-settings-picker-confirm" type="button">${labels.save}</button>
    </div>
  `;
  document.body.append(picker);

  const titleNode = picker.querySelector(".p2-settings-picker-title");
  const optionsNode = picker.querySelector(".p2-settings-picker-options");
  const closeButtons = picker.querySelectorAll(".p2-settings-picker-close, .p2-settings-picker-cancel");
  const confirmButton = picker.querySelector(".p2-settings-picker-confirm");
  let activeRow = null;
  let activeConfig = null;
  let selected = new Set();

  const close = () => {
    picker.classList.remove("is-open");
    picker.setAttribute("aria-hidden", "true");
    activeRow = null;
    activeConfig = null;
    selected = new Set();
  };

  const renderOptions = () => {
    optionsNode.replaceChildren(
      ...activeConfig.options.map((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `p2-settings-picker-option${selected.has(option) ? " is-selected" : ""}`;
        button.textContent = option;
        button.addEventListener("click", () => {
          if (activeConfig.mode === "single") {
            selected = new Set([option]);
          } else if (selected.has(option)) {
            selected.delete(option);
          } else {
            selected.add(option);
          }
          renderOptions();
        });
        return button;
      })
    );
  };

  const positionPanel = (row) => {
    const rowRect = row.getBoundingClientRect();
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 414;
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 896;
    const panelWidth = Math.min(300, Math.max(240, viewportWidth - 40));
    const left = Math.min(Math.max(20, rowRect.right - panelWidth), Math.max(20, viewportWidth - panelWidth - 20));

    picker.style.width = `${panelWidth}px`;
    picker.style.left = `${left}px`;
    picker.style.top = "18px";
    picker.style.visibility = "hidden";
    picker.classList.add("is-open");
    const panelHeight = Math.min(picker.offsetHeight || 292, viewportHeight - 36);
    picker.classList.remove("is-open");
    picker.style.visibility = "";

    const belowTop = rowRect.bottom + 8;
    const aboveTop = rowRect.top - panelHeight - 8;
    const top = belowTop + panelHeight <= viewportHeight - 18
      ? belowTop
      : Math.max(18, Math.min(aboveTop, viewportHeight - panelHeight - 18));
    picker.style.top = `${top}px`;
  };

  const open = (row, title, config) => {
    activeRow = row;
    activeConfig = config;
    const valueNode = getSettingValueNode(row);
    selected = new Set(parseSelectedValue(valueNode?.textContent || ""));
    titleNode.textContent = title;
    renderOptions();
    positionPanel(row);
    picker.setAttribute("aria-hidden", "false");
    picker.classList.add("is-open");
  };

  const handleDocumentPointerDown = (event) => {
    if (!picker.classList.contains("is-open")) {
      return;
    }
    if (picker.contains(event.target) || activeRow?.contains(event.target)) {
      return;
    }
    close();
  };

  closeButtons.forEach((button) => button.addEventListener("click", close));
  picker.addEventListener("pointerdown", (event) => event.stopPropagation());
  document.addEventListener("pointerdown", handleDocumentPointerDown, true);
  confirmButton.addEventListener("click", () => {
    if (!activeRow || !activeConfig) {
      close();
      return;
    }
    const valueNode = getSettingValueNode(activeRow);
    if (valueNode) {
      const values = Array.from(selected);
      valueNode.textContent = values.length ? values.join("，") : labels.unset;
      if (typeof onSave === "function") {
        onSave(activeRow, getSettingTitle(activeRow), values);
      }
    }
    close();
  });

  close();
  return {
    open,
    node: picker,
    dispose: () => document.removeEventListener("pointerdown", handleDocumentPointerDown, true)
  };
}

function createNicknameEditor({ onSave } = {}) {
  const editor = document.createElement("div");
  editor.className = "p2-profile-editor";
  editor.setAttribute("role", "dialog");
  editor.setAttribute("aria-modal", "true");
  editor.setAttribute("aria-hidden", "true");
  editor.setAttribute("aria-label", labels.editNickname);
  editor.innerHTML = `
    <div class="p2-profile-editor-card">
      <h3 class="p2-profile-editor-title">${labels.editNickname}</h3>
      <input class="p2-profile-editor-input" type="text" maxlength="16" autocomplete="off" placeholder="${labels.nicknameInput}">
      <div class="p2-profile-editor-actions">
        <button class="p2-profile-editor-action p2-profile-editor-cancel" type="button">${labels.cancel}</button>
        <button class="p2-profile-editor-action p2-profile-editor-save" type="button">${labels.save}</button>
      </div>
    </div>
  `;
  document.body.append(editor);

  const input = editor.querySelector(".p2-profile-editor-input");
  const cancelButton = editor.querySelector(".p2-profile-editor-cancel");
  const saveButton = editor.querySelector(".p2-profile-editor-save");

  const close = () => {
    editor.classList.remove("is-open");
    editor.setAttribute("aria-hidden", "true");
  };

  const save = () => {
    if (typeof onSave === "function") {
      onSave(String(input?.value || "").trim());
    }
    close();
  };

  const open = (currentName = "") => {
    if (input) {
      input.value = currentName || "";
    }
    editor.setAttribute("aria-hidden", "false");
    editor.classList.add("is-open");
    window.setTimeout(() => input?.focus(), 0);
  };

  const handleBackdrop = (event) => {
    if (event.target === editor) {
      close();
    }
  };

  const handleKeydown = (event) => {
    if (event.key === "Escape") {
      close();
    }
    if (event.key === "Enter") {
      save();
    }
  };

  editor.addEventListener("pointerdown", handleBackdrop);
  input?.addEventListener("keydown", handleKeydown);
  cancelButton?.addEventListener("click", close);
  saveButton?.addEventListener("click", save);
  close();

  return {
    open,
    node: editor,
    dispose: () => {
      editor.removeEventListener("pointerdown", handleBackdrop);
      input?.removeEventListener("keydown", handleKeydown);
    }
  };
}

function bindSettings(root, { router }) {
  const cleanup = [];
  const disposeScripts = mountTemplateScripts(root, { html: template, router });
  if (typeof disposeScripts === "function") {
    cleanup.push(disposeScripts);
  }
  cleanup.push(installSettingsPickerStyles());

  let profile = writeProfile(readProfile());
  hydrateSettingRows(root, profile);
  hydrateKpis(root, profile);

  let userProfile = writeUserProfile(readUserProfile());
  hydrateUserProfile(root, userProfile);

  const nicknameEditor = createNicknameEditor({
    onSave(value) {
      userProfile = writeUserProfile({
        ...readUserProfile(),
        displayName: value
      });
      hydrateUserProfile(root, userProfile);
    }
  });
  cleanup.push(() => {
    nicknameEditor.dispose();
    nicknameEditor.node.remove();
  });

  const nameButton = root.querySelector("#settingsNameButton");
  const avatarButton = root.querySelector("#settingsAvatarButton");
  const avatarInput = root.querySelector("#settingsAvatarInput");

  const handleNameClick = (event) => {
    event.preventDefault();
    nicknameEditor.open(readUserProfile().displayName);
  };

  const handleAvatarClick = (event) => {
    event.preventDefault();
    avatarInput?.click();
  };

  const handleAvatarChange = async (event) => {
    const file = event.target?.files?.[0];
    if (!file) {
      return;
    }

    try {
      const avatarDataUrl = await readImageFileAsDataUrl(file);
      userProfile = writeUserProfile({
        ...readUserProfile(),
        avatarDataUrl
      });
      hydrateUserProfile(root, userProfile);
    } catch (error) {
      console.warn("Failed to update avatar image", error);
    } finally {
      if (event.target) {
        event.target.value = "";
      }
    }
  };

  nameButton?.addEventListener("click", handleNameClick);
  avatarButton?.addEventListener("click", handleAvatarClick);
  avatarInput?.addEventListener("change", handleAvatarChange);
  cleanup.push(() => {
    nameButton?.removeEventListener("click", handleNameClick);
    avatarButton?.removeEventListener("click", handleAvatarClick);
    avatarInput?.removeEventListener("change", handleAvatarChange);
  });

  const picker = createSettingsPicker({
    onSave(row, title, values) {
      const key = SETTING_KEYS_BY_LABEL[title];
      if (!key) {
        return;
      }

      profile = readProfile();
      profile.settings[key] = values;
      profile = writeProfile(profile);
      hydrateSettingRows(root, profile);
      hydrateKpis(root, profile);
    }
  });
  cleanup.push(() => {
    picker.dispose();
    picker.node.remove();
  });

  root.querySelectorAll('a[href="#"]').forEach((row) => {
    const title = getSettingTitle(row);
    const config = SETTING_OPTIONS[title];

    const handleClick = (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (typeof event.stopImmediatePropagation === "function") {
        event.stopImmediatePropagation();
      }

      if (config) {
        picker.open(row, title, config);
      }
    };

    row.addEventListener("click", handleClick, true);
    cleanup.push(() => row.removeEventListener("click", handleClick, true));
  });

  return () => {
    while (cleanup.length) {
      cleanup.pop()();
    }
  };
}

const subpageStyle = `
  :root {
    color-scheme: dark;
    --bg: #000000;
    --text: #ffffff;
    --muted: rgba(255,255,255,.54);
    --line: rgba(255,255,255,.09);
    --line-soft: rgba(255,255,255,.055);
    --green: #235347;
    --accent: #8EB69B;
    --font: var(--miro-font-body);
  }
  *{box-sizing:border-box}
  html,body{margin:0;min-height:100%;font-family:var(--font);}
  body.nexus-shell-body{display:flex!important;justify-content:center;align-items:flex-start!important;padding:20px;overflow:auto!important;background:radial-gradient(circle at 15% 8%,rgba(35,83,71,.34) 0%,rgba(35,83,71,0) 30%),radial-gradient(circle at 86% 10%,rgba(142,182,155,.14) 0%,rgba(142,182,155,0) 24%),linear-gradient(180deg,#050505 0%,#000 100%)!important;color:var(--text);-webkit-font-smoothing:antialiased;}
  a{color:inherit;text-decoration:none}
  .material-symbols-outlined{font-family:var(--miro-font-icon);font-weight:var(--miro-font-weight-regular);font-style:normal;font-size:var(--miro-type-icon-size);line-height:var(--miro-type-icon-line);display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;-webkit-font-smoothing:antialiased;font-variation-settings:"FILL" 0,"wght" 400,"GRAD" 0,"opsz" 24;}
  .nexus-shell-device{position:relative;width:min(100%,414px);height:min(calc(100vh - 40px),844px);max-height:min(calc(100vh - 40px),844px);border-radius:40px;overflow:hidden;background:linear-gradient(180deg,rgba(28,28,30,.92) 0%,rgba(0,0,0,.98) 100%),#000;border:1px solid rgba(255,255,255,.06);box-shadow:0 30px 60px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.06);isolation:isolate;}
  .nexus-shell-device::before{content:"";position:absolute;width:220px;height:220px;top:72px;right:-70px;border-radius:50%;background:rgba(35,83,71,.24);filter:blur(72px);pointer-events:none;z-index:0;}
  .nexus-shell-device::after{content:"";position:absolute;width:250px;height:250px;bottom:132px;left:-96px;border-radius:50%;background:rgba(142,182,155,.1);filter:blur(72px);pointer-events:none;z-index:0;}
  .nexus-shell-screen{position:relative;z-index:1;height:100%;overflow-y:auto;overflow-x:hidden;scrollbar-width:none;-webkit-overflow-scrolling:touch;overscroll-behavior-y:contain;}
  .nexus-shell-screen::-webkit-scrollbar{display:none;}
  .sub-topbar{height:72px;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:20;background:linear-gradient(180deg,rgba(0,0,0,.92) 20%,rgba(0,0,0,.62) 100%);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border-bottom:1px solid rgba(255,255,255,.045);}
  .sub-topbar h1{margin:0;color:#fff;font-size:var(--miro-type-page-title-size);line-height:var(--miro-type-page-title-line);font-weight:var(--miro-font-weight-heavy);letter-spacing:-.02em;}
  .sub-icon{width:44px;height:44px;border:1px solid rgba(255,255,255,.1);border-radius:20px;display:inline-flex;align-items:center;justify-content:center;background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.025)),rgba(12,12,12,.8);color:#fff;text-decoration:none;box-shadow:inset 0 1px 0 rgba(255,255,255,.06);}
  .sub-icon .material-symbols-outlined{font-size:var(--miro-type-icon-button-size);}
  .sub-main{padding:18px 20px 42px;}
  .sub-tabs{display:grid;grid-template-columns:1fr 1fr;margin:0 0 20px;border-radius:24px;background:rgba(255,255,255,.045);border:1px solid var(--line);padding:4px;}
  .sub-tab{position:relative;min-height:42px;border-radius:20px;display:flex;align-items:center;justify-content:center;color:var(--muted);text-decoration:none;font-size:var(--miro-type-tab-size);line-height:var(--miro-type-tab-line);font-weight:var(--miro-font-weight-bold);}
  .sub-tab.active{color:#fff;background:rgba(35,83,71,.42);border:1px solid rgba(142,182,155,.18);}
  .sub-list{overflow:hidden;border-radius:26px;background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.022)),rgba(10,10,10,.82);border:1px solid var(--line);box-shadow:0 14px 34px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.035);}
  .sub-row{min-height:66px;padding:0 16px;display:flex;align-items:center;justify-content:space-between;gap:14px;color:#fff;text-decoration:none;border-bottom:1px solid var(--line-soft);}
  .sub-row:last-child{border-bottom:0;}
  .sub-row strong{font-size:var(--miro-type-row-title-size);line-height:var(--miro-type-row-title-line);font-weight:var(--miro-font-weight-bold);letter-spacing:-.02em;}
  .sub-row span{color:var(--muted);font-size:var(--miro-type-row-meta-size);line-height:var(--miro-type-row-meta-line);font-weight:var(--miro-font-weight-semibold);}
  .sub-row .material-symbols-outlined{color:rgba(255,255,255,.42);font-size:var(--miro-type-icon-chevron-size);}
  .sub-card{position:relative;overflow:hidden;border-radius:28px;padding:22px;background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.022)),rgba(10,10,10,.82);border:1px solid var(--line);box-shadow:0 14px 34px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.035);margin-bottom:18px;}
  .sub-card::after{content:"";position:absolute;right:-56px;top:-56px;width:150px;height:150px;border-radius:999px;background:rgba(35,83,71,.18);filter:blur(10px);pointer-events:none;}
  .sub-card h2{position:relative;z-index:1;margin:0 0 10px;color:#fff;font-size:var(--miro-type-card-title-size);line-height:var(--miro-type-card-title-line);font-weight:var(--miro-font-weight-bold);letter-spacing:-.04em;}
  .sub-card p{position:relative;z-index:1;margin:0 0 12px;color:rgba(255,255,255,.64);font-size:var(--miro-type-body-size);line-height:var(--miro-type-body-line);font-weight:var(--miro-font-weight-semibold);}
  .sub-card p:last-child{margin-bottom:0;}
  .sub-amount{position:relative;z-index:1;color:#fff;font-size:var(--miro-type-sub-amount-size);font-weight:var(--miro-font-weight-heavy);letter-spacing:-.06em;line-height:var(--miro-type-sub-amount-line);margin:16px 0;}
  .sub-button{position:relative;z-index:1;min-height:48px;border-radius:999px;background:linear-gradient(180deg,rgba(142,182,155,.96),rgba(35,83,71,.98));color:#fff;text-decoration:none;display:flex;align-items:center;justify-content:center;font-size:var(--miro-type-tab-size);line-height:var(--miro-type-tab-line);font-weight:var(--miro-font-weight-bold);margin-top:16px;box-shadow:0 10px 22px rgba(35,83,71,.28);}
  @media (max-width:480px){body.nexus-shell-body{padding:0}.nexus-shell-device{width:100%;height:100dvh;max-height:none;border-radius:0;border:0;box-shadow:none}}
`;

function pageShell({ title, parent = "/settings", content }) {
  return `<!DOCTYPE html><html lang="zh-CN"><head>
    <meta charset="utf-8">
    <meta content="width=device-width, initial-scale=1.0" name="viewport">
    <title>拍立食 | ${title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet">
    <style>${subpageStyle}</style>
  </head>
  <body class="nexus-shell-body">
    <div class="nexus-shell-device"><div class="nexus-shell-screen">
      <header class="sub-topbar">
        <a class="sub-icon" href="#${parent}" aria-label="返回"><span class="material-symbols-outlined">arrow_back_ios_new</span></a>
        <h1>${title}</h1>
        <button class="sub-icon" type="button" aria-label="更多"><span class="material-symbols-outlined">more_horiz</span></button>
      </header>
      <main class="sub-main">${content}</main>
    </div></div>
  </body></html>`;
}

function row(title, href, subtitle = "") {
  return `<a class="sub-row" href="#${href}"><div><strong>${title}</strong>${subtitle ? `<br><span>${subtitle}</span>` : ""}</div><span class="material-symbols-outlined">chevron_right</span></a>`;
}

function detailCard(title, paragraphs, extra = "") {
  return `<section class="sub-card"><h2>${title}</h2>${paragraphs.map((item) => `<p>${item}</p>`).join("")}${extra}</section>`;
}

function createSubpageRoute(path, title, parent, content) {
  return createLegacyTemplateRoute({
    path,
    title,
    html: pageShell({ title, parent, content }),
    runScripts: false
  });
}

export const settingsPage = createLegacyTemplateRoute({
  path: "/settings",
  title: "Settings",
  html: template,
  runScripts: false,
  onMount: bindSettings
});

export const settingsRoutes = [
  settingsPage,
  createSubpageRoute(
    "/settings/account",
    "账户服务",
    "/settings",
    `<div class="sub-list">
      ${row("余额与充值", "/settings/recharge", "查看余额、充值入口与消费记录")}
      ${row("会员方案", "/settings/membership", "月卡、季卡与权益说明")}
      ${row("联系客服", "/settings/customer-service", "反馈问题或咨询服务")}
    </div>`
  ),
  createSubpageRoute(
    "/settings/recharge",
    "余额与充值",
    "/settings/account",
    `${detailCard("拍立食余额", ["余额用于后续解锁高级生成、会员增值能力或模板服务。当前版本未接入真实支付，因此余额保持为演示状态。"], `<div class="sub-amount">¥0.00</div><a class="sub-button" href="#/settings/membership">查看会员方案</a>`)}
    <div class="sub-list">${row("充值记录", "/settings/recharge/history", "暂无真实交易记录")}</div>`
  ),
  createSubpageRoute(
    "/settings/recharge/history",
    "充值记录",
    "/settings/recharge",
    detailCard("暂无充值记录", ["正式接入微信支付后，这里会展示充值时间、金额、支付状态与退款状态。"])
  ),
  createSubpageRoute(
    "/settings/membership",
    "会员方案",
    "/settings/account",
    `${detailCard("月卡方案", ["未来可以开放月卡制，包含更高的生成次数、历史档案云同步、偏好模型长期记忆和高级菜谱模板。"], `<a class="sub-button" href="#/settings/rules/member-service">查看会员服务协议</a>`)}
    ${detailCard("当前状态", ["当前账户未开通会员，所有权益均为原型演示，不产生真实扣费。"])}`
  ),
  createSubpageRoute(
    "/settings/customer-service",
    "联系客服",
    "/settings",
    detailCard("客服入口", ["正式小程序内这里会接入微信客服、问题分类、反馈图片上传和处理进度。", "当前原型先保留入口，避免用户在设置里找不到服务支持。"])
  ),
  createSubpageRoute(
    "/settings/rules",
    "条款与规则",
    "/settings",
    `<nav class="sub-tabs"><a class="sub-tab active" href="#/settings/rules">条款规则</a><a class="sub-tab" href="#/settings/announcements">公告</a></nav>
    <div class="sub-list">
      ${row("会员服务协议", "/settings/rules/member-service")}
      ${row("隐私政策", "/settings/rules/privacy-policy")}
      ${row("使用条款", "/settings/rules/user-terms")}
      ${row("经营证照公示", "/settings/rules/license")}
      ${row("各类服务公示", "/settings/rules/service-notices")}
      ${row("各类业务规则", "/settings/rules/business-rules")}
    </div>`
  ),
  createSubpageRoute(
    "/settings/announcements",
    "条款与规则",
    "/settings",
    `<nav class="sub-tabs"><a class="sub-tab" href="#/settings/rules">条款规则</a><a class="sub-tab active" href="#/settings/announcements">公告</a></nav>
    ${detailCard("暂无公告", ["上线后这里会展示服务调整、会员价格调整、隐私政策更新和功能维护公告。"])}`
  ),
  createSubpageRoute(
    "/settings/rules/member-service",
    "会员服务协议",
    "/settings/rules",
    detailCard("会员服务协议", ["会员服务用于说明套餐权益、自动续费、退款规则、权益失效和异常处理。", "当前内容为产品原型占位，正式上线前需要替换为法务确认版本。"])
  ),
  createSubpageRoute(
    "/settings/rules/privacy-policy",
    "隐私政策",
    "/settings/rules",
    `${detailCard("隐私政策", ["拍立食会在必要范围内处理账号信息、设备信息、图片识别结果、偏好约束和生成记录，用于完成菜谱生成与档案保存。"])}
    <div class="sub-list">${row("查看个人信息共享清单", "/settings/privacy/personal-sharing")}${row("查看第三方信息共享清单", "/settings/privacy/third-party-sharing")}</div>`
  ),
  createSubpageRoute(
    "/settings/rules/user-terms",
    "使用条款",
    "/settings/rules",
    detailCard("使用条款", ["用户需要保证上传图片来源合法，不上传违法、侵权或与食物识别无关的内容。", "生成结果仅作为烹饪建议，不替代医疗、营养诊断或食品安全判断。"])
  ),
  createSubpageRoute(
    "/settings/rules/license",
    "经营证照公示",
    "/settings/rules",
    detailCard("经营证照公示", ["正式运营主体、营业执照、食品相关资质和支付服务资质会在这里展示。", "当前原型阶段暂无真实主体信息。"])
  ),
  createSubpageRoute(
    "/settings/rules/service-notices",
    "各类服务公示",
    "/settings/rules",
    detailCard("各类服务公示", ["这里用于展示充值服务、会员服务、AI 生成服务、客服处理时效和数据保存规则。"])
  ),
  createSubpageRoute(
    "/settings/rules/business-rules",
    "各类业务规则",
    "/settings/rules",
    detailCard("各类业务规则", ["这里用于展示生成次数计算、档案保存、退款边界、违规内容处理和账号异常处理规则。"])
  ),
  createSubpageRoute(
    "/settings/privacy",
    "隐私与信息",
    "/settings",
    `<div class="sub-list">
      ${row("隐私政策摘要", "/settings/privacy/summary")}
      ${row("个人信息共享清单", "/settings/privacy/personal-sharing")}
      ${row("第三方信息共享清单", "/settings/privacy/third-party-sharing")}
    </div>`
  ),
  createSubpageRoute(
    "/settings/privacy/summary",
    "隐私政策摘要",
    "/settings/privacy",
    detailCard("隐私政策摘要", ["我们只在提供菜谱生成、偏好记忆、档案保存、客服和安全风控时处理必要信息。", "涉及图片识别、支付、客服或统计分析的第三方能力，会在共享清单中列明。"])
  ),
  createSubpageRoute(
    "/settings/privacy/personal-sharing",
    "个人信息共享清单",
    "/settings/privacy",
    detailCard("个人信息共享清单", ["可能使用的信息包括微信授权身份标识、头像昵称、上传图片、识别出的食材、偏好设置、生成结果和操作日志。", "这些信息用于完成产品功能，不会在原型阶段上传到真实账号系统。"])
  ),
  createSubpageRoute(
    "/settings/privacy/third-party-sharing",
    "第三方信息共享清单",
    "/settings/privacy",
    detailCard("第三方信息共享清单", ["后续可能涉及微信登录、微信支付、云存储、图像识别、AI 生成和客服系统。", "正式上线前需要列出第三方名称、处理目的、共享字段和隐私政策链接。"])
  ),
  createSubpageRoute(
    "/settings/about",
    "关于拍立食",
    "/settings",
    `${detailCard("拍立食", ["拍立食是面向家庭与轻食场景的拍照生成菜谱工具，目标是把可用食材快速转成可执行的烹饪方案。"])}
    <div class="sub-list">${row("版本信息", "/settings/about/version")}${row("功能介绍", "/settings/about/features")}</div>`
  ),
  createSubpageRoute(
    "/settings/about/version",
    "版本信息",
    "/settings/about",
    detailCard("P2 原型版本", ["当前为 P2 H5 重构候选版本，用于验证信息架构、页面流转和核心交互。"])
  ),
  createSubpageRoute(
    "/settings/about/features",
    "功能介绍",
    "/settings/about",
    detailCard("核心能力", ["拍照识别食材、配置口味与营养约束、生成菜谱、保存档案，并在未来支持会员与充值能力。"])
  )
];
