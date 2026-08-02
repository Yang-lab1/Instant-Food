import templateOne from "./template-1.html?raw";
import templateTwo from "./template-2.html?raw";
import templateThree from "./template-3.html?raw";
import { createLegacyTemplateRoute, resolveRouteTarget } from "../../utils/legacy-page.js";

function installOnboardingExitMotion() {
  if (document.getElementById("p2-onboarding-exit-motion")) {
    return;
  }

  const style = document.createElement("style");
  style.id = "p2-onboarding-exit-motion";
  style.textContent = `
    body.onboarding-body.is-page-exiting .phone-shell {
      transform: scale(0.996) !important;
      opacity: 0.96 !important;
      filter: saturate(0.99) brightness(0.96) !important;
      transition: transform 180ms cubic-bezier(0.2, 0.8, 0.2, 1), opacity 180ms cubic-bezier(0.2, 0.8, 0.2, 1), filter 180ms cubic-bezier(0.2, 0.8, 0.2, 1) !important;
    }
  `;
  document.head.appendChild(style);
}

function bindOnboarding(root, { router }) {
  const page = root.querySelector("[data-onboarding-page]");
  if (!page) {
    return;
  }

  installOnboardingExitMotion();

  const nextPage = page.dataset.next || "";
  const prevPage = page.dataset.prev || "";
  const authPage = decodeURIComponent("%E8%BA%AB%E4%BB%BD%E9%AA%8C%E8%AF%81.html");
  const goShell = page.querySelector("[data-go-shell]");
  const goRail = page.querySelector("[data-go-rail]");
  const goKnob = page.querySelector("[data-go-knob]");
  const goTrail = page.querySelector(".go-trail");
  const goLabel = page.querySelector("[data-go-label]");
  const loginCard = page.querySelector("[data-login-card]");
  const idleLabel = goShell?.dataset.idleLabel || decodeURIComponent("%E5%90%91%E5%8F%B3%E6%BB%91%E5%8A%A8");
  const readyLabel = goShell?.dataset.readyLabel || decodeURIComponent("%E6%9D%BE%E6%89%8B%E8%BF%9B%E5%85%A5");
  const cleanup = [];

  let authRequested = false;
  let dragging = false;
  let activePointerId = null;
  let startX = 0;
  let startOffset = 0;
  let currentOffset = 0;
  let maxOffset = 0;
  let exitTimer = 0;
  const railInset = 6;
  const railEndGap = 16;

  function addListener(target, type, handler, options) {
    target.addEventListener(type, handler, options);
    cleanup.push(() => target.removeEventListener(type, handler, options));
  }

  function navigateTo(target) {
    const route = resolveRouteTarget(target);
    if (!route) {
      return;
    }

    document.body.classList.add("is-page-exiting");
    window.clearTimeout(exitTimer);
    exitTimer = window.setTimeout(() => {
      router.navigate(route);
    }, 180);
  }

  if (goShell && goRail && goKnob && loginCard) {
    goShell.style.touchAction = "none";
    goRail.style.touchAction = "none";
    goRail.style.cursor = "grab";
    goKnob.style.touchAction = "none";
    goKnob.draggable = false;
    goKnob.style.webkitUserDrag = "none";

    const getMaxOffset = () =>
      Math.max(0, goRail.getBoundingClientRect().width - goKnob.getBoundingClientRect().width - railInset - railEndGap);

    const setState = (offset) => {
      maxOffset = getMaxOffset();
      currentOffset = Math.max(0, Math.min(offset, maxOffset));
      const progress = maxOffset === 0 ? 0 : currentOffset / maxOffset;
      goRail.style.setProperty("--knob-offset", `${currentOffset}px`);
      goRail.style.setProperty("--go-progress", progress.toFixed(3));
      goKnob.style.transform = `translate3d(${currentOffset}px, 0, 0)`;
      if (goTrail) {
        const maxTrailWidth = Math.max(goKnob.clientWidth, goRail.clientWidth - railInset - railEndGap);
        goTrail.style.width = `${Math.min(goKnob.clientWidth + currentOffset, maxTrailWidth)}px`;
      }
      return progress;
    };

    const setReady = (ready) => {
      goShell.classList.toggle("is-ready", ready);
      if (goLabel) {
        goLabel.textContent = ready ? readyLabel : idleLabel;
      }
    };

    const measure = () => {
      setState(Math.min(currentOffset, maxOffset));
    };

    const animateTo = (offset, ready) => {
      goKnob.style.transition =
        "transform 260ms cubic-bezier(0.16, 1, 0.3, 1), background-color 260ms cubic-bezier(0.16, 1, 0.3, 1), color 260ms cubic-bezier(0.16, 1, 0.3, 1)";
      setState(offset);
      setReady(ready);
      const timer = window.setTimeout(() => {
        goKnob.style.transition = "";
      }, 280);
      cleanup.push(() => window.clearTimeout(timer));
    };

    const resetSlider = () => {
      authRequested = false;
      animateTo(0, false);
    };

    const enterAuth = () => {
      if (authRequested) {
        return;
      }
      authRequested = true;
      navigateTo(authPage);
    };

    const activateLogin = (event) => {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      enterAuth();
    };

    const markReadyWhenMaxed = () => {
      if (maxOffset === 0) {
        return;
      }
      const progress = currentOffset / maxOffset;
      setReady(progress >= 0.94);
    };

    const stopDragEvent = (event) => {
      if (!event) {
        return;
      }
      if (event.cancelable) {
        event.preventDefault();
      }
      event.stopPropagation();
    };

    const beginDrag = (clientX, pointerId = null, snapToClient = false) => {
      if (dragging) {
        return;
      }
      if (goShell.classList.contains("is-ready")) {
        resetSlider();
        return;
      }

      dragging = true;
      activePointerId = pointerId;
      startX = clientX;
      if (snapToClient) {
        const railRect = goRail.getBoundingClientRect();
        const nextOffset = clientX - railRect.left - goKnob.clientWidth / 2 - railInset;
        setState(nextOffset);
      }
      startOffset = currentOffset;
      goKnob.style.transition = "none";
    };

    const updateDrag = (clientX) => {
      if (!dragging) {
        return;
      }

      const delta = clientX - startX;
      setState(startOffset + delta);
      markReadyWhenMaxed();
    };

    const finishDrag = (event) => {
      if (!dragging) {
        return;
      }
      if (event && activePointerId !== null && event.pointerId !== activePointerId) {
        return;
      }

      const pointerId = activePointerId;
      dragging = false;
      const progress = maxOffset === 0 ? 0 : currentOffset / maxOffset;
      const shouldEnter = progress > 0.52;
      animateTo(shouldEnter ? maxOffset : 0, shouldEnter);
      if (pointerId !== null && typeof goRail.releasePointerCapture === "function" && goRail.hasPointerCapture(pointerId)) {
        try {
          goRail.releasePointerCapture(pointerId);
        } catch (error) {
          // Pointer capture can already be released by the browser.
        }
      }
      activePointerId = null;
      if (shouldEnter) {
        const timer = window.setTimeout(enterAuth, 20);
        cleanup.push(() => window.clearTimeout(timer));
      }
    };

    loginCard.tabIndex = 0;
    loginCard.setAttribute("role", "button");
    loginCard.setAttribute("aria-label", decodeURIComponent("%E5%89%8D%E5%BE%80%E8%BA%AB%E4%BB%BD%E9%AA%8C%E8%AF%81"));
    loginCard.style.cursor = "pointer";
    loginCard.style.touchAction = "manipulation";
    loginCard.style.webkitTapHighlightColor = "transparent";

    addListener(loginCard, "click", activateLogin);
    addListener(loginCard, "keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activateLogin(event);
      }
    });

    addListener(goKnob, "dragstart", (event) => {
      stopDragEvent(event);
    });

    addListener(goShell, "pointerdown", (event) => {
      if (event.pointerType === "touch") {
        return;
      }
      if (event.pointerType === "mouse" && event.button !== 0) {
        return;
      }

      beginDrag(event.clientX, event.pointerId, event.target !== goKnob);
      if (typeof goRail.setPointerCapture === "function") {
        try {
          goRail.setPointerCapture(event.pointerId);
        } catch (error) {
          // Pointer capture is best-effort across browsers.
        }
      }
      stopDragEvent(event);
    }, { capture: true });

    addListener(window, "pointermove", (event) => {
      if (!dragging || event.pointerId !== activePointerId) {
        return;
      }

      updateDrag(event.clientX);
      stopDragEvent(event);
    }, { capture: true });

    addListener(window, "pointerup", finishDrag, { capture: true });
    addListener(window, "pointercancel", finishDrag, { capture: true });
    addListener(goRail, "lostpointercapture", finishDrag);

    addListener(goShell, "touchstart", (event) => {
      const touch = event.changedTouches[0] || event.touches[0];
      if (!touch) {
        return;
      }

      beginDrag(touch.clientX, null, event.target !== goKnob);
      stopDragEvent(event);
    }, { passive: false, capture: true });

    addListener(window, "touchmove", (event) => {
      if (!dragging || activePointerId !== null) {
        return;
      }
      const touch = event.changedTouches[0] || event.touches[0];
      if (!touch) {
        return;
      }

      updateDrag(touch.clientX);
      stopDragEvent(event);
    }, { passive: false, capture: true });

    addListener(window, "touchend", (event) => {
      if (activePointerId !== null) {
        return;
      }
      finishDrag(event);
    }, { passive: false, capture: true });

    addListener(window, "touchcancel", (event) => {
      if (activePointerId !== null) {
        return;
      }
      finishDrag(event);
    }, { passive: false, capture: true });

    addListener(window, "resize", measure);
    measure();
    setReady(false);
  }

  let swipeTracking = false;
  let swipeTriggered = false;
  let swipeStartX = 0;
  let swipeStartY = 0;

  const shouldIgnoreSwipe = (target) =>
    Boolean(target?.closest("[data-go-shell]") || target?.closest("[data-login-card]"));

  const beginSwipe = (clientX, clientY, target) => {
    if (!target || shouldIgnoreSwipe(target)) {
      return;
    }
    swipeTracking = true;
    swipeTriggered = false;
    swipeStartX = clientX;
    swipeStartY = clientY;
  };

  const routeSwipe = (clientX, clientY) => {
    const deltaX = clientX - swipeStartX;
    const deltaY = clientY - swipeStartY;
    swipeTracking = false;
    if (Math.abs(deltaY) > 64 || Math.abs(deltaX) < 84 || Math.abs(deltaX) <= Math.abs(deltaY) * 1.15) {
      return false;
    }
    if (deltaX < 0 && nextPage) {
      navigateTo(nextPage);
      return true;
    }
    if (deltaX > 0 && prevPage) {
      navigateTo(prevPage);
      return true;
    }
    return false;
  };

  const updateSwipe = (clientX, clientY) => {
    if (!swipeTracking || swipeTriggered) {
      return;
    }
    const deltaX = clientX - swipeStartX;
    const deltaY = clientY - swipeStartY;
    if (Math.abs(deltaY) > 64) {
      swipeTracking = false;
      return;
    }
    if (Math.abs(deltaX) < 84 || Math.abs(deltaX) <= Math.abs(deltaY) * 1.15) {
      return;
    }
    swipeTriggered = routeSwipe(clientX, clientY);
  };

  const completeSwipe = (clientX, clientY) => {
    if (!swipeTracking || swipeTriggered) {
      return;
    }
    routeSwipe(clientX, clientY);
  };

  addListener(page, "pointerdown", (event) => {
    beginSwipe(event.clientX, event.clientY, event.target);
  });
  addListener(page, "pointermove", (event) => {
    updateSwipe(event.clientX, event.clientY);
  });
  addListener(page, "pointerup", (event) => {
    completeSwipe(event.clientX, event.clientY);
  });
  addListener(page, "pointercancel", () => {
    swipeTracking = false;
    swipeTriggered = false;
  });

  return () => {
    window.clearTimeout(exitTimer);
    cleanup.forEach((dispose) => dispose());
  };
}

export const onboardingRoutes = [
  createLegacyTemplateRoute({
    path: "/onboarding/1",
    title: "Onboarding 1",
    html: templateOne,
    runScripts: false,
    onMount: bindOnboarding
  }),
  createLegacyTemplateRoute({
    path: "/onboarding/2",
    title: "Onboarding 2",
    html: templateTwo,
    runScripts: false,
    onMount: bindOnboarding
  }),
  createLegacyTemplateRoute({
    path: "/onboarding/3",
    title: "Onboarding 3",
    html: templateThree,
    runScripts: false,
    onMount: bindOnboarding
  })
];
