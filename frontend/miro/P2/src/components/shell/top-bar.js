import { createElement } from "../../utils/dom.js";

export function createTopBar(appName) {
  const root = createElement("header", { className: "miro-top-bar" });
  const brand = createElement("div", { className: "miro-top-bar__brand" });
  const label = createElement("span", {
    className: "miro-top-bar__eyebrow",
    text: "P2"
  });
  const title = createElement("strong", {
    className: "miro-top-bar__title",
    text: appName
  });

  const meta = createElement("div", { className: "miro-top-bar__meta" });
  const routeTitle = createElement("strong", {
    className: "miro-top-bar__route",
    text: "单层路由"
  });
  const routeDescription = createElement("span", {
    className: "miro-top-bar__description",
    text: "旧总装页不再参与新架构运行"
  });

  brand.append(label, title);
  meta.append(routeTitle, routeDescription);
  root.append(brand, meta);

  return {
    root,
    setRouteMeta(nextTitle, nextDescription) {
      routeTitle.textContent = nextTitle;
      routeDescription.textContent = nextDescription;
    }
  };
}
