import { createElement } from "../../utils/dom.js";

export function createButtonLink({ href, className, label }) {
  return createElement("a", {
    className,
    text: label,
    attributes: { href }
  });
}
