import { API_BASE_STORAGE_KEY } from "../app/constants.js";
import { readStorage } from "./storage.js";

export function buildApiUrl(pathname) {
  const baseUrl = readStorage(API_BASE_STORAGE_KEY, "").replace(/\/+$/, "");
  if (!baseUrl) {
    return pathname;
  }
  const safePath = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return `${baseUrl}${safePath}`;
}

export async function fetchJson(pathname, options = {}) {
  const response = await fetch(buildApiUrl(pathname), options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}
