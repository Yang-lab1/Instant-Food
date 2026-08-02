import template from "./template.html?raw";
import { createLegacyTemplateRoute, mountTemplateScripts } from "../../utils/legacy-page.js";

function bindArchive(root, { router }) {
  const cleanup = [];
  const backButton = root.querySelector('.archive-icon-btn[aria-label="返回"]');
  const handleBack = () => router.navigate("/nexus");

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

export const archivePage = createLegacyTemplateRoute({
  path: "/archive",
  title: "Archive",
  html: template,
  runScripts: false,
  onMount: bindArchive
});
