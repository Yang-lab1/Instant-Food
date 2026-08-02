import { APP_NAME, DEFAULT_ROUTE_PATH } from "./app/constants.js";
import { createRouter } from "./app/router.js";
import { routes, findRouteByPath } from "./app/routes.js";
import { createStore } from "./app/store.js";
import { createOverlayHost } from "./components/overlay/overlay-host.js";
import { createAppShell } from "./components/shell/app-shell.js";

export function bootApp(container) {
  if (!container) {
    return;
  }

  const store = createStore({
    currentPath: DEFAULT_ROUTE_PATH
  });

  const shell = createAppShell({
    appName: APP_NAME,
    routes
  });
  shell.setLayout("runtime");
  shell.setChrome({
    showTopBar: false,
    showBottomNav: false
  });

  const overlayHost = createOverlayHost();
  shell.root.append(overlayHost);

  container.replaceChildren(shell.root);

  const router = createRouter({
    routes,
    defaultPath: DEFAULT_ROUTE_PATH,
    onRouteChange(path) {
      const route = findRouteByPath(path);
      if (route.redirectTo) {
        router.navigate(route.redirectTo);
        return;
      }

      const isImmersive = route.layout === "immersive";
      store.setState({ currentPath: route.path });
      shell.setLayout(route.layout || "default");
      shell.setChrome({
        showTopBar: route.showTopBar ?? !isImmersive,
        showBottomNav: route.showBottomNav ?? !isImmersive
      });
      shell.setActiveRoute(route.path);
      shell.setHeader(route.title, route.description);
      shell.clearContent();
      shell.setContent(route.render({ store, router }));
      document.title = `${APP_NAME} | ${route.title}`;
    }
  });

  router.start();
}
