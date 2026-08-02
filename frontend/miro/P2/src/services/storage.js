import { isNonEmptyString } from "../utils/guards.js";

export function readStorage(key, fallbackValue = "") {
  try {
    const value = window.localStorage.getItem(key);
    return value ?? fallbackValue;
  } catch (error) {
    return fallbackValue;
  }
}

export function writeStorage(key, value) {
  try {
    if (!isNonEmptyString(value)) {
      window.localStorage.removeItem(key);
      return;
    }
    window.localStorage.setItem(key, value);
  } catch (error) {
    return;
  }
}
