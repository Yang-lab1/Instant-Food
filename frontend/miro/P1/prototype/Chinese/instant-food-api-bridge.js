(function (global) {
  "use strict";

  var STORAGE_KEYS = {
    apiBaseUrl: "instantFoodApiBaseUrl",
    userId: "instantFoodUserId",
    selection: "molecularReconstructSelection",
    capturedImage: "capturedImageDataUrl",
    capturedImages: "capturedImagesDataUrl",
    generationResult: "generatedRecipeResult",
    boardPreview: "generatedBoardPreview"
  };
  var DEFAULT_API_BASE_URL = "https://instant-food-backend-api-20260402.vercel.app";
  var MAX_CAPTURED_IMAGES = 5;

  function safeStorage(storage, action) {
    try {
      return action(storage);
    } catch (error) {
      return null;
    }
  }

  function readStorage(storage, key) {
    return safeStorage(storage, function (target) {
      return target ? target.getItem(key) : null;
    });
  }

  function writeStorage(storage, key, value) {
    return safeStorage(storage, function (target) {
      if (!target) {
        return null;
      }
      if (value === null || value === undefined || value === "") {
        target.removeItem(key);
        return null;
      }
      target.setItem(key, value);
      return value;
    });
  }

  function resolveRuntimeWindow(view) {
    var win = view || global;
    try {
      if (
        win &&
        win.top &&
        win.top.location &&
        win.location &&
        win.top.location.origin === win.location.origin
      ) {
        return win.top;
      }
    } catch (error) {}
    return win;
  }

  function getRuntimeState(view) {
    var runtimeWindow = resolveRuntimeWindow(view);
    if (!runtimeWindow.__instantFoodRuntimeState__ || typeof runtimeWindow.__instantFoodRuntimeState__ !== "object") {
      runtimeWindow.__instantFoodRuntimeState__ = {};
    }
    return runtimeWindow.__instantFoodRuntimeState__;
  }

  function writeRuntimeState(key, value, view) {
    var state = getRuntimeState(view);
    if (value === null || value === undefined || value === "") {
      delete state[key];
      return null;
    }
    state[key] = value;
    return value;
  }

  function readRuntimeState(key, view) {
    var state = getRuntimeState(view);
    if (Object.prototype.hasOwnProperty.call(state, key)) {
      return state[key];
    }
    return null;
  }

  function parseJson(rawValue, fallbackValue) {
    if (!rawValue) {
      return fallbackValue;
    }
    try {
      return JSON.parse(rawValue);
    } catch (error) {
      return fallbackValue;
    }
  }

  function normalizeBaseUrl(rawValue) {
    var value = String(rawValue || "").trim();
    return value.replace(/\/+$/, "");
  }

  function isLoopbackHost(hostname) {
    var host = String(hostname || "").toLowerCase();
    return host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0";
  }

  function isFrontendVercelHost(hostname) {
    return /^frontend(?:-[a-z0-9-]+)?(?:-yangs-projects-d2ad4c9e)?\.vercel\.app$/i.test(String(hostname || ""));
  }

  function shouldUseSameOriginApiProxy(view) {
    var win = view || global;
    var protocol = String((win.location && win.location.protocol) || "").toLowerCase();
    var host = String((win.location && win.location.hostname) || "").toLowerCase();
    return protocol === "https:" && isFrontendVercelHost(host);
  }

  function sanitizeApiBaseUrl(rawValue, view) {
    var normalized = normalizeBaseUrl(rawValue);
    if (!normalized) {
      return normalizeBaseUrl(DEFAULT_API_BASE_URL);
    }

    var win = view || global;
    try {
      var targetUrl = new URL(normalized);
      var pageProtocol = String((win.location && win.location.protocol) || "").toLowerCase();
      var pageHost = String((win.location && win.location.hostname) || "").toLowerCase();
      var targetProtocol = String(targetUrl.protocol || "").toLowerCase();
      var targetHost = String(targetUrl.hostname || "").toLowerCase();

      if (targetProtocol !== "http:" && targetProtocol !== "https:") {
        return normalizeBaseUrl(DEFAULT_API_BASE_URL);
      }

      if (pageProtocol === "https:" && targetProtocol !== "https:") {
        return normalizeBaseUrl(DEFAULT_API_BASE_URL);
      }

      if (!isLoopbackHost(pageHost) && isLoopbackHost(targetHost)) {
        return normalizeBaseUrl(DEFAULT_API_BASE_URL);
      }

      return normalized;
    } catch (error) {
      return normalizeBaseUrl(DEFAULT_API_BASE_URL);
    }
  }

  function getApiBaseUrl(view) {
    var win = view || global;
    var params = new URLSearchParams((win.location && win.location.search) || "");
    var queryApiBase = params.get("apiBaseUrl");

    if (queryApiBase) {
      var normalizedFromQuery = normalizeBaseUrl(queryApiBase);
      writeStorage(win.localStorage, STORAGE_KEYS.apiBaseUrl, normalizedFromQuery);
      writeStorage(win.sessionStorage, STORAGE_KEYS.apiBaseUrl, normalizedFromQuery);
    }

    var explicitBase =
      global.__INSTANT_FOOD_API_BASE_URL__ ||
      queryApiBase ||
      readStorage(win.localStorage, STORAGE_KEYS.apiBaseUrl) ||
      readStorage(win.sessionStorage, STORAGE_KEYS.apiBaseUrl) ||
      DEFAULT_API_BASE_URL;

    var normalizedDefaultBase = normalizeBaseUrl(DEFAULT_API_BASE_URL);
    var normalizedExplicitBase = normalizeBaseUrl(explicitBase);
    if (shouldUseSameOriginApiProxy(win) && (!normalizedExplicitBase || normalizedExplicitBase === normalizedDefaultBase)) {
      writeStorage(win.localStorage, STORAGE_KEYS.apiBaseUrl, "");
      writeStorage(win.sessionStorage, STORAGE_KEYS.apiBaseUrl, "");
      return "";
    }

    var safeBase = sanitizeApiBaseUrl(explicitBase, win);
    if (safeBase) {
      writeStorage(win.localStorage, STORAGE_KEYS.apiBaseUrl, safeBase);
      writeStorage(win.sessionStorage, STORAGE_KEYS.apiBaseUrl, safeBase);
    }
    return safeBase;
  }

  function buildApiUrl(path, view) {
    var requestedPath = String(path || "").trim();
    if (!requestedPath) {
      return "";
    }

    if (/^https?:\/\//i.test(requestedPath)) {
      return requestedPath;
    }

    if (requestedPath.charAt(0) !== "/") {
      requestedPath = "/" + requestedPath;
    }

    var apiBaseUrl = getApiBaseUrl(view);
    if (!apiBaseUrl) {
      return requestedPath;
    }

    try {
      var requestUrl = new URL(requestedPath, "https://instant-food.local");
      var resolvedUrl = new URL(apiBaseUrl);
      var basePath = String(resolvedUrl.pathname || "").replace(/\/+$/, "");
      var mergedParams = new URLSearchParams(resolvedUrl.search);
      resolvedUrl.pathname = (basePath || "") + requestUrl.pathname;
      requestUrl.searchParams.forEach(function (value, key) {
        mergedParams.append(key, value);
      });
      resolvedUrl.search = mergedParams.toString();
      return resolvedUrl.toString();
    } catch (error) {
      return apiBaseUrl + requestedPath;
    }
  }

  function getUserId(view) {
    var win = view || global;
    var params = new URLSearchParams((win.location && win.location.search) || "");
    return (
      params.get("userId") ||
      readStorage(win.localStorage, STORAGE_KEYS.userId) ||
      readStorage(win.sessionStorage, STORAGE_KEYS.userId) ||
      "frontend-demo-user"
    );
  }

  function readSelection(view) {
    var win = view || global;
    return parseJson(readStorage(win.sessionStorage, STORAGE_KEYS.selection), null);
  }

  function writeCapturedImage(dataUrl, view) {
    var win = view || global;
    var normalized = String(dataUrl || "");
    writeRuntimeState(STORAGE_KEYS.capturedImage, normalized, win);
    writeStorage(win.sessionStorage, STORAGE_KEYS.capturedImage, normalized);
    return normalized;
  }

  function readCapturedImage(view) {
    var win = view || global;
    var fromRuntime = readRuntimeState(STORAGE_KEYS.capturedImage, win);
    if (typeof fromRuntime === "string" && fromRuntime.indexOf("data:") === 0) {
      return fromRuntime;
    }
    return readStorage(win.sessionStorage, STORAGE_KEYS.capturedImage) || "";
  }

  function normalizeCapturedImageArray(rawValue) {
    if (!Array.isArray(rawValue)) {
      return [];
    }

    var seen = Object.create(null);
    var normalized = [];
    rawValue.forEach(function (item) {
      var value = String(item || "").trim();
      if (!value || value.indexOf("data:") !== 0 || seen[value]) {
        return;
      }
      seen[value] = true;
      normalized.push(value);
    });
    return normalized;
  }

  function writeCapturedImages(dataUrls, view) {
    var win = view || global;
    var normalized = normalizeCapturedImageArray(dataUrls).slice(0, MAX_CAPTURED_IMAGES);
    writeRuntimeState(STORAGE_KEYS.capturedImages, normalized.slice(), win);
    writeStorage(win.sessionStorage, STORAGE_KEYS.capturedImages, JSON.stringify(normalized));
    writeCapturedImage(normalized[0] || "", win);
    return normalized;
  }

  function readCapturedImages(view) {
    var win = view || global;
    var fromRuntime = readRuntimeState(STORAGE_KEYS.capturedImages, win);
    var normalizedFromRuntime = normalizeCapturedImageArray(fromRuntime).slice(0, MAX_CAPTURED_IMAGES);
    if (normalizedFromRuntime.length) {
      return normalizedFromRuntime;
    }

    var raw = readStorage(win.sessionStorage, STORAGE_KEYS.capturedImages);
    var parsed = parseJson(raw, []);
    var normalized = normalizeCapturedImageArray(parsed).slice(0, MAX_CAPTURED_IMAGES);
    if (normalized.length) {
      return normalized;
    }

    var single = readCapturedImage(win);
    return single ? [single] : [];
  }

  function clearCapturedImage(view) {
    var win = view || global;
    writeRuntimeState(STORAGE_KEYS.capturedImage, "", win);
    writeRuntimeState(STORAGE_KEYS.capturedImages, "", win);
    writeStorage(win.sessionStorage, STORAGE_KEYS.capturedImage, "");
    writeStorage(win.sessionStorage, STORAGE_KEYS.capturedImages, "");
  }

  function readGenerationResult(view) {
    var win = view || global;
    return parseJson(readStorage(win.sessionStorage, STORAGE_KEYS.generationResult), null);
  }

  function writeGenerationResult(payload, view) {
    var win = view || global;
    var normalized = payload || {};
    writeStorage(win.sessionStorage, STORAGE_KEYS.generationResult, JSON.stringify(normalized));

    var preview = normalized.boardPreview || normalized.imageUrl || "";
    if (preview) {
      writeStorage(win.sessionStorage, STORAGE_KEYS.boardPreview, preview);
    }

    return normalized;
  }

  function clearGenerationResult(view) {
    var win = view || global;
    writeStorage(win.sessionStorage, STORAGE_KEYS.generationResult, "");
    writeStorage(win.sessionStorage, STORAGE_KEYS.boardPreview, "");
  }

  function resolveFlavorProfile(selection) {
    var tastes = Array.isArray(selection && selection.tastes) ? selection.tastes : [];
    if (!tastes.length) {
      return "\u5bb6\u5e38";
    }
    if (!tastes.length) {
      return "家常";
    }
    if (!tastes.length) {
      return "家常";
    }
    return tastes[0];
  }

  function isRandomOption(value) {
    return String(value || "").trim() === "\u968f\u673a";
    return String(value || "").trim() === "随机";
  }

  function normalizeSelectionValues(values) {
    return Array.isArray(values)
      ? values
          .map(function (item) {
            return String(item || "").trim();
          })
          .filter(function (item) {
            return item && !isRandomOption(item);
          })
      : [];
  }

  function buildRecipePayload(selection) {
    var safeSelection = selection || {};
    var ingredients = Array.isArray(safeSelection.ingredients) ? safeSelection.ingredients : [];
    var includedIngredients = ingredients.filter(function (item) {
      return item && item.included !== false && String(item.name || "").trim();
    });
    var normalizedTechnique = isRandomOption(safeSelection.technique) ? "" : String(safeSelection.technique || "").trim();
    var normalizedTastes = normalizeSelectionValues(safeSelection.tastes);
    var normalizedTools = normalizeSelectionValues(safeSelection.tools);
    var exclusions = Array.isArray(safeSelection.exclusions)
      ? safeSelection.exclusions
      : Array.isArray(safeSelection.excluded_ingredients)
      ? safeSelection.excluded_ingredients
      : Array.isArray(safeSelection.avoid_ingredients)
      ? safeSelection.avoid_ingredients
      : [];
    var normalizedExclusions = Array.from(new Set(exclusions.map(function (item) {
      return String(item || "").trim();
    }).filter(Boolean)));

    return {
      ingredients: includedIngredients.map(function (item) {
        var count = Number(item.count || 0) || 1;
        var unit = String(item.unit || "份").trim() || "份";
        var unitText = String(item.unit || "").trim() || "份";
        var normalizedUnitText = String(item.unit || "").trim() || "\u4efd";
        var quantity = [count, normalizedUnitText].join(" ").trim();
        return {
          name: String(item.name || "").trim(),
          count: count,
          quantity: quantity,
          quantity_text: quantity,
          unit: String(item.unit || "份").trim() || "份"
          , unit: normalizedUnitText
        };
      }),
      cooking_technique: normalizedTechnique,
      technique: normalizedTechnique,
      flavor_profile: resolveFlavorProfile({ tastes: normalizedTastes }),
      tastes: normalizedTastes,
      spice_level: 3,
      max_time: 30,
      equipment: normalizedTools,
      tools: normalizedTools,
      exclusions: normalizedExclusions,
      excluded_ingredients: normalizedExclusions,
      avoid_ingredients: normalizedExclusions,
      dietary_restrictions: normalizedExclusions
    };
  }

  function extractPhotoDataUrl(photo) {
    if (!photo) {
      return "";
    }

    if (typeof photo.dataUrl === "string" && photo.dataUrl.indexOf("data:") === 0) {
      return photo.dataUrl;
    }

    if (typeof photo.src === "string" && photo.src.indexOf("data:") === 0) {
      return photo.src;
    }

    return "";
  }

  function fileToDataUrl(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onload = function () {
        resolve(typeof reader.result === "string" ? reader.result : "");
      };
      reader.onerror = function () {
        reject(reader.error || new Error("file-to-data-url-failed"));
      };
      reader.readAsDataURL(file);
    });
  }

  function fetchJson(url, options) {
    var requestOptions = options || {};
    var method = String(requestOptions.method || "GET").toUpperCase();
    var headers = Object.assign({}, requestOptions.headers || {});

    if (!headers["Content-Type"] && !headers["content-type"] && method !== "GET" && method !== "HEAD") {
      headers["Content-Type"] = "application/json";
    }

    return fetch(url, Object.assign({}, requestOptions, { headers: headers })).then(function (response) {
      return response.text().then(function (rawText) {
        var parsed = null;
        if (rawText) {
          try {
            parsed = JSON.parse(rawText);
          } catch (error) {
            parsed = { detail: rawText };
          }
        }

        if (!response.ok) {
          var detail = parsed && (parsed.detail || parsed.message);
          var error = new Error(detail || ("HTTP " + response.status));
          error.status = response.status;
          error.payload = parsed;
          throw error;
        }

        return parsed || {};
      });
    });
  }

  global.InstantFoodApiBridge = {
    STORAGE_KEYS: STORAGE_KEYS,
    getApiBaseUrl: getApiBaseUrl,
    buildApiUrl: buildApiUrl,
    getUserId: getUserId,
    readSelection: readSelection,
    buildRecipePayload: buildRecipePayload,
    writeCapturedImage: writeCapturedImage,
    readCapturedImage: readCapturedImage,
    writeCapturedImages: writeCapturedImages,
    readCapturedImages: readCapturedImages,
    clearCapturedImage: clearCapturedImage,
    readGenerationResult: readGenerationResult,
    writeGenerationResult: writeGenerationResult,
    clearGenerationResult: clearGenerationResult,
    extractPhotoDataUrl: extractPhotoDataUrl,
    fileToDataUrl: fileToDataUrl,
    fetchJson: fetchJson
  };
})(window);
