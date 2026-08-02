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

  const navigateTo = (target) => {
    if (!target) {
      return;
    }
    document.body.classList.add("is-page-exiting");
    window.setTimeout(() => {
      window.location.href = target;
    }, 130);
  };

  if (goShell && goRail && goKnob) {
    let dragging = false;
    let activePointerId = null;
    let startX = 0;
    let startOffset = 0;
    let currentOffset = 0;
    let maxOffset = 0;

    const setState = (offset) => {
      currentOffset = Math.max(0, Math.min(offset, maxOffset));
      const progress = maxOffset === 0 ? 0 : currentOffset / maxOffset;
      goRail.style.setProperty("--knob-offset", currentOffset + "px");
      goRail.style.setProperty("--go-progress", progress.toFixed(3));
    };

    const setReady = (ready) => {
      goShell.classList.toggle("is-ready", ready);
      if (goLabel) {
        goLabel.textContent = ready ? "Ready" : "SWIPE RIGHT";
      }
    };

    const measure = () => {
      maxOffset = Math.max(0, goRail.clientWidth - goKnob.clientWidth - 12);
      setState(Math.min(currentOffset, maxOffset));
    };

    const animateTo = (offset, ready) => {
      goKnob.style.transition = "transform 220ms ease, background-color 220ms ease, color 220ms ease";
      setState(offset);
      setReady(ready);
      window.setTimeout(() => {
        goKnob.style.transition = "";
      }, 240);
    };

    const finishDrag = () => {
      if (!dragging) {
        return;
      }

      dragging = false;
      const progress = maxOffset === 0 ? 0 : currentOffset / maxOffset;
      animateTo(progress > 0.58 ? maxOffset : 0, progress > 0.58);
      activePointerId = null;
    };

    goKnob.addEventListener("pointerdown", (event) => {
      if (goShell.classList.contains("is-ready")) {
        animateTo(0, false);
        return;
      }

      dragging = true;
      activePointerId = event.pointerId;
      startX = event.clientX;
      startOffset = currentOffset;
      goKnob.style.transition = "none";
      goKnob.setPointerCapture(event.pointerId);
    });

    goKnob.addEventListener("pointermove", (event) => {
      if (!dragging || event.pointerId !== activePointerId) {
        return;
      }

      const delta = event.clientX - startX;
      setState(startOffset + delta);
    });

    goKnob.addEventListener("pointerup", finishDrag);
    goKnob.addEventListener("pointercancel", finishDrag);
    window.addEventListener("resize", measure);
    measure();
    setReady(false);
  }

  let swipeTracking = false;
  let swipePointerId = null;
  let swipeStartX = 0;
  let swipeStartY = 0;

  const resetSwipe = () => {
    swipeTracking = false;
    swipePointerId = null;
  };

  page.addEventListener("pointerdown", (event) => {
    if (
      event.target.closest("[data-go-shell]") ||
      event.target.closest("[data-login-card]")
    ) {
      return;
    }

    swipeTracking = true;
    swipePointerId = event.pointerId;
    swipeStartX = event.clientX;
    swipeStartY = event.clientY;
  });

  const completeSwipe = (event) => {
    if (!swipeTracking || event.pointerId !== swipePointerId) {
      return;
    }

    const deltaX = event.clientX - swipeStartX;
    const deltaY = event.clientY - swipeStartY;
    resetSwipe();

    if (Math.abs(deltaY) > 64 || Math.abs(deltaX) < 76) {
      return;
    }

    if (deltaX < 0 && nextPage) {
      navigateTo(nextPage);
    } else if (deltaX > 0 && prevPage) {
      navigateTo(prevPage);
    }
  };

  page.addEventListener("pointerup", completeSwipe);
  page.addEventListener("pointercancel", resetSwipe);
})();
