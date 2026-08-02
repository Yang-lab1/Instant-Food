import { archivePage } from "../pages/archive/index.js";
import { authPage } from "../pages/auth/index.js";
import { capturePage } from "../pages/capture/index.js";
import { communityPage } from "../pages/community/index.js";
import { generationPage } from "../pages/generation/index.js";
import { nexusPage } from "../pages/nexus/index.js";
import { onboardingRoutes } from "../pages/onboarding/index.js";
import { resultPage } from "../pages/result/index.js";
import { settingsRoutes } from "../pages/settings/index.js";
import { workbenchPage } from "../pages/workbench/index.js";
import { DEFAULT_ROUTE_PATH } from "./constants.js";

export const routes = [
  ...onboardingRoutes,
  authPage,
  nexusPage,
  communityPage,
  capturePage,
  archivePage,
  ...settingsRoutes,
  workbenchPage,
  generationPage,
  resultPage
];

export function findRouteByPath(path) {
  return (
    routes.find((route) => route.path === path) ||
    routes.find((route) => route.path === DEFAULT_ROUTE_PATH) ||
    routes[0]
  );
}
