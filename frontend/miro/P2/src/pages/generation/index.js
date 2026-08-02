import template from "./template.html?raw";
import { createLegacyTemplateRoute, mountTemplateScripts } from "../../utils/legacy-page.js";

function bindGeneration(root, { router }) {
  return mountTemplateScripts(root, { html: template, router });
}

export const generationPage = createLegacyTemplateRoute({
  path: "/generation",
  title: "Generation",
  html: template,
  runScripts: false,
  onMount: bindGeneration
});
