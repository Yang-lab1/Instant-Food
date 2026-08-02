import template from "./template.html?raw";
import { createLegacyTemplateRoute, mountTemplateScripts } from "../../utils/legacy-page.js";

function bindCapture(root, { router }) {
  return mountTemplateScripts(root, { html: template, router });
}

export const capturePage = createLegacyTemplateRoute({
  path: "/capture",
  title: "Capture",
  html: template,
  runScripts: false,
  onMount: bindCapture
});
