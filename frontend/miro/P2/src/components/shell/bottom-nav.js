import { createButtonLink } from "../common/button.js";
import { createIcon } from "../common/icon.js";
import { createElement } from "../../utils/dom.js";

export function createBottomNav(routes) {
  const root = createElement("nav", {
    className: "miro-bottom-nav",
    attributes: {
      "aria-label": "页面导航"
    }
  });

  const items = routes
    .filter((route) => route.navLabel)
    .map((route) => {
      const link = createButtonLink({
        href: `#${route.path}`,
        className: "miro-bottom-nav__item",
        label: route.navLabel || route.title
      });
      link.prepend(createIcon(route.icon));
      root.append(link);
      return { path: route.path, link };
    });

  return {
    root,
    setActive(currentPath) {
      items.forEach(({ path, link }) => {
        link.classList.toggle("is-active", path === currentPath);
      });
    }
  };
}
