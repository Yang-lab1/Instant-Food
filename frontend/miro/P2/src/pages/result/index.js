import template from "./template.html?raw";
import { createLegacyTemplateRoute, mountTemplateScripts } from "../../utils/legacy-page.js";

function bindResult(root, { router }) {
  const cleanup = [];
  const backButton = root.querySelector(".result-topbar button");
  const handleBack = () => router.navigate("/generation");

  if (backButton) {
    backButton.addEventListener("click", handleBack);
    cleanup.push(() => backButton.removeEventListener("click", handleBack));
  }

  cleanup.push(mountTemplateScripts(root, { html: template, router }));
  return () => {
    while (cleanup.length) {
      const dispose = cleanup.pop();
      dispose();
    }
  };
}

export const resultPage = createLegacyTemplateRoute({
  path: "/result",
  title: "Result",
  html: template,
  runScripts: false,
  onMount: bindResult
});
