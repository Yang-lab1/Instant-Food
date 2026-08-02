import { createElement } from "../../utils/dom.js";

export function createOverlayHost() {
  return createElement("div", {
    className: "overlay-host",
    attributes: {
      "aria-hidden": "true"
    }
  });
}
