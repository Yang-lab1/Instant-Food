import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchAiStatus, generateFromImage, generateRecipe, saveRecipe } from "../lib/api";

const defaultForm = {
  ingredients: "番茄, 鸡蛋, 葱",
  cooking_technique: "炒",
  flavor_profile: "家常",
  spice_level: 1,
  max_time: 20,
  equipment: "炒锅",
  image_url: ""
};

export function CapturePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(defaultForm);
  const [aiStatus, setAiStatus] = useState({ loading: true, error: "", data: null });
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState({ loading: false, error: "", saved: "" });
  const [captureFlash, setCaptureFlash] = useState(false);
  const [captureBadge, setCaptureBadge] = useState("");
  const [draggedImageId, setDraggedImageId] = useState("");
  const [cameraState, setCameraState] = useState({
    active: false,
    loading: false,
    error: ""
  });
  const [selectedImages, setSelectedImages] = useState([]);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const flashTimerRef = useRef(null);
  const badgeTimerRef = useRef(null);
  const teachingIngredients = buildTeachingIngredients(result);
  const teachingSteps = buildTeachingSteps(result);
  const teachingSummary = buildTeachingSummary(result);

  useEffect(() => {
    fetchAiStatus()
      .then((data) => setAiStatus({ loading: false, error: "", data }))
      .catch((error) =>
        setAiStatus({ loading: false, error: error.message, data: null })
      );

    return () => {
      stopCameraStream();
      if (flashTimerRef.current) {
        window.clearTimeout(flashTimerRef.current);
      }
      if (badgeTimerRef.current) {
        window.clearTimeout(badgeTimerRef.current);
      }
    };
  }, []);

  async function handleGenerate(event) {
    event.preventDefault();
    setStatus({ loading: true, error: "", saved: "" });
    setResult(null);
    try {
      const payload = await generateRecipe({
        ingredients: form.ingredients
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        cooking_technique: form.cooking_technique,
        flavor_profile: form.flavor_profile,
        spice_level: Number(form.spice_level),
        max_time: Number(form.max_time),
        equipment: form.equipment
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      });
      setResult(payload.recipe);
      setStatus({ loading: false, error: "", saved: "" });
    } catch (error) {
      setStatus({ loading: false, error: error.message, saved: "" });
    }
  }

  async function handleImageGenerate() {
    if (!selectedImages.length && !form.image_url.trim()) {
      setStatus({ loading: false, error: "请先拍摄/上传图片，或填写图片 URL。", saved: "" });
      return;
    }
    setStatus({ loading: true, error: "", saved: "" });
    setResult(null);
    try {
      const mergedBase64 = selectedImages.length
        ? await buildCollageBase64(selectedImages)
        : "";
      const payload = await generateFromImage(
        mergedBase64
          ? { image_base64: mergedBase64 }
          : { image_url: form.image_url.trim() }
      );
      setResult({
        ...payload.recipe,
        recognizedIngredients: payload.recognition?.ingredients || []
      });
      setStatus({ loading: false, error: "", saved: "" });
    } catch (error) {
      setStatus({ loading: false, error: error.message, saved: "" });
    }
  }

  function handleFileChange(event) {
    const files = Array.from(event.target.files || []);
    files.slice(0, Math.max(0, 9 - selectedImages.length)).forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = typeof reader.result === "string" ? reader.result : "";
        const base64 = result.includes(",") ? result.split(",")[1] : result;
        appendImage({
          id: createImageId(),
          fileName: file.name,
          previewUrl: result,
          base64
        });
      };
      reader.readAsDataURL(file);
    });
    setStatus({ loading: false, error: "", saved: "" });
    event.target.value = "";
  }

  function appendImage(image) {
    setSelectedImages((current) => {
      if (current.length >= 9) {
        return current;
      }
      const next = [...current, image];
      showCaptureFeedback(next.length);
      return next;
    });
  }

  function removeSelectedImage(imageId) {
    setSelectedImages((current) => current.filter((item) => item.id !== imageId));
  }

  function moveImage(fromId, toId) {
    if (!fromId || !toId || fromId === toId) {
      return;
    }
    setSelectedImages((current) => {
      const fromIndex = current.findIndex((item) => item.id === fromId);
      const toIndex = current.findIndex((item) => item.id === toId);
      if (fromIndex === -1 || toIndex === -1) {
        return current;
      }
      const next = [...current];
      const [moved] = next.splice(fromIndex, 1);
      next.splice(toIndex, 0, moved);
      return next;
    });
  }

  function clearSelectedImages() {
    setSelectedImages([]);
  }

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraState({
        active: false,
        loading: false,
        error: "当前浏览器不支持摄像头调用。"
      });
      return;
    }

    setCameraState({ active: false, loading: true, error: "" });

    try {
      stopCameraStream();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraState({ active: true, loading: false, error: "" });
      setStatus({ loading: false, error: "", saved: "" });
    } catch (error) {
      setCameraState({
        active: false,
        loading: false,
        error: error.message || "摄像头启动失败。"
      });
    }
  }

  function stopCameraStream() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }

  function stopCamera() {
    stopCameraStream();
    setCameraState({ active: false, loading: false, error: "" });
  }

  function captureFrame() {
    if (!videoRef.current) {
      return;
    }

    const video = videoRef.current;
    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) {
      setCameraState((current) => ({
        ...current,
        error: "当前环境无法生成截图。"
      }));
      return;
    }

    context.drawImage(video, 0, 0, width, height);
    const previewUrl = canvas.toDataURL("image/jpeg", 0.92);
    const base64 = previewUrl.split(",")[1] || "";
    appendImage({
      id: createImageId(),
      fileName: `capture-${Date.now()}.jpg`,
      previewUrl,
      base64
    });
    setStatus({ loading: false, error: "", saved: "" });
  }

  async function handleSave() {
    if (!result) {
      return;
    }
    setStatus({ loading: true, error: "", saved: "" });
    try {
      const payload = await saveRecipe({
        title: result.title || result.title_zh,
        title_zh: result.title_zh || result.title,
        description: result.description,
        description_zh: result.description,
        cuisine_type: "AI 生成",
        meal_type: "待分类",
        difficulty: "medium",
        prep_time_minutes: 0,
        cook_time_minutes: 0,
        servings: 2,
        calories_per_serving: result.nutrition?.calories_per_serving || null,
        image_url: null,
        ingredients: (result.ingredients || []).map((item) => ({
          name: item.name,
          quantity: item.quantity || item.estimated_quantity || "适量",
          unit: item.unit || "",
          notes: item.notes || ""
        })),
        steps: (result.steps || []).map((step) => ({
          instruction: step.instruction,
          duration_minutes: step.duration_minutes || 0,
          tips: step.tips || ""
        })),
        is_published: true,
        source: "ai_generated"
      });
      const savedRecipeId = payload.recipe?.id;
      setStatus({ loading: false, error: "", saved: "已保存到 recipes 表，正在跳转详情页。" });
      if (savedRecipeId) {
        window.setTimeout(() => {
          navigate(`/recipes/${savedRecipeId}`);
        }, 500);
      }
    } catch (error) {
      setStatus({ loading: false, error: error.message, saved: "" });
    }
  }

  function showCaptureFeedback(count) {
    setCaptureFlash(true);
    setCaptureBadge(`已捕捉 ${count} / 9 张`);
    if (flashTimerRef.current) {
      window.clearTimeout(flashTimerRef.current);
    }
    if (badgeTimerRef.current) {
      window.clearTimeout(badgeTimerRef.current);
    }
    flashTimerRef.current = window.setTimeout(() => {
      setCaptureFlash(false);
    }, 260);
    badgeTimerRef.current = window.setTimeout(() => {
      setCaptureBadge("");
    }, 1800);
  }

  return (
    <section className="page-stack">
      <header className="hero-panel capture-hero">
        <div>
          <p className="eyebrow">Generate</p>
          <h2>拍摄 / 生成</h2>
          <p className="hero-copy">
            先把静态“拍摄页”转换成真正的数据交互页。文字生成走后端，后续再补真实摄像头和生图能力。
          </p>
        </div>
        <div className="ai-status-box">
          <strong>AI 状态</strong>
          {aiStatus.loading ? <p>检查中...</p> : null}
          {aiStatus.error ? <p>{aiStatus.error}</p> : null}
          {aiStatus.data ? (
            <p>
              {aiStatus.data.provider} / {aiStatus.data.model}
            </p>
          ) : null}
        </div>
      </header>

      <div className="capture-layout">
        <form className="form-panel" onSubmit={handleGenerate}>
          <section className="upload-panel">
            <div className="upload-panel-head">
              <div>
                <p className="eyebrow">Image Input</p>
                <h3>拍摄原材料，最多 9 张</h3>
              </div>
              <div className="inline-actions">
                {!cameraState.active ? (
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={startCamera}
                    disabled={cameraState.loading}
                  >
                    {cameraState.loading ? "启动中..." : "打开摄像头"}
                  </button>
                ) : (
                  <button type="button" className="ghost-button" onClick={stopCamera}>
                    关闭摄像头
                  </button>
                )}
                {selectedImages.length ? (
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={clearSelectedImages}
                  >
                    清空图片
                  </button>
                ) : null}
              </div>
            </div>
            <div className="camera-stage">
              {cameraState.active ? (
                <div className="camera-live-shell">
                  <video
                    ref={videoRef}
                    className="camera-preview"
                    playsInline
                    muted
                    autoPlay
                  />
                  {captureFlash ? <div className="camera-flash" /> : null}
                  {captureBadge ? <div className="capture-badge">{captureBadge}</div> : null}
                  <div className="camera-overlay">
                    <div className="camera-guide" />
                    <button
                      type="button"
                      className="shutter-button"
                      onClick={captureFrame}
                      disabled={selectedImages.length >= 9}
                      aria-label="拍照"
                      title={selectedImages.length >= 9 ? "最多保存 9 张" : "拍照"}
                    >
                      <span />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="camera-placeholder">
                  <strong>实时取景区</strong>
                  <p>打开摄像头后可连续抓拍原材料图片，最多保存 9 张，再一起分析生成菜谱。</p>
                </div>
              )}
            </div>
            {cameraState.error ? (
              <div className="message-panel message-panel-error">
                <strong>摄像头不可用</strong>
                <p>{cameraState.error}</p>
              </div>
            ) : null}
            <label className="upload-dropzone">
              <input
                type="file"
                multiple
                accept="image/png,image/jpeg,image/webp"
                onChange={handleFileChange}
                disabled={selectedImages.length >= 9}
              />
              {selectedImages.length ? (
                <div className="upload-gallery">
                  {selectedImages.map((image, index) => (
                    <figure
                      key={image.id}
                      className={
                        draggedImageId === image.id
                          ? "gallery-card gallery-card-dragging"
                          : "gallery-card"
                      }
                      draggable
                      onDragStart={() => setDraggedImageId(image.id)}
                      onDragEnd={() => setDraggedImageId("")}
                      onDragOver={(event) => {
                        event.preventDefault();
                      }}
                      onDrop={(event) => {
                        event.preventDefault();
                        moveImage(draggedImageId, image.id);
                        setDraggedImageId("");
                      }}
                    >
                      <img
                        src={image.previewUrl}
                        alt={`待识别图片 ${index + 1}`}
                        className="upload-preview"
                      />
                      <figcaption>
                        <span>第 {index + 1} 张</span>
                        <button
                          type="button"
                          className="ghost-button ghost-button-inline"
                          onClick={(event) => {
                            event.preventDefault();
                            removeSelectedImage(image.id);
                          }}
                        >
                          删除
                        </button>
                      </figcaption>
                    </figure>
                  ))}
                </div>
              ) : (
                <div className="upload-placeholder">
                  <strong>上传本地原材料图</strong>
                  <p>支持 JPG / PNG / WEBP。也可以先打开摄像头抓拍，再把最多 9 张图一起送进后端分析。</p>
                </div>
              )}
            </label>
            <p className="image-counter">
              已选择 {selectedImages.length} / 9 张图片。拖拽缩略图可调整分析顺序。
            </p>
            <label>
              图片 URL（备用）
              <input
                value={form.image_url}
                onChange={(event) =>
                  setForm({ ...form, image_url: event.target.value })
                }
                placeholder="https://example.com/food.jpg"
              />
            </label>
          </section>

          <label>
            食材
            <textarea
              value={form.ingredients}
              onChange={(event) =>
                setForm({ ...form, ingredients: event.target.value })
              }
              rows={4}
            />
          </label>
          <div className="form-grid">
            <label>
              烹饪技法
              <input
                value={form.cooking_technique}
                onChange={(event) =>
                  setForm({ ...form, cooking_technique: event.target.value })
                }
              />
            </label>
            <label>
              风味
              <input
                value={form.flavor_profile}
                onChange={(event) =>
                  setForm({ ...form, flavor_profile: event.target.value })
                }
              />
            </label>
            <label>
              辣度
              <input
                type="number"
                min="1"
                max="5"
                value={form.spice_level}
                onChange={(event) =>
                  setForm({ ...form, spice_level: event.target.value })
                }
              />
            </label>
            <label>
              最大时长
              <input
                type="number"
                min="5"
                max="180"
                value={form.max_time}
                onChange={(event) =>
                  setForm({ ...form, max_time: event.target.value })
                }
              />
            </label>
          </div>
          <label>
            可用厨具
            <input
              value={form.equipment}
              onChange={(event) =>
                setForm({ ...form, equipment: event.target.value })
              }
            />
          </label>
          <div className="button-row">
            <button type="submit" disabled={status.loading}>
              {status.loading ? "生成中..." : "用食材生成"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={handleImageGenerate}
              disabled={status.loading}
            >
              从图片生成
            </button>
          </div>
          {status.error ? (
            <div className="message-panel message-panel-error">
              <strong>生成失败</strong>
              <p>{status.error}</p>
            </div>
          ) : null}
          {status.saved ? (
            <div className="message-panel message-panel-success">
              <strong>保存成功</strong>
              <p>{status.saved}</p>
            </div>
          ) : null}
        </form>

        <section className="result-panel">
          {!result ? (
            <div className="message-panel message-panel-empty">
              <strong>等待生成</strong>
              <p>这里会展示模型返回的菜谱结果，并支持一键保存回 Supabase。你可以上传图片进行识别，也可以直接输入食材生成。</p>
            </div>
          ) : (
            <>
              <div className="result-head">
                <div>
                  <p className="eyebrow">Generated Recipe</p>
                  <h3>{result.title_zh || result.title}</h3>
                  <p>{result.description}</p>
                </div>
                <button onClick={handleSave} disabled={status.loading}>
                  保存到食谱库
                </button>
              </div>
              {result.recognizedIngredients?.length ? (
                <section className="detail-panel recognized-panel">
                  <div className="section-head">
                    <div>
                      <p className="eyebrow">Ingredient Map</p>
                      <h3>识别到的原材料</h3>
                    </div>
                    <span className="section-meta">共 {result.recognizedIngredients.length} 项</span>
                  </div>
                  <div className="tag-cloud">
                    {result.recognizedIngredients.map((item, index) => (
                      <span key={`${item.name}-${index}`} className="ingredient-tag">
                        {item.name}
                        {item.confidence ? ` · ${Math.round(item.confidence * 100)}%` : ""}
                      </span>
                    ))}
                  </div>
                </section>
              ) : null}
              {teachingIngredients.length ? (
                <section className="detail-panel ingredient-atlas-panel">
                  <div className="section-head">
                    <div>
                      <p className="eyebrow">Atlas</p>
                      <h3>食材图谱介绍</h3>
                    </div>
                    <span className="section-meta">帮你先认识原材料，再开始做</span>
                  </div>
                  <div className="ingredient-atlas-grid">
                    {teachingIngredients.map((item, index) => (
                      <article key={`${item.name}-${index}`} className="ingredient-atlas-card">
                        <div className="ingredient-atlas-top">
                          <span className="ingredient-atlas-index">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                          <span className="ingredient-atlas-amount">{item.amount}</span>
                        </div>
                        <strong>{item.name}</strong>
                        <p>{item.intro}</p>
                        <div className="atlas-chip-row">
                          <span>{item.role}</span>
                          <span>{item.action}</span>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              ) : null}
              <div className="detail-columns">
                <section className="detail-panel">
                  <div className="section-head">
                    <div>
                      <p className="eyebrow">Ingredients</p>
                      <h3>食材清单</h3>
                    </div>
                    <span className="section-meta">生成结果可直接保存到 recipes</span>
                  </div>
                  <ul className="list-block">
                    {(result.ingredients || []).map((item, index) => (
                      <li key={`${item.name}-${index}`}>
                        <span>{item.name}</span>
                        <span>{item.quantity || item.estimated_quantity || "适量"}</span>
                      </li>
                    ))}
                  </ul>
                </section>
                <section className="detail-panel">
                  <div className="section-head">
                    <div>
                      <p className="eyebrow">Tutorial</p>
                      <h3>做法流程教学</h3>
                    </div>
                    <span className="section-meta">
                      {teachingSteps.length ? `共 ${teachingSteps.length} 步` : "暂无步骤"}
                    </span>
                  </div>
                  {teachingSteps.length ? (
                    <ol className="teaching-timeline">
                      {teachingSteps.map((step) => (
                        <li key={step.id} className="teaching-step-card">
                          <div className="teaching-step-marker">
                            <span>{step.number}</span>
                          </div>
                          <div className="teaching-step-body">
                            <div className="teaching-step-head">
                              <strong>{step.title}</strong>
                              <span>{step.duration}</span>
                            </div>
                            <p>{step.instruction}</p>
                            <div className="teaching-tip-box">
                              <span>教学提示</span>
                              <p>{step.tip}</p>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <div className="message-panel message-panel-empty">
                      <strong>暂无步骤</strong>
                      <p>当前结果还没有返回完整流程，稍后可以继续补一轮生成。</p>
                    </div>
                  )}
                </section>
              </div>
              {teachingSummary.length ? (
                <section className="detail-panel teaching-summary-panel">
                  <div className="section-head">
                    <div>
                      <p className="eyebrow">Coach Notes</p>
                      <h3>上手提醒</h3>
                    </div>
                    <span className="section-meta">做之前先看这一栏</span>
                  </div>
                  <div className="summary-grid">
                    {teachingSummary.map((item, index) => (
                      <article key={`${item.label}-${index}`} className="summary-card">
                        <span>{item.label}</span>
                        <strong>{item.value}</strong>
                      </article>
                    ))}
                  </div>
                </section>
              ) : null}
            </>
          )}
        </section>
      </div>
    </section>
  );
}

function createImageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

async function buildCollageBase64(images) {
  const tileCount = Math.min(images.length, 9);
  const columns = tileCount <= 1 ? 1 : tileCount <= 4 ? 2 : 3;
  const rows = Math.ceil(tileCount / columns);
  const tileSize = 512;
  const gap = 20;
  const width = columns * tileSize + (columns + 1) * gap;
  const height = rows * tileSize + (rows + 1) * gap;

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("当前浏览器无法创建拼图画布。");
  }

  context.fillStyle = "#08110e";
  context.fillRect(0, 0, width, height);

  const loadedImages = await Promise.all(
    images.slice(0, 9).map(
      (item) =>
        new Promise((resolve, reject) => {
          const img = new Image();
          img.onload = () => resolve(img);
          img.onerror = () => reject(new Error("图片拼接失败。"));
          img.src = item.previewUrl;
        })
    )
  );

  loadedImages.forEach((img, index) => {
    const row = Math.floor(index / columns);
    const col = index % columns;
    const x = gap + col * (tileSize + gap);
    const y = gap + row * (tileSize + gap);
    drawCoverImage(context, img, x, y, tileSize, tileSize);
  });

  const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
  return dataUrl.split(",")[1] || "";
}

function drawCoverImage(context, image, x, y, width, height) {
  const sourceRatio = image.width / image.height;
  const targetRatio = width / height;

  let sx = 0;
  let sy = 0;
  let sWidth = image.width;
  let sHeight = image.height;

  if (sourceRatio > targetRatio) {
    sWidth = image.height * targetRatio;
    sx = (image.width - sWidth) / 2;
  } else {
    sHeight = image.width / targetRatio;
    sy = (image.height - sHeight) / 2;
  }

  context.drawImage(image, sx, sy, sWidth, sHeight, x, y, width, height);
}

function buildTeachingIngredients(result) {
  return (result?.ingredients || []).map((item, index) => {
    const quantity = item.quantity || item.estimated_quantity || "适量";
    const unit = item.unit || "";
    const notes = item.notes || "";
    const amount = `${quantity}${unit}`.trim() || "适量";

    return {
      name: item.name || `食材 ${index + 1}`,
      amount,
      role: inferIngredientRole(item.name, index),
      action: inferIngredientAction(item.name),
      intro: notes || `${item.name || "这份食材"}建议提前洗净、切好，方便下锅时更顺手。`
    };
  });
}

function buildTeachingSteps(result) {
  return (result?.steps || []).map((step, index) => ({
    id: `${index}-${step.instruction}`,
    number: String(index + 1).padStart(2, "0"),
    title: inferStepTitle(step.instruction, index),
    instruction: step.instruction,
    duration: step.duration_minutes ? `${step.duration_minutes} 分钟` : "按状态灵活调整",
    tip: step.tips || inferStepTip(step.instruction, index)
  }));
}

function buildTeachingSummary(result) {
  const ingredients = result?.ingredients || [];
  const steps = result?.steps || [];
  const recognized = result?.recognizedIngredients || [];
  const totalMinutes = steps.reduce(
    (sum, item) => sum + Number(item.duration_minutes || 0),
    0
  );

  return [
    {
      label: "原材料",
      value: recognized.length ? `${recognized.length} 项已识别` : `${ingredients.length} 项待处理`
    },
    {
      label: "节奏",
      value: steps.length ? `${steps.length} 步完成一餐` : "等待模型返回步骤"
    },
    {
      label: "时长",
      value: totalMinutes > 0 ? `约 ${totalMinutes} 分钟` : "按现场火候判断"
    }
  ];
}

function inferIngredientRole(name, index) {
  const text = name || "";
  if (/葱|姜|蒜|椒|香菜/.test(text)) {
    return "提香点睛";
  }
  if (/盐|糖|酱|醋|油|料酒|蚝油|生抽|老抽/.test(text)) {
    return "调味关键";
  }
  if (/蛋|肉|鸡|虾|鱼|豆腐/.test(text)) {
    return "主体蛋白";
  }
  if (/番茄|土豆|青椒|洋葱|菌|白菜|生菜|黄瓜/.test(text)) {
    return "主蔬菜";
  }
  return index === 0 ? "核心主料" : "辅助配料";
}

function inferIngredientAction(name) {
  const text = name || "";
  if (/葱|姜|蒜|椒|洋葱/.test(text)) {
    return "建议切碎爆香";
  }
  if (/肉|鸡|虾|鱼/.test(text)) {
    return "建议提前腌制";
  }
  if (/蛋/.test(text)) {
    return "建议先打散";
  }
  if (/番茄|土豆|黄瓜|白菜|豆腐/.test(text)) {
    return "建议切块备用";
  }
  return "建议洗净备料";
}

function inferStepTitle(instruction, index) {
  const text = instruction || "";
  if (/洗|切|备|腌/.test(text)) {
    return "备料阶段";
  }
  if (/热锅|下油|爆香/.test(text)) {
    return "起锅增香";
  }
  if (/翻炒|炒/.test(text)) {
    return "主火翻炒";
  }
  if (/煮|焖|炖/.test(text)) {
    return "加热收味";
  }
  if (/装盘|出锅/.test(text)) {
    return "完成装盘";
  }
  return `步骤 ${index + 1}`;
}

function inferStepTip(instruction, index) {
  const text = instruction || "";
  if (/洗|切|备|腌/.test(text)) {
    return "先把所有原材料按顺序摆好，正式下锅时会更顺手。";
  }
  if (/热锅|下油|爆香/.test(text)) {
    return "锅热后再下油和香料，能减少粘锅，也更容易把香味带出来。";
  }
  if (/翻炒|炒/.test(text)) {
    return "保持中大火快速翻动，避免局部受热过度。";
  }
  if (/煮|焖|炖/.test(text)) {
    return "这一步更看重时间和火候，建议边观察汤汁边调整。";
  }
  if (/装盘|出锅/.test(text)) {
    return "临出锅前再试一次味道，确认咸淡和口感。";
  }
  if (index === 0) {
    return "先完成准备动作，后面每一步都会更轻松。";
  }
  return "跟着节奏一步一步来，看到状态变化再决定下一步。";
}
