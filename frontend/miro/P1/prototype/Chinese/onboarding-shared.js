(function () {
  const page = document.querySelector("[data-onboarding-page]");
  if (!page) {
    return;
  }

  const nextPage = page.dataset.next || "";
  const prevPage = page.dataset.prev || "";
  const goShell = page.querySelector("[data-go-shell]");
  const goRail = page.querySelector("[data-go-rail]");
  const goKnob = page.querySelector("[data-go-knob]");
  const goLabel = page.querySelector("[data-go-label]");
  const loginCard = page.querySelector("[data-login-card]");
  const idleLabel = (goShell && goShell.dataset.idleLabel) || "向右滑动";
  const readyLabel = (goShell && goShell.dataset.readyLabel) || "松手进入";
  const authPage = "身份验证.html";

  let authRequested = false;
  let dragging = false;
  let activePointerId = null;
  let startX = 0;
  let startOffset = 0;
  let currentOffset = 0;
  let maxOffset = 0;

  const navigateTo = (target) => {
    if (!target) {
      return;
    }
    document.body.classList.add("is-page-exiting");
    window.setTimeout(() => {
      window.location.href = target;
    }, 180);
  };

  if (goShell && goRail && goKnob) {
    goShell.style.touchAction = "pan-y";
    goRail.style.touchAction = "none";
    goRail.style.cursor = "grab";
    goKnob.style.touchAction = "none";

    const setState = (offset) => {
      currentOffset = Math.max(0, Math.min(offset, maxOffset));
      const progress = maxOffset === 0 ? 0 : currentOffset / maxOffset;
      goRail.style.setProperty("--knob-offset", currentOffset + "px");
      goRail.style.setProperty("--go-progress", progress.toFixed(3));
      return progress;
    };

    const setReady = (ready) => {
      goShell.classList.toggle("is-ready", ready);
      if (goLabel) {
        goLabel.textContent = ready ? readyLabel : idleLabel;
      }
    };

    const measure = () => {
      maxOffset = Math.max(0, goRail.clientWidth - goKnob.clientWidth - 12);
      setState(Math.min(currentOffset, maxOffset));
    };

    const animateTo = (offset, ready) => {
      goKnob.style.transition = "transform 260ms cubic-bezier(0.16, 1, 0.3, 1), background-color 260ms cubic-bezier(0.16, 1, 0.3, 1), color 260ms cubic-bezier(0.16, 1, 0.3, 1)";
      setState(offset);
      setReady(ready);
      window.setTimeout(() => {
        goKnob.style.transition = "";
      }, 280);
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

    const enterIfReady = () => {
      if (goShell.classList.contains("is-ready")) {
        enterAuth();
      }
    };

    const activateLogin = (event) => {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      enterAuth();
    };

    const enterWhenMaxed = (pointerId) => {
      if (maxOffset === 0) {
        return;
      }
      const progress = currentOffset / maxOffset;
      if (progress < 0.94) {
        return;
      }
      dragging = false;
      activePointerId = null;
      if (pointerId !== null && typeof goRail.releasePointerCapture === "function" && goRail.hasPointerCapture(pointerId)) {
        goRail.releasePointerCapture(pointerId);
      }
      animateTo(maxOffset, true);
      window.setTimeout(() => {
        enterAuth();
      }, 20);
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
        } catch (error) {}
      }
      activePointerId = null;
      if (shouldEnter) {
        window.setTimeout(() => {
          enterAuth();
        }, 20);
      }
    };

    loginCard.tabIndex = 0;
    loginCard.setAttribute("role", "button");
    loginCard.setAttribute("aria-label", "前往身份验证");
    loginCard.style.cursor = "pointer";
    loginCard.style.touchAction = "manipulation";
    loginCard.style.webkitTapHighlightColor = "transparent";
    loginCard.addEventListener("click", activateLogin);
    loginCard.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activateLogin(event);
      }
    });

    goRail.addEventListener("pointerdown", (event) => {
      if (event.pointerType === "mouse" && event.button !== 0) {
        return;
      }
      if (goShell.classList.contains("is-ready")) {
        resetSlider();
        return;
      }
      dragging = true;
      activePointerId = event.pointerId;
      startX = event.clientX;
      startOffset = currentOffset;
      goKnob.style.transition = "none";
      if (typeof goRail.setPointerCapture === "function") {
        try {
          goRail.setPointerCapture(event.pointerId);
        } catch (error) {}
      }
      event.preventDefault();
      event.stopPropagation();
    });

    goRail.addEventListener("pointermove", (event) => {
      if (!dragging || event.pointerId !== activePointerId) {
        return;
      }
      const delta = event.clientX - startX;
      setState(startOffset + delta);
      enterWhenMaxed(event.pointerId);
      event.preventDefault();
    });

    goRail.addEventListener("pointerup", finishDrag);
    goRail.addEventListener("pointercancel", finishDrag);
    goRail.addEventListener("lostpointercapture", finishDrag);
    const readyObserver = new MutationObserver(() => {
      enterIfReady();
    });
    readyObserver.observe(goShell, {
      attributes: true,
      attributeFilter: ["class"]
    });
    window.addEventListener("resize", measure);
    measure();
    setReady(false);
  }

  let swipeTracking = false;
  let swipeTriggered = false;
  let swipeStartX = 0;
  let swipeStartY = 0;

  const shouldIgnoreSwipe = (target) => {
    return Boolean(
      target?.closest("[data-go-shell]") ||
      target?.closest("[data-login-card]")
    );
  };

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

  page.addEventListener("pointerdown", (event) => {
    beginSwipe(event.clientX, event.clientY, event.target);
  });
  page.addEventListener("pointermove", (event) => {
    updateSwipe(event.clientX, event.clientY);
  });
  page.addEventListener("pointerup", (event) => {
    completeSwipe(event.clientX, event.clientY);
  });
  page.addEventListener("pointercancel", () => {
    swipeTracking = false;
    swipeTriggered = false;
  });
})();
