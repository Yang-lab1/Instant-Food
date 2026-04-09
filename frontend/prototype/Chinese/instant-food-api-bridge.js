(function (global) {
  "use strict";

  var STORAGE_KEYS = {
    apiBaseUrl: "instantFoodApiBaseUrl",
    userId: "instantFoodUserId",
    selection: "molecularReconstructSelection",
    capturedImage: "capturedImageDataUrl",
    generationResult: "generatedRecipeResult",
    boardPreview: "generatedBoardPreview"
  };
  var FIXED_YOGURT_PREVIEW = "../../assets/results/yogurt-bowl.svg";
  var FIXED_YOGURT_STEPS = [
    {
      title: "\u94fa\u597d\u9178\u5976\u5e95",
      instruction: "\u5c06\u539a\u9178\u5976\u94fa\u5165\u7897\u5e95\uff0c\u62b9\u6210\u5fae\u5fae\u9686\u8d77\u7684\u5f27\u9762\uff0c\u8ba9\u540e\u7eed\u6c34\u679c\u548c\u9ea6\u7247\u80fd\u7a33\u5b9a\u843d\u4f4d\u3002",
      duration_minutes: 2,
      tips: "\u9178\u5976\u4fdd\u6301\u51b7\u85cf\u72b6\u6001\uff0c\u53e3\u611f\u4f1a\u66f4\u7d27\u5b9e\u3002"
    },
    {
      title: "\u6446\u4e0a\u6c34\u679c\u4e0e\u8106\u6599",
      instruction: "\u628a\u84dd\u8393\u3001\u9999\u8549\u7247\u3001\u9ea6\u7247\u3001\u6930\u7247\u548c\u9ed1\u5de7\u514b\u529b\u8106\u7247\u4f9d\u6b21\u94fa\u5728\u8868\u9762\uff0c\u4e2d\u5fc3\u7559\u4e00\u70b9\u8d77\u4f0f\u611f\u3002",
      duration_minutes: 2,
      tips: "\u6c34\u679c\u96c6\u4e2d\u5728\u6b63\u9762\u533a\u57df\uff0c\u753b\u9762\u4f1a\u66f4\u50cf\u5b9e\u62cd\u6210\u54c1\u3002"
    },
    {
      title: "\u8865\u9f50\u6700\u540e\u70b9\u7f00",
      instruction: "\u6700\u540e\u8865\u4e0a\u4e00\u5757\u7126\u7cd6\u997c\u5e72\u505a\u6536\u5c3e\uff0c\u4fdd\u6301\u51b7\u98df\u51fa\u54c1\uff0c\u4e0d\u518d\u52a0\u70ed\u3002",
      duration_minutes: 1,
      tips: "\u62cd\u7167\u524d\u518d\u6492\u6930\u7247\uff0c\u8fb9\u7f18\u4f1a\u66f4\u5e72\u51c0\u3002"
    }
  ];
  var FIXED_YOGURT_RESULT = {
    success: true,
    source: "fixed-yogurt-bowl",
    title: "\u9178\u5976\u635e",
    summary: "\u539a\u9178\u5976\u6253\u5e95\uff0c\u914d\u84dd\u8393\u3001\u9999\u8549\u3001\u9ea6\u7247\u3001\u6930\u7247\u548c\u9ed1\u5de7\u514b\u529b\u8106\u7247\uff0c\u7ed3\u679c\u9875\u56fa\u5b9a\u8f93\u51fa\u8fd9\u4e00\u7897\u3002",
    imageUrl: FIXED_YOGURT_PREVIEW,
    boardPreview: FIXED_YOGURT_PREVIEW,
    technique: "\u51b7\u62cc\u88c5\u7897",
    tastes: ["\u6e05\u723d", "\u679c\u9999"],
    recognition: {
      cooking_method: "\u51b7\u62cc\u88c5\u7897"
    },
    recipe: {
      title: "\u9178\u5976\u635e",
      title_zh: "\u9178\u5976\u635e",
      description: "\u539a\u9178\u5976\u6253\u5e95\uff0c\u642d\u914d\u84dd\u8393\u3001\u9999\u8549\u3001\u9ea6\u7247\u3001\u6930\u7247\u548c\u9ed1\u5de7\u514b\u529b\u8106\u7247\uff0c\u51b7\u98df\u5373\u53ef\u3002",
      ingredients: [
        { name: "\u539a\u9178\u5976", quantity: "1", unit: "\u7897" },
        { name: "\u84dd\u8393", quantity: "4", unit: "\u9897" },
        { name: "\u9999\u8549\u7247", quantity: "3", unit: "\u7247" },
        { name: "\u683c\u5170\u8bfa\u62c9\u9ea6\u7247", quantity: "1", unit: "\u52fa" },
        { name: "\u6930\u7247", quantity: "\u9002\u91cf", unit: "" },
        { name: "\u9ed1\u5de7\u514b\u529b\u8106\u7247", quantity: "1", unit: "\u5757" },
        { name: "\u7126\u7cd6\u997c\u5e72", quantity: "1", unit: "\u5757" }
      ],
      steps: FIXED_YOGURT_STEPS,
      tips: "\u65e0\u8bba\u4e0a\u4f20\u4ec0\u4e48\u56fe\u7247\u6216\u6587\u6848\uff0c\u8fd9\u4e2a\u5206\u652f\u90fd\u56fa\u5b9a\u5c55\u793a\u8fd9\u4efd\u9178\u5976\u635e\u7ed3\u679c\u3002"
    },
    steps: FIXED_YOGURT_STEPS
  };

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

  function cloneJsonValue(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function normalizeBaseUrl(rawValue) {
    var value = String(rawValue || "").trim();
    return value.replace(/\/+$/, "");
  }

  function getApiBaseUrl(view) {
    var win = view || global;
    var params = new URLSearchParams((win.location && win.location.search) || "");
    var explicitBase =
      global.__INSTANT_FOOD_API_BASE_URL__ ||
      params.get("apiBaseUrl") ||
      readStorage(win.localStorage, STORAGE_KEYS.apiBaseUrl) ||
      readStorage(win.sessionStorage, STORAGE_KEYS.apiBaseUrl) ||
      "";

    return normalizeBaseUrl(explicitBase);
  }

  function buildApiUrl(path, view) {
    var normalizedPath = String(path || "").trim();
    if (!normalizedPath) {
      return "";
    }

    if (/^https?:\/\//i.test(normalizedPath)) {
      return normalizedPath;
    }

    if (normalizedPath.charAt(0) !== "/") {
      normalizedPath = "/" + normalizedPath;
    }

    var apiBaseUrl = getApiBaseUrl(view);
    return apiBaseUrl ? apiBaseUrl + normalizedPath : normalizedPath;
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
    return writeStorage(win.sessionStorage, STORAGE_KEYS.capturedImage, String(dataUrl || ""));
  }

  function readCapturedImage(view) {
    var win = view || global;
    return readStorage(win.sessionStorage, STORAGE_KEYS.capturedImage) || "";
  }

  function clearCapturedImage(view) {
    var win = view || global;
    writeStorage(win.sessionStorage, STORAGE_KEYS.capturedImage, "");
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

  function getFixedYogurtResult() {
    return cloneJsonValue(FIXED_YOGURT_RESULT);
  }

  function resolveFlavorProfile(selection) {
    var tastes = Array.isArray(selection && selection.tastes) ? selection.tastes : [];
    if (!tastes.length) {
      return "家常";
    }
    return tastes[0];
  }

  function buildRecipePayload(selection) {
    var safeSelection = selection || {};
    var ingredients = Array.isArray(safeSelection.ingredients) ? safeSelection.ingredients : [];
    var includedIngredients = ingredients.filter(function (item) {
      return item && item.included !== false && String(item.name || "").trim();
    });

    return {
      ingredients: includedIngredients.map(function (item) {
        return {
          name: String(item.name || "").trim(),
          count: Number(item.count || 0) || 1,
          unit: String(item.unit || "份").trim() || "份"
        };
      }),
      cooking_technique: String(safeSelection.technique || "").trim(),
      technique: String(safeSelection.technique || "").trim(),
      flavor_profile: resolveFlavorProfile(safeSelection),
      tastes: Array.isArray(safeSelection.tastes) ? safeSelection.tastes : [],
      spice_level: 3,
      max_time: 30,
      equipment: Array.isArray(safeSelection.tools) ? safeSelection.tools : [],
      tools: Array.isArray(safeSelection.tools) ? safeSelection.tools : []
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
    var headers = Object.assign(
      { "Content-Type": "application/json" },
      requestOptions.headers || {}
    );

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
    clearCapturedImage: clearCapturedImage,
    readGenerationResult: readGenerationResult,
    writeGenerationResult: writeGenerationResult,
    clearGenerationResult: clearGenerationResult,
    getFixedYogurtResult: getFixedYogurtResult,
    extractPhotoDataUrl: extractPhotoDataUrl,
    fileToDataUrl: fileToDataUrl,
    fetchJson: fetchJson
  };
})(window);
