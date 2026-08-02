import { formatStepLabel } from "./format.js";

export function createElement(tagName, options = {}) {
  const node = document.createElement(tagName);

  if (options.className) {
    node.className = options.className;
  }

  if (options.text) {
    node.textContent = options.text;
  }

  if (options.attributes) {
    Object.entries(options.attributes).forEach(([key, value]) => {
      node.setAttribute(key, value);
    });
  }

  return node;
}

export function clearNode(node) {
  node.replaceChildren();
}

export function createPageScaffold({ eyebrow, title, description, chips = [], sections = [] }) {
  const root = createElement("section", { className: "miro-page" });
  const header = createElement("header", { className: "miro-page__header" });

  header.append(
    createElement("span", { className: "miro-page__eyebrow", text: eyebrow }),
    createElement("h1", { className: "miro-page__title", text: title }),
    createElement("p", { className: "miro-page__description", text: description })
  );

  root.append(header);

  if (chips.length) {
    const chipRow = createElement("div", { className: "miro-chip-row" });
    chips.forEach((chip) => {
      chipRow.append(createElement("span", { className: "miro-chip", text: chip }));
    });
    root.append(chipRow);
  }

  if (sections.length) {
    const sectionGrid = createElement("div", { className: "miro-section-grid" });
    sections.forEach((section, index) => {
      const card = createElement("article", { className: "miro-section-card" });
      card.append(
        createElement("span", { className: "miro-page__eyebrow", text: formatStepLabel(index) }),
        createElement("h3", { text: section.title }),
        createElement("p", { text: section.description })
      );

      if (section.items?.length) {
        const list = createElement("ul");
        section.items.forEach((item) => {
          list.append(createElement("li", { text: item }));
        });
        card.append(list);
      }

      sectionGrid.append(card);
    });
    root.append(sectionGrid);
  }

  return root;
}
