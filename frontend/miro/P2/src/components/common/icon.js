import { createElement } from "../../utils/dom.js";

export function createIcon(name) {
  return createElement("span", {
    className: "miro-icon",
    text: name || "•",
    attributes: {
      "aria-hidden": "true"
    }
  });
}
