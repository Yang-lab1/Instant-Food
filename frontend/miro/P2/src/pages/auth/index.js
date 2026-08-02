import template from "./template.html?raw";
import { createLegacyTemplateRoute, resolveRouteTarget } from "../../utils/legacy-page.js";

function bindAuth(root, { router }) {
  const agreementCheckbox = root.querySelector("#agreementCheckbox");
  const actionButtons = Array.from(root.querySelectorAll("[data-target]"));
  if (!agreementCheckbox || !actionButtons.length) {
    return;
  }

  function syncButtons() {
    const disabled = !agreementCheckbox.checked;
    actionButtons.forEach((button) => {
      button.disabled = disabled;
    });
  }

  const removeListeners = [];
  actionButtons.forEach((button) => {
    const handleClick = () => {
      if (button.disabled) {
        return;
      }

      const route = resolveRouteTarget(button.dataset.target);
      if (route) {
        router.navigate(route);
      }
    };
    button.addEventListener("click", handleClick);
    removeListeners.push(() => button.removeEventListener("click", handleClick));
  });

  agreementCheckbox.addEventListener("change", syncButtons);
  removeListeners.push(() => agreementCheckbox.removeEventListener("change", syncButtons));
  syncButtons();

  return () => {
    removeListeners.forEach((remove) => remove());
  };
}

export const authPage = createLegacyTemplateRoute({
  path: "/auth",
  title: "Auth",
  html: template,
  runScripts: false,
  onMount: bindAuth
});
