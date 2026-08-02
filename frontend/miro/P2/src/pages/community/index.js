import template from "./template.html?raw";
import { createLegacyTemplateRoute, resolveLegacyAssetUrl } from "../../utils/legacy-page.js";

const dishes = [
  {
    id: "scallop",
    section: "interest",
    category: ["all", "hearty"],
    title: "扇贝失控现场",
    subtitle: "黄油、焦边和留白一起把舞台撑住",
    image: "../../assets/backgrounds/95dc01ddadd7c54292be548b216e61d8.jpg",
    badge: "今晚压轴",
    score: "4.9",
    duration: "15分钟",
    price: "¥45",
    mood: "正式晚餐",
    description: "把剩下的扇贝、黄油和一点绿叶做成像作品发布现场一样的热盘，主角明确，边缘克制。",
    reason: "它不是堆料型热闹，而是把焦香控制在刚刚好那一层，入口第一秒就有主角感。",
    marketCopy: "优先补齐黄油、扇贝和一抹能提亮盘面的绿色配菜，顺手带一只白盘，效果会更完整。",
    tags: ["焦香主角", "晚餐压轴", "留白摆盘"]
  },
  {
    id: "burger",
    section: "interest",
    category: ["all", "night", "snack"],
    title: "午夜双层堡",
    subtitle: "浓郁到有点危险，但完全值得",
    image: "../../assets/backgrounds/1.png",
    badge: "深夜高赞",
    score: "4.7",
    duration: "12分钟",
    price: "¥36",
    mood: "深夜救场",
    description: "剩牛肉、芝士和一点烤洋葱被重新压缩成重口但不粗糙的深夜解法。",
    reason: "芝士和焦边一起把情绪顶上来，是典型的深夜主角盘。",
    marketCopy: "补牛肉饼、芝士片和生菜就够，其它都能在冰箱里自己完成重组。",
    tags: ["罪恶感", "夜宵主角", "一口满足"]
  },
  {
    id: "rice",
    section: "interest",
    category: ["all", "hearty"],
    title: "焦糖鸡腿饭",
    subtitle: "收汁很亮，米饭也被照顾到了",
    image: "../../assets/backgrounds/5.png",
    badge: "一盘见效",
    score: "4.8",
    duration: "18分钟",
    price: "¥32",
    mood: "下班之后",
    description: "把鸡腿的油脂控制在亮泽但不负担的那一层，米饭只负责承接，不抢戏。",
    reason: "它最适合把松散食材重新收口，味道稳，视觉也稳。",
    marketCopy: "鸡腿、米饭和一点提亮的小葱最关键，调味只要保持焦糖感。",
    tags: ["热盘主菜", "下班快手", "收汁亮泽"]
  },
  {
    id: "sushi",
    section: "tonight",
    category: ["all", "fresh"],
    title: "夜幕寿司",
    subtitle: "更安静的一盘，边缘很干净",
    image: "../../assets/backgrounds/3.jpg",
    badge: "冷盘灵感",
    score: "4.6",
    duration: "10分钟",
    price: "¥28",
    mood: "轻盈收尾",
    description: "适合把剩下的刺身和米饭重新整理成一盘干净、克制、看起来不费力的作品。",
    reason: "它不是为了炫耀，而是为了让颜色、留白和切面一起说话。",
    marketCopy: "优先补刺身和米饭，顺手带一点海苔与香草，盘面会更完整。",
    tags: ["冷盘", "轻盈", "线条感"]
  },
  {
    id: "steak",
    section: "tonight",
    category: ["all", "hearty"],
    title: "热板牛排",
    subtitle: "焦边够响，中心依旧柔软",
    image: "../../assets/backgrounds/4.jpg",
    badge: "高热盘面",
    score: "4.8",
    duration: "14分钟",
    price: "¥39",
    mood: "周末主菜",
    description: "剩牛排不需要重新发明，只要重新安排热度、切面和摆位，就会像新做的一样。",
    reason: "这类菜的关键是控制火候与留白，不是把所有配菜堆满盘面。",
    marketCopy: "带一点黄油、海盐和一抹绿色即可，真正决定质感的还是牛排本身。",
    tags: ["主角感", "高温焦边", "干净收口"]
  },
  {
    id: "snack",
    section: "tonight",
    category: ["all", "snack", "night"],
    title: "一口拼盘",
    subtitle: "把零碎食材重新编排成节奏",
    image: "../../assets/backgrounds/2.jpg",
    badge: "零食重组",
    score: "4.5",
    duration: "8分钟",
    price: "¥22",
    mood: "边聊边吃",
    description: "适合把散碎的小食、蘸酱和一点炙烤元素拼成一个有秩序的分享盘。",
    reason: "它更像一块会说话的桌面编排，不需要复杂做法，但很适合拍照。",
    marketCopy: "去补蘸酱、香草和一个统一色系的主食材，整盘会立刻有完整度。",
    tags: ["零食盘", "分享感", "拍照友好"]
  }
];

const categories = [
  { id: "all", label: "全部灵感", icon: "dashboard_customize" },
  { id: "hearty", label: "热盘主菜", icon: "local_fire_department" },
  { id: "fresh", label: "轻盈冷盘", icon: "eco" },
  { id: "night", label: "深夜救场", icon: "bedtime" },
  { id: "snack", label: "零食重组", icon: "local_pizza" }
];

function bindCommunity(root, { router }) {
  const state = { category: "all", liked: false };
  const device = root.querySelector("#device");
  const categoriesEl = root.querySelector("#categories");
  const interestRail = root.querySelector("#interestRail");
  const tonightRail = root.querySelector("#tonightRail");
  const detail = root.querySelector("#detail");
  const decisionSheet = root.querySelector("#decisionSheet");
  const decisionBackdrop = root.querySelector("#decisionBackdrop");
  const fields = {
    image: root.querySelector("#detailImage"),
    title: root.querySelector("#detailTitle"),
    price: root.querySelector("#detailPrice"),
    sheetTitle: root.querySelector("#sheetTitle"),
    description: root.querySelector("#detailDescription"),
    score: root.querySelector("#detailScore"),
    duration: root.querySelector("#detailDuration"),
    mood: root.querySelector("#detailMood"),
    reason: root.querySelector("#detailReason"),
    marketCopy: root.querySelector("#detailMarketCopy"),
    tags: root.querySelector("#detailTags")
  };
  const firstDish = dishes[0];
  if (fields.image && firstDish) {
    fields.image.src = resolveLegacyAssetUrl(firstDish.image);
    fields.image.alt = firstDish.title;
  }
  root.querySelectorAll(".market-icon img").forEach((img) => {
    img.loading = "eager";
  });

  function current(section) {
    return dishes.filter(
      (dish) => dish.section === section && (state.category === "all" || dish.category.includes(state.category))
    );
  }

  function renderCategories() {
    categoriesEl.innerHTML = categories
      .map((item) => {
        const active = state.category === item.id ? " active" : "";
        return `<button type="button" class="cat${active}" data-category="${item.id}"><span class="material-symbols-outlined">${item.icon}</span><strong>${item.label}</strong></button>`;
      })
      .join("");

    categoriesEl.querySelectorAll("[data-category]").forEach((button) => {
      button.addEventListener("click", () => {
        state.category = button.dataset.category;
        renderCategories();
        renderRails();
      });
    });
  }

  function card(dish, compact) {
    const compactClass = compact ? " compact" : "";
    return `<button type="button" class="card${compactClass}" data-dish-id="${dish.id}"><div class="media"><img src="${resolveLegacyAssetUrl(dish.image)}" alt="${dish.title}" loading="lazy" /><div class="badges"><span class="chip">${dish.badge}</span><span class="score"><span class="material-symbols-outlined">star</span>${dish.score}</span></div><div class="copy"><h4>${dish.title}</h4><p>${dish.subtitle}</p></div></div></button>`;
  }

  function updateLike() {
    const icon = root.querySelector("#likeButton .material-symbols-outlined");
    if (!icon) {
      return;
    }

    if (state.liked) {
      icon.style.color = "#d4b178";
      icon.style.fontVariationSettings = '"FILL" 1, "wght" 500, "GRAD" 0, "opsz" 24';
      return;
    }

    icon.style.color = "";
    icon.style.fontVariationSettings = '"FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24';
  }

  function openDetail(id) {
    const dish = dishes.find((item) => item.id === id);
    if (!dish) {
      return;
    }

    state.liked = false;
    fields.image.src = resolveLegacyAssetUrl(dish.image);
    fields.image.alt = dish.title;
    fields.title.textContent = dish.title;
    fields.price.textContent = dish.price;
    fields.sheetTitle.textContent = dish.title;
    fields.description.textContent = dish.description;
    fields.score.textContent = `${dish.score}分`;
    fields.duration.textContent = dish.duration;
    fields.mood.textContent = dish.mood;
    fields.reason.textContent = dish.reason;
    fields.marketCopy.textContent = dish.marketCopy;
    fields.tags.innerHTML = dish.tags.map((tag) => `<span class="tag">${tag}</span>`).join("");
    root.querySelector("#directLink").href = "#/result";
    updateLike();
    detail.setAttribute("aria-hidden", "false");
    device.classList.add("is-detail");
    detail.querySelector(".detail-scroll").scrollTo({ top: 0, behavior: "auto" });
  }

  function bindCards(scope) {
    scope.querySelectorAll("[data-dish-id]").forEach((button) => {
      button.addEventListener("click", () => {
        const rail = button.closest(".rail");
        if (rail && rail.dataset.dragMoved === "true") {
          return;
        }
        openDetail(button.dataset.dishId);
      });
    });
  }

  function renderRails() {
    interestRail.innerHTML = current("interest").map((dish) => card(dish, false)).join("");
    tonightRail.innerHTML = current("tonight").map((dish) => card(dish, true)).join("");
    bindCards(interestRail);
    bindCards(tonightRail);
  }

  function attachElasticRail(rail) {
    if (!rail || rail.dataset.elasticBound === "true") {
      return;
    }

    rail.dataset.elasticBound = "true";
    let activePointerId = null;
    let startX = 0;
    let startScroll = 0;
    let lastX = 0;
    let lastTime = 0;
    let velocity = 0;
    let moved = false;
    let dragging = false;
    let currentOffset = 0;
    let springRaf = 0;

    const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
    const maxScroll = () => Math.max(0, rail.scrollWidth - rail.clientWidth);
    const damp = (value) => Math.sign(value) * Math.abs(value) ** 0.9 * 0.3;

    const setOffset = (value) => {
      currentOffset = value;
      rail.style.transform = value ? `translate3d(${value}px,0,0)` : "";
    };

    const springBack = () => {
      cancelAnimationFrame(springRaf);
      if (!currentOffset) {
        return;
      }

      const step = () => {
        currentOffset *= 0.78;
        if (Math.abs(currentOffset) < 0.45) {
          setOffset(0);
          return;
        }
        setOffset(currentOffset);
        springRaf = requestAnimationFrame(step);
      };
      springRaf = requestAnimationFrame(step);
    };

    const finishDrag = (event) => {
      if (activePointerId === null) {
        return;
      }
      if (event && event.pointerId !== activePointerId) {
        return;
      }

      activePointerId = null;
      dragging = false;
      rail.style.scrollSnapType = "x mandatory";
      if (moved) {
        const momentum = velocity * 240;
        rail.scrollTo({ left: clamp(rail.scrollLeft + momentum, 0, maxScroll()), behavior: "smooth" });
        rail.dataset.dragMoved = "true";
        setTimeout(() => {
          delete rail.dataset.dragMoved;
        }, 220);
      }
      springBack();
    };

    rail.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 || maxScroll() <= 0) {
        return;
      }

      cancelAnimationFrame(springRaf);
      activePointerId = event.pointerId;
      moved = false;
      dragging = false;
      startX = event.clientX;
      startScroll = rail.scrollLeft;
      lastX = event.clientX;
      lastTime = performance.now();
      velocity = 0;
      rail.style.scrollSnapType = "x mandatory";
    });

    rail.addEventListener("pointermove", (event) => {
      if (activePointerId === null || event.pointerId !== activePointerId) {
        return;
      }

      const dx = event.clientX - startX;
      if (!dragging && Math.abs(dx) > 14) {
        dragging = true;
        moved = true;
        rail.style.scrollSnapType = "none";
      }
      if (!dragging) {
        return;
      }

      const targetScroll = startScroll - dx;
      const max = maxScroll();
      const clamped = clamp(targetScroll, 0, max);
      const overshoot = targetScroll - clamped;
      rail.scrollLeft = clamped;
      setOffset(overshoot ? damp(-overshoot) : 0);
      const now = performance.now();
      const dt = Math.max(1, now - lastTime);
      velocity = (lastX - event.clientX) / dt;
      lastX = event.clientX;
      lastTime = now;
      event.preventDefault();
    });

    rail.addEventListener("pointerup", finishDrag);
    rail.addEventListener("pointercancel", finishDrag);
    rail.addEventListener("lostpointercapture", finishDrag);
  }

  function closeDetail() {
    device.classList.remove("is-detail", "is-decision-open");
    detail.setAttribute("aria-hidden", "true");
    decisionSheet.classList.remove("markets-open");
    decisionBackdrop.setAttribute("aria-hidden", "true");
  }

  function openDecision() {
    decisionSheet.classList.remove("markets-open");
    decisionBackdrop.setAttribute("aria-hidden", "false");
    device.classList.add("is-decision-open");
  }

  function closeDecision() {
    device.classList.remove("is-decision-open");
    decisionSheet.classList.remove("markets-open");
    decisionBackdrop.setAttribute("aria-hidden", "true");
  }

  root.querySelector("#backDetail").addEventListener("click", closeDetail);
  root.querySelector("#likeButton").addEventListener("click", () => {
    state.liked = !state.liked;
    updateLike();
  });
  root.querySelector("#followButton").addEventListener("click", openDecision);
  root.querySelector("#marketButton").addEventListener("click", () => {
    decisionSheet.classList.add("markets-open");
  });
  decisionBackdrop.addEventListener("click", (event) => {
    if (event.target === event.currentTarget) {
      closeDecision();
    }
  });
  root.querySelector("#resetButton").addEventListener("click", () => {
    state.category = "all";
    renderCategories();
    renderRails();
  });
  root.querySelector("#directLink").addEventListener("click", (event) => {
    event.preventDefault();
    router.navigate("/result");
  });

  renderCategories();
  renderRails();
  attachElasticRail(interestRail);
  attachElasticRail(tonightRail);
}

export const communityPage = createLegacyTemplateRoute({
  path: "/community",
  title: "Community",
  html: template,
  runScripts: false,
  onMount: bindCommunity
});
