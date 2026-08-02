import template from "./template.html?raw";
import { createLegacyTemplateRoute } from "../../utils/legacy-page.js";

const heroStates = {
  dinner: {
    tabLabel: "今晚推荐",
    heroAria: "今夜主推",
    heroImage: "../../assets/backgrounds/95dc01ddadd7c54292be548b216e61d8.jpg",
    heroAlt: "今夜主推灵感卡片",
    badgeValue: "30%",
    badgeLabel: "余料优先",
    heroTitle: "炙香夜盘",
    heroSubtitle: "今夜灵感主菜",
    featureImage:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuBFSekwk9S1EzjyTBu6cLlWtZ5wC4Ccu1IJ3A5FJ5_D-9QOotb5dnlOmLU1g7r2a1s48_NamDNznDxdrNOagWbwA-feRzR55DicJR98tTy9TabCL8cFfu9PCEhENUl0-yqeiASBKwn49hHechconjEEibzSGGRzR5kDr8g6FNJTjZ29fXWAOi7Q3BmOINICm_38EbLxI8u1We6WRveiIiHJfbxr5rXP7l_K-AKD3rgo0zbdqTPeHSigJfXGEvilT1Voj9iNBv4X0cs",
    featureAlt: "香草烤鸡",
    featureMetaPrimary: "15 分钟",
    featureMetaSecondary: "适合晚餐",
    featureTitle: "15 分钟热盘",
    featureCopy: "鸡肉、番茄和香草，快手又有光泽。"
  },
  drink: {
    tabLabel: "轻饮灵感",
    heroAria: "轻饮灵感",
    heroImage: "../../assets/backgrounds/2.jpg",
    heroAlt: "轻饮灵感卡片",
    badgeValue: "12%",
    badgeLabel: "清爽开场",
    heroTitle: "青柑冷萃",
    heroSubtitle: "先把味觉唤醒，再决定今晚做什么",
    featureImage: "../../assets/backgrounds/3.jpg",
    featureAlt: "轻饮灵感",
    featureMetaPrimary: "8 分钟",
    featureMetaSecondary: "低负担",
    featureTitle: "一杯先醒胃",
    featureCopy: "酸感、气泡和一点点香草，把这顿饭的前奏先铺出来。"
  },
  "late-night": {
    tabLabel: "夜宵救场",
    heroAria: "夜宵救场",
    heroImage: "../../assets/backgrounds/5.png",
    heroAlt: "夜宵救场卡片",
    badgeValue: "18%",
    badgeLabel: "快速上桌",
    heroTitle: "铁板夜食",
    heroSubtitle: "收尾不用复杂，够香、够快、够安定",
    featureImage: "../../assets/backgrounds/4.jpg",
    featureAlt: "夜宵救场",
    featureMetaPrimary: "12 分钟",
    featureMetaSecondary: "适合深夜",
    featureTitle: "深夜热盘",
    featureCopy: "把手边剩料重新组合，短时间内做出一盘能安静收尾的夜宵。"
  }
};

function animateSwap(elements) {
  elements.forEach((element, index) => {
    if (!element || typeof element.animate !== "function") {
      return;
    }

    element.animate(
      [
        { opacity: 0.56, transform: "translateY(8px) scale(0.99)" },
        { opacity: 1, transform: "translateY(0) scale(1)" }
      ],
      {
        duration: 280,
        delay: index * 18,
        easing: "cubic-bezier(0.22, 1, 0.36, 1)",
        fill: "both"
      }
    );
  });
}

function bindNexus(root) {
  const heroTabs = Array.from(root.querySelectorAll("#heroTabs .hero-tab"));
  const heroPanel = root.querySelector("#heroPanel");
  const heroImage = root.querySelector("#heroImage");
  const heroBadge = root.querySelector("#heroBadge");
  const heroBadgeValue = root.querySelector("#heroBadgeValue");
  const heroBadgeLabel = root.querySelector("#heroBadgeLabel");
  const heroTitle = root.querySelector("#heroTitle");
  const heroSubtitle = root.querySelector("#heroSubtitle");
  const featureSectionTitle = root.querySelector("#featureSectionTitle");
  const featureImage = root.querySelector("#featureImage");
  const featureMetaPrimary = root.querySelector("#featureMetaPrimary");
  const featureMetaSecondary = root.querySelector("#featureMetaSecondary");
  const featureTitle = root.querySelector("#featureTitle");
  const featureCopy = root.querySelector("#featureCopy");

  function applyHeroState(key) {
    const state = heroStates[key];
    if (!state) {
      return;
    }

    heroTabs.forEach((tab) => {
      const isActive = tab.dataset.heroKey === key;
      tab.classList.toggle("active", isActive);
      tab.setAttribute("aria-pressed", isActive ? "true" : "false");
    });

    heroPanel.setAttribute("aria-label", state.heroAria);
    heroImage.src = state.heroImage;
    heroImage.alt = state.heroAlt;
    heroBadge.setAttribute("aria-label", `${state.badgeValue} ${state.badgeLabel}`);
    heroBadgeValue.textContent = state.badgeValue;
    heroBadgeLabel.textContent = state.badgeLabel;
    heroTitle.textContent = state.heroTitle;
    heroSubtitle.textContent = state.heroSubtitle;
    featureSectionTitle.textContent = state.tabLabel;
    featureImage.src = state.featureImage;
    featureImage.alt = state.featureAlt;
    featureMetaPrimary.textContent = state.featureMetaPrimary;
    featureMetaSecondary.textContent = state.featureMetaSecondary;
    featureTitle.textContent = state.featureTitle;
    featureCopy.textContent = state.featureCopy;

    animateSwap([
      heroImage,
      heroBadge,
      heroTitle,
      heroSubtitle,
      featureSectionTitle,
      featureImage,
      featureMetaPrimary,
      featureMetaSecondary,
      featureTitle,
      featureCopy
    ]);
  }

  heroTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      applyHeroState(tab.dataset.heroKey);
    });
  });
}

export const nexusPage = createLegacyTemplateRoute({
  path: "/nexus",
  title: "Nexus",
  html: template,
  runScripts: false,
  onMount: bindNexus
});
