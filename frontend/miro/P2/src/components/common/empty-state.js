import { createElement } from "../../utils/dom.js";

export function createEmptyState(title, description) {
  const root = createElement("div", { className: "miro-empty-state" });
  root.append(
    createElement("strong", { text: title }),
    createElement("p", { text: description })
  );
  return root;
}
