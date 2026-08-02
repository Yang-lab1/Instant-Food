import template from "./template.html?raw";
import { createLegacyTemplateRoute, mountTemplateScripts } from "../../utils/legacy-page.js";

function bindWorkbench(root, { router }) {
  return mountTemplateScripts(root, { html: template, router });
}

export const workbenchPage = createLegacyTemplateRoute({
  path: "/workbench",
  title: "Workbench",
  html: template,
  runScripts: false,
  onMount: bindWorkbench
});
