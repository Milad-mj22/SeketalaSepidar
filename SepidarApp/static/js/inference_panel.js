/**
 * inference_panel.js
 * Single-file client-side logic for the AI Inference Panel.
 * Place at: <your_app>/static/js/inference_panel.js
 */

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────────────────────────────────────
window.INFERENCE_CONFIG = window.INFERENCE_CONFIG || readInferenceConfig();
const CFG = window.INFERENCE_CONFIG;
const CSRF = CFG.csrfToken || getCookie("csrftoken");

// ─────────────────────────────────────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────────────────────────────────────
/** @type {{ file: File, id: string, selected: boolean, objectUrl?: string | null }[]} */
let imageItems = [];
let previewId = null;
let selectedModel = null;
let tempSelectedModel = null;
let selectedProject = null;
let inferenceComplete = false;
let allSelected = false;

let lpAllProjects = [];
let lpPage = 1;
let lpHasMore = false;
const LP_PAGE_SIZE = 15;
const POLL_INTERVAL_MS = 2000;
const AUTO_SAVE_DEBOUNCE_MS = 700;

let allModels = [];
const DEFAULT_MODEL_SORT = Object.freeze({ key: "date", direction: "desc" });
let modelSortState = { ...DEFAULT_MODEL_SORT };

let currentJobId = null;
let pollInterval = null;
let lastProgressApplied = -1;
let lastTerminalState = null;

// ─────────────────────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", initInferencePanel);

function initInferencePanel() {
  bindFileUpload();
  bindProjectNameCheck();
  bindProjectModal();
  bindModelModal();
  updateBadge();
  syncInferenceStages();
}

function bindFileUpload() {
  const fileInput = byId("file-input");
  if (fileInput)
    fileInput.addEventListener("change", () => handleFileSelect(fileInput));
}

function bindProjectNameCheck() {
  const projectNameInput = byId("project-name");
  if (!projectNameInput || !CFG.checkProjectNameUrl) return;

  projectNameInput.addEventListener(
    "input",
    debounce(() => checkProjectName(projectNameInput.value.trim()), 500),
  );
}

function bindProjectModal() {
  byId("lp-search")?.addEventListener("input", debounce(applyProjectFilters, 350));
  byId("lp-date-filter")?.addEventListener("change", applyProjectFilters);
  byId("lp-inferred-filter")?.addEventListener("change", applyProjectFilters);

  // These buttons may already have inline onclick handlers in the template.
  // Assigning onclick here replaces the inline handler instead of stacking
  // another listener on top of it, which prevents duplicate actions/toasts.
  bindButtonClick("btn-lp-load-more", loadMoreProjects);
  bindButtonClick("btn-confirm-load-project", confirmLoadProject);

  const modal = byId("kt_modal_load_project");
  if (!modal) return;

  modal.addEventListener("show.bs.modal", () => {
    resetProjectModal();
    fetchProjects();
  });
}

function bindModelModal() {
  byId("model-search")?.addEventListener(
    "input",
    debounce(applyModelFilters, 350),
  );
  byId("model-filter-accuracy")?.addEventListener(
    "input",
    debounce(applyModelFilters, 350),
  );
  byId("model-filter-iou")?.addEventListener(
    "input",
    debounce(applyModelFilters, 350),
  );
  bindModelSortButtons();

  // Same reason as project modal: avoid inline onclick + JS listener double fire.
  bindButtonClick("btn-confirm-model", confirmModelSelection);

  const modal = byId("kt_modal_select_model");
  if (!modal) return;

  modal.addEventListener("show.bs.modal", () => {
    resetModelModal();
    fetchModels();
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE STAGE STATE
// ─────────────────────────────────────────────────────────────────────────────
function hasImagesReady() {
  return imageItems.length > 0;
}

function hasModelReady() {
  return Boolean(selectedModel && selectedModel.id);
}

function syncInferenceStages() {
  const hasImages = hasImagesReady();
  const hasModel = hasModelReady();
  const readyToRun = hasImages && hasModel;

  const modelFieldset = byId("model-settings-fieldset");
  if (modelFieldset) modelFieldset.disabled = !hasImages;

  const runButton = byId("btn-run-model");
  if (runButton) runButton.disabled = !readyToRun;

  if (!inferenceComplete && !currentJobId) {
    if (!hasImages) {
      setText("run-status-label", "ابتدا تصاویر را بارگذاری کنید");
    } else if (!hasModel) {
      setText("run-status-label", "مدل را انتخاب کنید");
    } else {
      setText("run-status-label", "آماده برای اجرا");
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PROJECT NAME CHECK
// ─────────────────────────────────────────────────────────────────────────────
async function checkProjectName(name) {
  const errorEl = byId("project-name-error");
  if (!errorEl || !name || !CFG.checkProjectNameUrl) {
    errorEl?.classList.add("d-none");
    return;
  }

  try {
    const data = await fetchJson(
      `${CFG.checkProjectNameUrl}?name=${encodeURIComponent(name)}`,
    );
    errorEl.classList.toggle("d-none", !data.exists);
    syncInferenceStages();
  } catch (err) {
    console.warn("Project name check failed:", err);
    errorEl.classList.add("d-none");
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// LOAD PROJECT MODAL
// ─────────────────────────────────────────────────────────────────────────────
function resetProjectModal() {
  lpAllProjects = [];
  lpPage = 1;
  lpHasMore = false;
  selectedProject = null;

  setValue("lp-search", "");
  setValue("lp-date-filter", "");
  setValue("lp-inferred-filter", "");
  setDisabled("btn-confirm-load-project", true);
  showProjectLoading();
}

function showProjectLoading() {
  show("lp-loading");
  hide("lp-empty");
  hide("lp-list");
  hide("lp-load-more-wrap");
}

async function fetchProjects(append = false) {
  if (!CFG.loadProjectsUrl) {
    showToast("آدرس بارگذاری پروژه‌ها تنظیم نشده است", "danger");
    return;
  }

  if (!append) showProjectLoading();

  const url = new URL(CFG.loadProjectsUrl, window.location.origin);
  url.searchParams.set("page", String(lpPage));
  url.searchParams.set("page_size", String(LP_PAGE_SIZE));

  try {
    const data = await fetchJson(url.toString());
    const projects = Array.isArray(data) ? data : data.results || [];

    lpHasMore = Boolean(data.next);
    lpAllProjects = append ? lpAllProjects.concat(projects) : projects;

    hide("lp-loading");
    renderProjectList(lpAllProjects);
    toggle("lp-load-more-wrap", lpHasMore);
  } catch (err) {
    hide("lp-loading");
    showToast("بارگذاری پروژه‌ها انجام نشد. لطفاً دوباره تلاش کنید.", "error", {
      serverMessage: err.message,
    });
  }
}

function loadMoreProjects() {
  if (!lpHasMore) return;
  lpPage += 1;
  fetchProjects(true);
}

function applyProjectFilters() {
  const search = getValue("lp-search").toLowerCase();
  const date = getValue("lp-date-filter");
  const inferred = getValue("lp-inferred-filter");

  const filtered = lpAllProjects.filter((project) => {
    const name = String(project.project_name || "").toLowerCase();
    const createdDate = String(project.created_date || "");
    const isInferred = String(Boolean(project.is_inferred));

    return (
      (!search || name.includes(search)) &&
      (!date || createdDate.startsWith(date)) &&
      (!inferred || isInferred === inferred)
    );
  });

  renderProjectList(filtered);
}

function renderProjectList(projects) {
  const list = byId("lp-list");
  const empty = byId("lp-empty");
  if (!list || !empty) return;

  list.innerHTML = "";

  if (!projects.length) {
    show("lp-empty");
    hide("lp-list");
    return;
  }

  hide("lp-empty");
  show("lp-list");

  projects.forEach((project) => {
    const item = createProjectItem(project);
    item.addEventListener("click", () => selectProjectInModal(project));
    list.appendChild(item);
  });
}

function createProjectItem(project) {
  const isSelected = selectedProject?.id === project.id;
  const createdDate = formatFaDate(project.created_date, "—");
  const lastLoaded = formatFaDate(project.last_loaded, "هرگز");
  const projectName = project.project_name || "بدون نام";
  const div = document.createElement("div");

  div.className =
    "lp-item d-flex align-items-center gap-3 p-4 rounded mb-2 cursor-pointer";
  div.dir = "rtl";
  div.dataset.projectId = project.id;
  setSelectableStyles(div, isSelected, "warning");
  div.innerHTML = `
        <div class="form-check form-check-custom form-check-solid flex-shrink-0">
            <input class="form-check-input" type="radio" name="lp_project_radio" value="${escAttr(project.id)}" ${isSelected ? "checked" : ""} />
        </div>
        <div class="flex-grow-1 min-w-0">
            <div class="fw-bold text-gray-800 fs-6 text-truncate">${escHtml(projectName)}</div>
            <div class="d-flex gap-4 mt-1 flex-wrap">
                <span class="text-gray-500 fs-7">
                    <i class="ki-duotone ki-calendar fs-7 me-1"><span class="path1"></span><span class="path2"></span></i>
                    ${createdDate}
                </span>
                <span class="text-gray-500 fs-7">
                    <i class="ki-duotone ki-time fs-7 me-1"><span class="path1"></span><span class="path2"></span></i>
                    آخرین باز: ${lastLoaded}
                </span>
            </div>
        </div>
        <span class="badge ${project.is_inferred ? "badge-light-success" : "badge-light-secondary"} flex-shrink-0">
            ${project.is_inferred ? "استنتاج‌شده ✓" : "استنتاج‌نشده"}
        </span>
        <div class="dropdown lp-project-actions flex-shrink-0">
            <button type="button"
                    class="btn btn-icon btn-sm btn-light lp-project-options-btn"
                    data-bs-toggle="dropdown"
                    data-bs-auto-close="outside"
                    aria-expanded="false"
                    aria-label="گزینه‌های پروژه">
                <i class="ki-duotone ki-dots-horizontal fs-2 text-gray-600">
                    <span class="path1"></span>
                    <span class="path2"></span>
                    <span class="path3"></span>
                </i>
            </button>
            <div class="dropdown-menu dropdown-menu-end menu-rounded menu-gray-700 fw-semibold fs-7 py-2 min-w-150px" dir="rtl">
                <button type="button" class="dropdown-item d-flex align-items-center gap-2 lp-project-rename">
                    <i class="ki-duotone ki-pencil fs-5"><span class="path1"></span><span class="path2"></span></i>
                    تغییر نام
                </button>
                <button type="button" class="dropdown-item d-flex align-items-center gap-2 text-danger lp-project-delete">
                    <i class="ki-duotone ki-trash fs-5 text-danger"><span class="path1"></span><span class="path2"></span></i>
                    حذف پروژه
                </button>
            </div>
        </div>
    `;

  div
    .querySelector(".lp-project-options-btn")
    ?.addEventListener("click", (event) => event.stopPropagation());
  div
    .querySelector(".lp-project-rename")
    ?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openRenameProjectModal(project);
    });
  div
    .querySelector(".lp-project-delete")
    ?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openDeleteProjectModal(project);
    });

  return div;
}

function selectProjectInModal(project) {
  selectedProject = project;

  document.querySelectorAll(".lp-item").forEach((el) => {
    const isThis = String(el.dataset.projectId) === String(project.id);
    setSelectableStyles(el, isThis, "warning");
    const radio = el.querySelector('input[type="radio"]');
    if (radio) radio.checked = isThis;
  });

  setDisabled("btn-confirm-load-project", false);
}

function openRenameProjectModal(project) {
  const modalEl = ensureRenameProjectModal();
  if (!modalEl) return;

  modalEl.dataset.previousProjectName = project.project_name || "";
  setText("lp-rename-current-name", project.project_name || "—");
  setValue("lp-rename-input", project.project_name || "");
  setDisabled("btn-confirm-rename-project", false);

  const input = byId("lp-rename-input");
  window.setTimeout(() => {
    input?.focus();
    input?.select();
  }, 150);

  bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

async function renameProjectFromModal() {
  const modalEl = byId("kt_modal_rename_project");
  const previousName = modalEl?.dataset.previousProjectName || "";
  const newName = getValue("lp-rename-input").trim();

  if (!previousName) {
    showToast("نام قبلی پروژه مشخص نیست", "danger");
    return;
  }
  if (!newName) {
    showToast("نام جدید پروژه را وارد کنید", "warning");
    byId("lp-rename-input")?.focus();
    return;
  }
  if (newName === previousName) {
    showToast("نام پروژه تغییری نکرده است", "info");
    return;
  }
  if (!CFG.renameProjectUrl) {
    showToast("آدرس تغییر نام پروژه تنظیم نشده است", "danger");
    return;
  }

  const btn = byId("btn-confirm-rename-project");
  setButtonLoading(btn, "در حال ذخیره...");

  try {
    const form = new FormData();
    form.append("previous_project_name", previousName);
    form.append("new_project_name", newName);

    const data = await fetchJson(CFG.renameProjectUrl, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      body: form,
    });

    if (getProjectName() === previousName) setValue("project-name", newName);
    if (selectedProject?.project_name === previousName)
      selectedProject.project_name = newName;

    bootstrap.Modal.getInstance(modalEl)?.hide();
    showToast("نام پروژه با موفقیت تغییر کرد.", "success", {
      serverMessage: data?.message,
    });
    await reloadProjectList();
  } catch (err) {
    console.error("Rename project failed:", err);
    showToast("تغییر نام پروژه انجام نشد. لطفاً دوباره تلاش کنید.", "error", {
      serverMessage: err.message,
    });
  } finally {
    resetButton(btn);
  }
}

function openDeleteProjectModal(project) {
  const modalEl = ensureDeleteProjectModal();
  if (!modalEl) return;

  modalEl.dataset.projectName = project.project_name || "";
  setText("lp-delete-project-name", project.project_name || "—");
  setDisabled("btn-confirm-delete-project", false);

  bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

async function deleteProjectFromModal() {
  const modalEl = byId("kt_modal_delete_project_confirm");
  const projectName = modalEl?.dataset.projectName || "";

  if (!projectName) {
    showToast("نام پروژه برای حذف مشخص نیست", "danger");
    return;
  }
  if (!CFG.deleteProjectUrl) {
    showToast("آدرس حذف پروژه تنظیم نشده است", "danger");
    return;
  }

  const btn = byId("btn-confirm-delete-project");
  setButtonLoading(btn, "در حال حذف...");

  try {
    const form = new FormData();
    form.append("project_name", projectName);

    const data = await fetchJson(CFG.deleteProjectUrl, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      body: form,
    });

    if (selectedProject?.project_name === projectName) selectedProject = null;
    if (getProjectName() === projectName) {
      setValue("project-name", CFG.defaultProjectName || "");
      resetImages();
    }

    bootstrap.Modal.getInstance(modalEl)?.hide();
    showToast("پروژه با موفقیت حذف شد.", "success", {
      serverMessage: data?.message,
    });
    await reloadProjectList();
  } catch (err) {
    console.error("Delete project failed:", err);
    showToast("حذف پروژه انجام نشد. لطفاً دوباره تلاش کنید.", "error", {
      serverMessage: err.message,
    });
  } finally {
    resetButton(btn);
  }
}

async function reloadProjectList() {
  lpPage = 1;
  lpHasMore = false;
  selectedProject = null;
  setDisabled("btn-confirm-load-project", true);
  await fetchProjects(false);
  applyProjectFilters();
}

async function confirmLoadProject() {
  if (!selectedProject) return;
  if (!CFG.loadImages) {
    showToast("آدرس بارگذاری تصاویر پروژه تنظیم نشده است", "danger");
    return;
  }

  const projectName = selectedProject.project_name || "";
  setValue("project-name", projectName);
  byId("project-name-error")?.classList.add("d-none");

  try {
    const url = `${CFG.loadImages}?project_name=${encodeURIComponent(projectName)}`;
    const data = await fetchJson(url);
    const images = Array.isArray(data.images) ? data.images : [];

    resetImages(await Promise.all(images.map(createImageItemFromServerImage)));
    showToast(
      `پروژه «${projectName}» با ${images.length} تصویر بارگذاری شد`,
      "success",
    );
  } catch (err) {
    console.error("Error loading project images:", err);
    showToast(
      "بارگذاری تصاویر پروژه انجام نشد. لطفاً دوباره تلاش کنید.",
      "error",
      { serverMessage: err.message },
    );
  }
}

async function createImageItemFromServerImage(imgData) {
  const url = normalizePath(imgData.url || "");
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const blob = await response.blob();
  const name = imgData.name || extractFileName(url) || "image";

  return {
    file: new File([blob], name, {
      type: blob.type || "application/octet-stream",
    }),
    id: makeImageId(),
    selected: false,
    objectUrl: URL.createObjectURL(blob),
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// MODEL MODAL
// ─────────────────────────────────────────────────────────────────────────────
function resetModelModal() {
  tempSelectedModel = null;

  setValue("model-search", "");
  setValue("model-filter-accuracy", "");
  setValue("model-filter-iou", "");
  modelSortState = { ...DEFAULT_MODEL_SORT };
  syncModelSortButtons();
  setDisabled("btn-confirm-model", true);

  show("model-loading");
  hide("model-empty");
  byId("model-list-container")
    ?.querySelectorAll(".model-item")
    .forEach((el) => el.remove());
}

async function fetchModels() {
  if (!CFG.loadModelsUrl) {
    showToast("آدرس بارگذاری مدل‌ها تنظیم نشده است", "danger");
    return;
  }

  try {
    const data = await fetchJson(CFG.loadModelsUrl);
    allModels = Array.isArray(data) ? data : data.results || [];

    hide("model-loading");
    applyModelFilters();
  } catch (err) {
    hide("model-loading");
    showToast("بارگذاری مدل‌ها انجام نشد. لطفاً دوباره تلاش کنید.", "error", {
      serverMessage: err.message,
    });
  }
}

function applyModelFilters() {
  const search = getValue("model-search").toLowerCase();
  const minAcc = parseFloat(getValue("model-filter-accuracy")) || 0;
  const minIou = parseFloat(getValue("model-filter-iou")) || 0;

  const filtered = allModels.filter((model) => {
    const name = String(model.name || "").toLowerCase();
    const acc = getModelMetric(model, "accuracy");
    const iou = getModelMetric(model, "iou");

    return (
      (!search || name.includes(search)) &&
      (!minAcc || (Number.isFinite(acc) && acc * 100 >= minAcc)) &&
      (!minIou || (Number.isFinite(iou) && iou * 100 >= minIou))
    );
  });

  renderModelList(sortModels(filtered));
}

function bindModelSortButtons() {
  // Use one delegated listener so sort buttons still work if the modal
  // markup is rendered or replaced after DOMContentLoaded.
  if (!document.body.dataset.modelSortBound) {
    document.addEventListener("click", handleModelSortClick);
    document.body.dataset.modelSortBound = "true";
  }

  syncModelSortButtons();
}

function handleModelSortClick(event) {
  const button = event.target.closest("[data-model-sort]");
  if (!button) return;

  event.preventDefault();
  setModelSort(button.dataset.modelSort);
}

function setModelSort(key) {
  if (!key) return;

  modelSortState =
    modelSortState.key === key
      ? { key, direction: modelSortState.direction === "desc" ? "asc" : "desc" }
      : { key, direction: "desc" };

  syncModelSortButtons();
  applyModelFilters();
}

function syncModelSortButtons() {
  document.querySelectorAll("[data-model-sort]").forEach((button) => {
    const isActive = button.dataset.modelSort === modelSortState.key;
    const indicator = button.querySelector(".model-sort-indicator");

    button.classList.toggle("btn-primary", isActive);
    button.classList.toggle("btn-light-primary", !isActive);
    button.setAttribute("aria-pressed", String(isActive));
    button.title = isActive
      ? modelSortState.direction === "desc"
        ? "نزولی"
        : "صعودی"
      : "مرتب‌سازی با این ستون";

    if (indicator)
      indicator.textContent = isActive
        ? modelSortState.direction === "desc"
          ? "↓"
          : "↑"
        : "";
  });
}

function sortModels(models) {
  return [...models].sort((a, b) => compareModels(a, b, modelSortState));
}

function compareModels(a, b, sortState) {
  const direction = sortState.direction === "asc" ? 1 : -1;
  const valueA = getModelSortValue(a, sortState.key);
  const valueB = getModelSortValue(b, sortState.key);

  const hasA = valueA !== null && valueA !== undefined && !Number.isNaN(valueA);
  const hasB = valueB !== null && valueB !== undefined && !Number.isNaN(valueB);

  if (!hasA && !hasB) return compareModelNames(a, b);
  if (!hasA) return 1;
  if (!hasB) return -1;

  if (valueA === valueB) return compareModelNames(a, b);
  return valueA > valueB ? direction : -direction;
}

function getModelSortValue(model, key) {
  if (key === "accuracy") return getModelMetric(model, "accuracy");
  if (key === "iou") return getModelMetric(model, "iou");
  if (key === "date") return getTimestamp(model.training_date);
  return null;
}

function getModelMetric(model, metricName) {
  const value = Number(model.metrics?.[metricName]);
  return Number.isFinite(value) ? value : null;
}

function getTimestamp(value) {
  if (!value) return null;

  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function compareModelNames(a, b) {
  return String(a.name || "").localeCompare(String(b.name || ""), "fa", {
    sensitivity: "base",
  });
}

function renderModelList(models) {
  const container = byId("model-list-container");
  const emptyEl = byId("model-empty");
  if (!container || !emptyEl) return;

  container.querySelectorAll(".model-item").forEach((el) => el.remove());

  if (!models.length) {
    show("model-empty");
    return;
  }

  hide("model-empty");

  models.forEach((model) => {
    const item = createModelItem(model);
    item.addEventListener("click", () => selectModelInModal(model));
    container.appendChild(item);
  });
}

function createModelItem(model) {
  const isSelected = tempSelectedModel?.id === model.id;
  const accVal = formatPercent(model.metrics?.accuracy);
  const iouVal = formatPercent(model.metrics?.iou);
  const trainDate = formatFaDate(model.training_date, "—");
  const div = document.createElement("div");

  div.className =
    "model-item d-flex align-items-center gap-4 p-4 rounded mb-2 cursor-pointer";
  div.dataset.modelId = model.id;
  setSelectableStyles(div, isSelected, "primary");
  div.innerHTML = `
        <div class="form-check form-check-custom form-check-solid flex-shrink-0">
            <input class="form-check-input" type="radio" name="modal_model_radio" value="${escAttr(model.id)}" ${isSelected ? "checked" : ""} />
        </div>
        <div class="flex-grow-1 min-w-0">
            <div class="fw-bold text-gray-800 fs-6 text-truncate">${escHtml(model.name || "بدون نام")}</div>
            <div class="d-flex gap-4 mt-1 flex-wrap">
                <span class="text-gray-500 fs-7">
                    <i class="ki-duotone ki-chart-line-up fs-7 me-1"><span class="path1"></span><span class="path2"></span></i>
                    Acc: ${accVal}
                </span>
                <span class="text-gray-500 fs-7">IOU: ${iouVal}</span>
                <span class="text-gray-500 fs-7">
                    <i class="ki-duotone ki-calendar fs-7 me-1"><span class="path1"></span><span class="path2"></span></i>
                    ${trainDate}
                </span>
            </div>
        </div>
    `;
  return div;
}

function selectModelInModal(model) {
  tempSelectedModel = model;

  document.querySelectorAll(".model-item").forEach((el) => {
    const isThis = String(el.dataset.modelId) === String(model.id);
    setSelectableStyles(el, isThis, "primary");
    const radio = el.querySelector('input[type="radio"]');
    if (radio) radio.checked = isThis;
  });

  setDisabled("btn-confirm-model", false);
}

function confirmModelSelection() {
  if (!tempSelectedModel) {
    showToast("لطفاً یک مدل انتخاب کنید", "warning");
    return;
  }

  selectedModel = tempSelectedModel;
  setValue("model-name", selectedModel.name || "");
  setValue("model-id", selectedModel.id || "");
  syncInferenceStages();
  showToast(`مدل «${selectedModel.name || "بدون نام"}» انتخاب شد`, "success");
}

// ─────────────────────────────────────────────────────────────────────────────
// FILE UPLOAD
// ─────────────────────────────────────────────────────────────────────────────
function handleFileSelect(input) {
  const files = Array.from(input.files || []);
  if (!files.length) return;

  let added = 0;

  files.forEach((file) => {
    if (isDuplicateImage(file)) return;

    imageItems.push({
      file,
      id: makeImageId(),
      selected: false,
      objectUrl: null,
    });
    added += 1;
  });

  input.value = "";
  allSelected =
    imageItems.length > 0 && imageItems.every((item) => item.selected);
  renderImageList();
  updateBadge();
  updateSelectAllButton();
  syncInferenceStages();

  showToast(
    added === 0
      ? "هیچ تصویر جدیدی اضافه نشد (تکراری)"
      : `${added} تصویر اضافه شد`,
    added === 0 ? "warning" : "success",
  );

  if (added > 0) scheduleAutoSaveProject("images-added");
}

function isDuplicateImage(file) {
  return imageItems.some(
    (item) => item.file.name === file.name && item.file.size === file.size,
  );
}

function getImageItem(id) {
  return imageItems.find((image) => image.id === id);
}

function syncAllSelectedState() {
  allSelected =
    imageItems.length > 0 && imageItems.every((item) => item.selected);
}

function refreshImageUi({ syncStages = true } = {}) {
  renderImageList();
  updateBadge();
  updateSelectAllButton();
  if (syncStages) syncInferenceStages();
}

function resetImages(items = []) {
  revokeAllObjectUrls();
  imageItems = items;
  allSelected = false;
  previewId = imageItems.some((item) => item.id === previewId)
    ? previewId
    : null;
  refreshImageUi();
}

// ─────────────────────────────────────────────────────────────────────────────
// IMAGE LIST RENDERING
// ─────────────────────────────────────────────────────────────────────────────
function renderImageList() {
  const list = byId("image-list-ul");
  const emptyMsg = byId("image-list-empty");
  if (!list || !emptyMsg) return;

  list.innerHTML = "";

  if (!imageItems.length) {
    show("image-list-empty");
    clearPreview();
    return;
  }

  hide("image-list-empty");

  imageItems.forEach((item) => {
    const listItem = createImageListItem(item);
    list.appendChild(listItem);
  });
}

function createImageListItem(item) {
  if (!item.objectUrl) item.objectUrl = URL.createObjectURL(item.file);

  const li = document.createElement("li");
  li.className =
    "image-list-item d-flex align-items-center gap-3 p-3 rounded mb-2 cursor-pointer";
  li.dataset.id = item.id;
  setSelectableStyles(li, item.selected, "primary");

  const thumb = document.createElement("img");
  thumb.className = "rounded flex-shrink-0";
  thumb.style.cssText =
    "width:44px; height:44px; object-fit:cover; border:1px solid var(--bs-gray-200);";
  thumb.alt = item.file.name;
  thumb.src = item.objectUrl;

  const nameSpan = document.createElement("span");
  nameSpan.className =
    "flex-grow-1 text-gray-800 fw-semibold fs-7 text-truncate";
  nameSpan.style.maxWidth = "180px";
  nameSpan.textContent = item.file.name;
  nameSpan.title = item.file.name;

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.className = "form-check-input ms-auto flex-shrink-0";
  checkbox.checked = item.selected;
  checkbox.style.cssText = "width:18px; height:18px;";
  checkbox.addEventListener("change", (event) => {
    event.stopPropagation();
    setItemSelection(item.id, checkbox.checked);
  });

  li.addEventListener("click", (event) => {
    if (event.target === checkbox) return;
    showPreview(item);
  });

  li.append(thumb, nameSpan, checkbox);
  return li;
}

// ─────────────────────────────────────────────────────────────────────────────
// PREVIEW
// ─────────────────────────────────────────────────────────────────────────────
function showPreview(item) {
  previewId = item.id;
  if (!item.objectUrl) item.objectUrl = URL.createObjectURL(item.file);

  const image = byId("preview-image");
  const placeholder = byId("preview-placeholder");
  const filename = byId("preview-filename");

  if (image) {
    image.src = item.objectUrl;
    image.classList.remove("d-none");
  }
  placeholder?.classList.add("d-none");
  if (filename) {
    filename.textContent = item.file.name;
    filename.classList.remove("d-none");
  }
}

function clearPreview() {
  previewId = null;

  const image = byId("preview-image");
  if (image) {
    image.src = "";
    image.classList.add("d-none");
  }

  byId("preview-placeholder")?.classList.remove("d-none");
  byId("preview-filename")?.classList.add("d-none");
}

// ─────────────────────────────────────────────────────────────────────────────
// SELECTION & DELETE
// ─────────────────────────────────────────────────────────────────────────────
function toggleItemSelection(id) {
  const item = imageItems.find((image) => image.id === id);
  if (!item) return;
  setItemSelection(id, !item.selected);
}

function setItemSelection(id, selected) {
  const item = imageItems.find((image) => image.id === id);
  if (!item) return;

  item.selected = Boolean(selected);
  allSelected =
    imageItems.length > 0 && imageItems.every((image) => image.selected);
  renderImageList();
  updateSelectAllButton();
}

function toggleSelectAll() {
  allSelected = !(
    imageItems.length > 0 && imageItems.every((item) => item.selected)
  );
  imageItems.forEach((item) => {
    item.selected = allSelected;
  });
  renderImageList();
  updateSelectAllButton();
}

function updateSelectAllButton() {
  const btn = byId("btn-select-all");
  if (!btn) return;

  btn.innerHTML = allSelected
    ? `<i class="ki-duotone ki-cross-square fs-4"><span class="path1"></span><span class="path2"></span></i><span>لغو انتخاب</span>`
    : `<i class="ki-duotone ki-check-square fs-4"><span class="path1"></span><span class="path2"></span></i><span>انتخاب همه</span>`;
}

function deleteSelected() {
  const before = imageItems.length;
  const selectedIds = new Set(
    imageItems.filter((item) => item.selected).map((item) => item.id),
  );

  imageItems.forEach((item) => {
    if (selectedIds.has(item.id) && item.objectUrl)
      URL.revokeObjectURL(item.objectUrl);
  });

  imageItems = imageItems.filter((item) => !selectedIds.has(item.id));
  allSelected = false;

  if (previewId && !imageItems.some((item) => item.id === previewId))
    clearPreview();

  refreshImageUi();

  const removed = before - imageItems.length;
  showToast(
    removed > 0 ? `${removed} تصویر حذف شد` : "هیچ تصویری انتخاب نشده بود",
    removed > 0 ? "danger" : "warning",
  );

  if (removed > 0) scheduleAutoSaveProject("images-deleted");
}

function updateBadge() {
  const badge = byId("image-count-badge");
  if (badge) badge.textContent = String(imageItems.length);
}

// ─────────────────────────────────────────────────────────────────────────────
// RUN MODEL — POLLING-BASED
// ─────────────────────────────────────────────────────────────────────────────
async function runModel() {
  const validationError = validateRunModelInput();
  if (validationError) {
    showToast(validationError, "danger");
    return;
  }

  resetRunningModalToRunningState();
  setText("run-status-label", "در حال اجرا...");
  openRunningModal();

  try {
    const response = await fetch(CFG.runInferenceUrl, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      body: buildInferenceFormData(),
    });
    const body = await safeJson(response);

    if (!response.ok) {
      renderTerminalState({
        status: "error",
        message: body?.error || `HTTP ${response.status}`,
      });
      return;
    }

    currentJobId = body.job_id;
    if (!currentJobId) throw new Error("شناسه اجرای مدل از سرور دریافت نشد");
    startPolling(currentJobId);
  } catch (err) {
    console.error("Run inference failed:", err);
    renderTerminalState({
      status: "error",
      message: "خطا در شروع اجرا: " + err.message,
    });
  }
}

function validateRunModelInput() {
  if (!CFG.runInferenceUrl) return "آدرس اجرای مدل تنظیم نشده است";
  if (!CFG.statusInferenceUrlBase) return "آدرس بررسی وضعیت مدل تنظیم نشده است";
  if (!imageItems.length) return "لطفاً ابتدا تصاویر را بارگذاری کنید";
  if (!selectedModel) return "لطفاً یک مدل انتخاب کنید";

  const nameErrorEl = byId("project-name-error");
  if (nameErrorEl && !nameErrorEl.classList.contains("d-none")) {
    return "نام پروژه تکراری است. لطفاً نام دیگری انتخاب کنید";
  }

  return "";
}

function buildInferenceFormData() {
  const formData = new FormData();
  formData.append("project_name", getProjectName());
  formData.append("model_id", selectedModel.id);
  formData.append("accuracy", String(getPercentValue("accuracy")));
  formData.append("iou", String(getPercentValue("iou")));
  formData.append("img_width", getValue("img-width"));
  formData.append("img_height", getValue("img-height"));
  formData.append(
    "processor",
    document.querySelector('input[name="processor"]:checked')?.value || "cpu",
  );
  imageItems.forEach((item) => formData.append("images", item.file));
  return formData;
}

function startPolling(jobId) {
  clearPolling();
  lastProgressApplied = -1;
  pollStatus(jobId);
  pollInterval = window.setInterval(() => pollStatus(jobId), POLL_INTERVAL_MS);
}

async function pollStatus(jobId) {
  try {
    const url = CFG.statusInferenceUrlBase.replace(
      "__JOBID__",
      encodeURIComponent(jobId),
    );
    const data = await fetchJson(url, { headers: { "X-CSRFToken": CSRF } });
    const current = data.progress_current || 0;

    if (current >= lastProgressApplied) {
      lastProgressApplied = current;
      renderProgress(data);
    }

    if (["done", "stopped", "error"].includes(data.status)) {
      clearPolling();
      renderTerminalState(data);
    }
  } catch (err) {
    console.warn("Status poll failed:", err.message);
  }
}

async function stopInference() {
  if (!currentJobId) return;
  if (!CFG.stopInferenceUrl) {
    showToast("آدرس توقف اجرا تنظیم نشده است", "danger");
    return;
  }

  const btn = byId("btn-stop-inference");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>در حال توقف...`;
  }

  const form = new FormData();
  form.append("job_id", currentJobId);

  try {
    const data = await fetchJson(CFG.stopInferenceUrl, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      body: form,
    });

    if (data.status === "noop") showToast("کاری برای توقف وجود ندارد", "info");
  } catch (err) {
    console.error("Stop inference failed:", err);
    showToast("ارسال درخواست توقف ناموفق بود", "danger");
    resetStopButton();
  }
}

function resetStopButton() {
  const btn = byId("btn-stop-inference");
  if (!btn) return;
  btn.disabled = false;
  btn.innerHTML = `<i class="ki-duotone ki-stop fs-3 me-1"><span class="path1"></span><span class="path2"></span></i>توقف`;
}

function clearPolling() {
  window.clearInterval(pollInterval);
  pollInterval = null;
}

function openRunningModal() {
  const el = byId("kt_modal_running");
  if (!el || !window.bootstrap) return;
  bootstrap.Modal.getOrCreateInstance(el).show();
  window.showLoading?.();
}

function resetRunningModalToRunningState() {
  lastTerminalState = null;
  currentJobId = null;
  lastProgressApplied = -1;
  clearPolling();

  setText("run-title", "مدل در حال پردازش است");
  setText(
    "run-subtitle",
    "لطفاً صبر کنید. این عملیات ممکن است چند دقیقه طول بکشد.",
  );
  setText("run-step-label", "در حال آماده‌سازی...");
  setText("run-progress-label", "۰٪ تکمیل شده");
  setText("run-image-counter", "0 / 0");

  const bar = byId("run-progress-bar");
  if (bar) {
    bar.style.width = "0%";
    bar.setAttribute("aria-valuenow", "0");
    bar.classList.remove("bg-success", "bg-warning", "bg-danger");
    bar.classList.add(
      "bg-primary",
      "progress-bar-animated",
      "progress-bar-striped",
    );
  }

  show("btn-stop-inference");
  hide("btn-confirm-close");
  resetStopButton();
}

function renderProgress(data) {
  const current = data.progress_current || 0;
  const total = data.progress_total || 0;
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;

  const bar = byId("run-progress-bar");
  if (bar) {
    bar.style.width = `${pct}%`;
    bar.setAttribute("aria-valuenow", String(pct));
  }

  setText("run-progress-label", `${pct}٪ تکمیل شده`);
  setText("run-image-counter", `${current} / ${total}`);

  if (data.status === "running") {
    setText(
      "run-step-label",
      total > 0
        ? `در حال پردازش تصویر ${current} از ${total}...`
        : "در حال آماده‌سازی...",
    );
  }
}

function renderTerminalState(data) {
  lastTerminalState = data;
  clearPolling();

  const bar = byId("run-progress-bar");
  if (bar)
    bar.classList.remove(
      "progress-bar-animated",
      "progress-bar-striped",
      "bg-primary",
    );

  if (data.status === "done") {
    setTerminalVisual(
      "success",
      "اجرا با موفقیت تکمیل شد",
      data.message || "تمام تصاویر پردازش شدند.",
      `${data.labels_saved || 0} برچسب ذخیره شد`,
    );
    window.showSuccess?.();
    if (bar) {
      bar.style.width = "100%";
      bar.setAttribute("aria-valuenow", "100");
    }
    setText("run-progress-label", "۱۰۰٪ تکمیل شده");
    const total =
      data.progress_total || data.progress_current || imageItems.length;
    setText("run-image-counter", `${total} / ${total}`);
  } else if (data.status === "stopped") {
    window.showError?.();
    setTerminalVisual(
      "warning",
      "اجرا متوقف شد",
      data.message || "نتایج جزئی ذخیره شدند.",
      `${data.labels_saved || 0} برچسب ذخیره شد`,
    );
    showToast("اجرا توسط کاربر متوقف شد", "warning");
  } else {
    window.showError?.();
    setTerminalVisual(
      "danger",
      "خطا در اجرا",
      data.message || data.error || "اجرا با خطا مواجه شد.",
      "",
    );
  }

  hide("btn-stop-inference");
  show("btn-confirm-close");
}

function setTerminalVisual(type, title, subtitle, stepText) {
  const bar = byId("run-progress-bar");
  if (bar) bar.classList.add(`bg-${type}`);
  setText("run-title", title);
  setText("run-subtitle", subtitle);
  setText("run-step-label", stepText);
}

function confirmCloseRunningModal() {
  const el = byId("kt_modal_running");
  if (el && window.bootstrap) bootstrap.Modal.getInstance(el)?.hide();

  if (lastTerminalState?.status === "done")
    onInferenceComplete(lastTerminalState);

  currentJobId = null;
  lastTerminalState = null;
  syncInferenceStages();
}

function closeRunningModal() {
  clearPolling();
  const el = byId("kt_modal_running");
  if (el && window.bootstrap) bootstrap.Modal.getInstance(el)?.hide();
}

// Kept for compatibility with existing inline calls, but real progress comes from polling.
function setRunProgress(pct, stepLabel) {
  const p = Math.max(0, Math.min(100, Math.round(Number(pct) || 0)));
  const bar = byId("run-progress-bar");
  if (bar) {
    bar.style.width = `${p}%`;
    bar.setAttribute("aria-valuenow", String(p));
  }
  setText("run-progress-label", `${p}٪ تکمیل شده`);
  setText("run-step-label", stepLabel || "");
}

// ─────────────────────────────────────────────────────────────────────────────
// POST-INFERENCE UI
// ─────────────────────────────────────────────────────────────────────────────
function onInferenceComplete() {
  inferenceComplete = true;

  setText("run-status-label", "اجرا کامل شد ✓");

  const btnRun = byId("btn-run-model");
  if (btnRun) {
    btnRun.innerHTML = `
            <i class="ki-duotone ki-arrows-circle fs-3">
                <span class="path1"></span>
                <span class="path2"></span>
            </i>
            <span>اجرای مجدد</span>
        `;
    btnRun.classList.replace("btn-success", "btn-primary");
  }

  show("btn-go-to-labeler");
  syncInferenceStages();
  showToast("استنتاج با موفقیت انجام شد", "success");
}

function goToLabeler() {
  if (!CFG.editProjectLabel) {
    showToast("آدرس مشاهده نتایج تنظیم نشده است", "danger");
    return;
  }

  const projectName = getProjectName();
  const url = CFG.editProjectLabel.replace(
    "__PRNAME__",
    encodeURIComponent(projectName),
  );
  window.location.href = url;
}

// ─────────────────────────────────────────────────────────────────────────────
// SAVE PROJECT
// ─────────────────────────────────────────────────────────────────────────────
let autoSaveTimer = null;
let autoSaveInFlight = false;
let pendingAutoSaveReason = "";

function scheduleAutoSaveProject(reason = "image-list-changed") {
  pendingAutoSaveReason = reason;
  window.clearTimeout(autoSaveTimer);
  autoSaveTimer = window.setTimeout(() => {
    autoSaveProject(pendingAutoSaveReason);
  }, AUTO_SAVE_DEBOUNCE_MS);
}

async function autoSaveProject(reason = "image-list-changed") {
  if (autoSaveInFlight) {
    scheduleAutoSaveProject(reason);
    return;
  }

  autoSaveInFlight = true;
  setText("run-status-label", "در حال ذخیره خودکار پروژه...");

  try {
    await saveProject({ isSure: true, isAutomatic: true });
  } finally {
    autoSaveInFlight = false;
    syncInferenceStages();
  }
}

async function saveProject(options = {}) {
  const normalized = normalizeSaveOptions(options);
  const { isSure, isAutomatic } = normalized;

  if (!CFG.saveProjectUrl) {
    showToast("آدرس ذخیره پروژه تنظیم نشده است", "danger");
    return false;
  }

  if (!imageItems.length && !isAutomatic) {
    showToast("لطفاً ابتدا تصاویر را بارگذاری کنید", "danger");
    return false;
  }

  const nameErrorEl = byId("project-name-error");
  if (!isSure && nameErrorEl && !nameErrorEl.classList.contains("d-none")) {
    showToast("نام پروژه تکراری است. لطفاً نام دیگری انتخاب کنید", "danger");
    return false;
  }

  const projectForm = new FormData();
  projectForm.append("project_name", getProjectName());
  projectForm.append("isSure", String(Boolean(isSure)));
  imageItems.forEach((item) => projectForm.append("images", item.file));

  try {
    const response = await fetch(CFG.saveProjectUrl, {
      method: "POST",
      headers: { "X-CSRFToken": CSRF },
      body: projectForm,
    });
    const data = await safeJson(response);

    if (response.ok && data?.requires_isSure) {
      if (isAutomatic) {
        return await saveProject({ isSure: true, isAutomatic: true });
      }
      showOverwriteConfirmModal();
      return false;
    }
    if (!response.ok) throw new Error(data?.error || `HTTP ${response.status}`);

    showToast(
      isAutomatic
        ? "تغییرات پروژه به صورت خودکار ذخیره شد."
        : "پروژه با موفقیت ذخیره شد.",
      "success",
      { serverMessage: data?.message },
    );
    return true;
  } catch (err) {
    console.error("Save project error:", err);
    showToast("ذخیره پروژه انجام نشد. لطفاً دوباره تلاش کنید.", "error", {
      serverMessage: err.message,
    });
    return false;
  }
}

function normalizeSaveOptions(options) {
  if (typeof options === "boolean")
    return { isSure: options, isAutomatic: false };
  return {
    isSure: Boolean(options.isSure),
    isAutomatic: Boolean(options.isAutomatic),
  };
}

function showOverwriteConfirmModal() {
  let modalEl = byId("overwriteConfirmModal");

  if (!modalEl) {
    document.body.insertAdjacentHTML(
      "beforeend",
      `
            <div class="modal fade" id="overwriteConfirmModal" tabindex="-1" aria-hidden="true" dir="rtl">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">هشدار: پروژه تکراری</h5>
                            <button type="button" class="btn-close m-0" data-bs-dismiss="modal" aria-label="بستن"></button>
                        </div>
                        <div class="modal-body">
                            <p>پروژه‌ای با این نام از قبل وجود دارد. آیا از جایگزینی و ذخیره تغییرات روی آن اطمینان دارید؟</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">انصراف</button>
                            <button type="button" class="btn btn-danger" id="confirmOverwriteBtn">بله، جایگزین شود</button>
                        </div>
                    </div>
                </div>
            </div>
        `,
    );
    modalEl = byId("overwriteConfirmModal");
    byId("confirmOverwriteBtn")?.addEventListener("click", () => {
      bootstrap.Modal.getInstance(modalEl)?.hide();
      saveProject({ isSure: true });
    });
  }

  if (!window.bootstrap || !modalEl) return;
  bootstrap.Modal.getOrCreateInstance(modalEl).show();
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────────────────
function byId(id) {
  return document.getElementById(id);
}

function show(id) {
  byId(id)?.classList.remove("d-none");
}

function hide(id) {
  byId(id)?.classList.add("d-none");
}

function toggle(id, visible) {
  byId(id)?.classList.toggle("d-none", !visible);
}

function getValue(id) {
  return byId(id)?.value || "";
}

function setValue(id, value) {
  const el = byId(id);
  if (el) el.value = value;
}

function setText(id, value) {
  const el = byId(id);
  if (el) el.textContent = value;
}

function setDisabled(id, disabled) {
  const el = byId(id);
  if (el) el.disabled = Boolean(disabled);
}

function getProjectName() {
  const input = byId("project-name");
  return (
    input?.value?.trim() ||
    input?.getAttribute("value") ||
    CFG.defaultProjectName ||
    "untitled-project"
  );
}

function getPercentValue(id) {
  const value = parseFloat(getValue(id));
  return Number.isFinite(value) ? value / 100 : 0;
}

function getCookie(name) {
  let value = "";
  if (!document.cookie) return value;

  document.cookie.split(";").forEach((cookie) => {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(name + "="))
      value = decodeURIComponent(trimmed.slice(name.length + 1));
  });

  return value;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await safeJson(response);
  if (!response.ok)
    throw new Error(data?.error || data?.message || `HTTP ${response.status}`);
  return data;
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

function escHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

function escAttr(value) {
  return escHtml(value).replace(/"/g, "&quot;");
}

function debounce(fn, delay) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function formatFaDate(value, fallback = "—") {
  if (!value) return fallback;
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? fallback
    : date.toLocaleDateString("fa-IR");
}

function formatPercent(value) {
  return Number.isFinite(value) ? `${(value * 100).toFixed(1)}٪` : "—";
}

function normalizePath(path) {
  if (!path) return "/";
  if (/^https?:\/\//i.test(path)) return path;
  return path.startsWith("/") ? path : `/${path}`;
}

function extractFileName(path) {
  return path.split("/").pop()?.split("?")[0] || "";
}

function makeImageId() {
  return `img-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function setSelectableStyles(el, selected, color) {
  el.style.cssText = `
        transition: all 0.15s;
        border: 1.5px solid ${selected ? `var(--bs-${color})` : "var(--bs-gray-200)"};
        background: ${selected ? `var(--bs-${color}-light, rgba(var(--bs-${color}-rgb), .08))` : "var(--bs-white)"};
    `;
}

function revokeAllObjectUrls() {
  imageItems.forEach((item) => {
    if (item.objectUrl) URL.revokeObjectURL(item.objectUrl);
  });
}

const RECENT_TOAST_WINDOW_MS = 900;
const TOAST_AUTOHIDE_MS = 3500;
const recentToastKeys = new Map();

function showToast(message, type = "info", options = {}) {
  /*
      User-facing toast messages must stay in Farsi.
      Any raw backend/server text should be passed as options.serverMessage
      so it is logged to the console instead of shown in the UI.
    */

  const normalizedType = normalizeToastType(type);
  const config = toastConfigForType(normalizedType);
  const displayMessage = message || config.defaultMessage;

  if (options.serverMessage) {
    console.log("[Server message]", options.serverMessage);
  }

  // Prevent the same toast from appearing twice when an action is triggered
  // by both an inline onclick and a JS-bound handler, or when fast async
  // callbacks return at nearly the same time.
  if (isDuplicateRecentToast(displayMessage, normalizedType)) return;

  const container = ensureToastContainer();
  const toastEl = document.createElement("div");

  toastEl.className = "toast inference-toast align-items-center border-0 mb-3";
  toastEl.role = "status";
  toastEl.ariaLive = "polite";
  toastEl.ariaAtomic = "true";
  toastEl.dir = "rtl";
  toastEl.style.background = "#ffffff";
  toastEl.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.14)";
  toastEl.style.borderRadius = "14px";
  toastEl.style.minWidth = "300px";
  toastEl.style.maxWidth = "420px";

  toastEl.innerHTML = `
        <div class="d-flex align-items-center px-4 py-3">
            <div class="d-flex align-items-center justify-content-center me-0 ms-3">
                <i class="ki-duotone ${config.icon} fs-2 ${config.colorClass}">
                    <span class="path1"></span>
                    <span class="path2"></span>
                    <span class="path3"></span>
                </i>
            </div>

            <div class="toast-body text-gray-800 fw-semibold fs-7 flex-grow-1 p-0">
                ${escHtml(displayMessage)}
            </div>

            <button type="button"
                    class="btn btn-sm btn-icon btn-light ms-0 me-3"
                    data-bs-dismiss="toast"
                    aria-label="بستن">
                <i class="ki-duotone ki-cross fs-3 text-gray-500">
                    <span class="path1"></span>
                    <span class="path2"></span>
                </i>
            </button>
        </div>
    `;

  container.appendChild(toastEl);

  if (window.bootstrap?.Toast) {
    const toast = bootstrap.Toast.getOrCreateInstance(toastEl, {
      delay: 3500,
      autohide: true,
    });
    toastEl.addEventListener("hidden.bs.toast", () =>
      removeToastElement(toastEl, container),
    );
    toast.show();
  } else {
    toastEl.classList.add("show");
    window.setTimeout(
      () => removeToastElement(toastEl, container),
      TOAST_AUTOHIDE_MS,
    );
  }
}

function ensureToastContainer() {
  let container = byId("inference-toast-container");
  if (container) return container;

  container = document.createElement("div");
  container.id = "inference-toast-container";
  container.className = "toast-container position-fixed bottom-0 end-0 p-4";
  container.dir = "rtl";
  container.style.zIndex = "11000";
  document.body.appendChild(container);
  return container;
}

function removeToastElement(toastEl, container) {
  toastEl.remove();
  if (container && !container.children.length) container.remove();
}

function isDuplicateRecentToast(message, type) {
  const now = Date.now();
  const key = `${type}:${message}`;
  const lastShownAt = recentToastKeys.get(key) || 0;

  for (const [storedKey, storedAt] of recentToastKeys.entries()) {
    if (now - storedAt > RECENT_TOAST_WINDOW_MS) {
      recentToastKeys.delete(storedKey);
    }
  }

  if (now - lastShownAt < RECENT_TOAST_WINDOW_MS) {
    return true;
  }

  recentToastKeys.set(key, now);
  return false;
}

function bindButtonClick(id, handler) {
  const el = byId(id);
  if (!el) return;

  el.onclick = (event) => {
    event?.preventDefault?.();
    handler(event);
  };
}

function normalizeToastType(type) {
  if (type === "danger") return "error";
  if (["success", "warning", "error", "info"].includes(type)) return type;
  return "info";
}

function toastConfigForType(type) {
  return (
    {
      success: {
        icon: "ki-check-circle",
        colorClass: "text-success",
        defaultMessage: "عملیات با موفقیت انجام شد.",
      },
      warning: {
        icon: "ki-information-5",
        colorClass: "text-warning",
        defaultMessage: "لطفاً مورد مشخص‌شده را بررسی کنید.",
      },
      error: {
        icon: "ki-cross-circle",
        colorClass: "text-danger",
        defaultMessage: "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
      },
      info: {
        icon: "ki-information-2",
        colorClass: "text-primary",
        defaultMessage: "اطلاعات به‌روزرسانی شد.",
      },
    }[type] || {
      icon: "ki-information-2",
      colorClass: "text-primary",
      defaultMessage: "اطلاعات به‌روزرسانی شد.",
    }
  );
}

function setButtonLoading(button, label = "در حال انجام...") {
  if (!button) return;
  button.dataset.originalHtml = button.innerHTML;
  button.disabled = true;
  button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${escHtml(label)}`;
}

function resetButton(button) {
  if (!button) return;
  button.disabled = false;
  if (button.dataset.originalHtml) {
    button.innerHTML = button.dataset.originalHtml;
    delete button.dataset.originalHtml;
  }
}

function readInferenceConfig() {
  const el = byId("inference-config");
  if (!el?.textContent?.trim()) return {};

  try {
    return JSON.parse(el.textContent);
  } catch (err) {
    console.error("Invalid inference-config JSON:", err);
    return {};
  }
}

function ensureRenameProjectModal() {
  let modalEl = byId("kt_modal_rename_project");
  if (modalEl) return modalEl;

  document.body.insertAdjacentHTML(
    "beforeend",
    `
        <div class="modal fade" id="kt_modal_rename_project" tabindex="-1" aria-hidden="true" dir="rtl">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0 pb-0">
                        <h2 class="fw-bold text-gray-900">تغییر نام پروژه</h2>
                        <button type="button" class="btn-close m-0" data-bs-dismiss="modal" aria-label="بستن"></button>
                    </div>
                    <div class="modal-body px-8 py-6">
                        <div class="text-gray-500 fs-7 mb-3">نام فعلی: <span id="lp-rename-current-name" class="fw-bold text-gray-700">—</span></div>
                        <label class="form-label fw-semibold text-gray-700">نام جدید پروژه</label>
                        <input type="text" class="form-control form-control-solid" id="lp-rename-input" autocomplete="off" />
                    </div>
                    <div class="modal-footer border-0 pt-0">
                        <button type="button" class="btn btn-light" data-bs-dismiss="modal">انصراف</button>
                        <button type="button" class="btn btn-primary fw-bold" id="btn-confirm-rename-project">ذخیره نام جدید</button>
                    </div>
                </div>
            </div>
        </div>
    `,
  );
  modalEl = byId("kt_modal_rename_project");
  byId("btn-confirm-rename-project")?.addEventListener(
    "click",
    renameProjectFromModal,
  );
  byId("lp-rename-input")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") renameProjectFromModal();
  });
  return modalEl;
}

function ensureDeleteProjectModal() {
  let modalEl = byId("kt_modal_delete_project_confirm");
  if (modalEl) return modalEl;

  document.body.insertAdjacentHTML(
    "beforeend",
    `
        <div class="modal fade" id="kt_modal_delete_project_confirm" tabindex="-1" aria-hidden="true" dir="rtl">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0 pb-0">
                        <h2 class="fw-bold text-gray-900">حذف پروژه</h2>
                        <button type="button" class="btn-close m-0" data-bs-dismiss="modal" aria-label="بستن"></button>
                    </div>
                    <div class="modal-body px-8 py-6">
                        <p class="text-gray-700 fs-6 mb-2">آیا از حذف این پروژه مطمئن هستید؟</p>
                        <div class="badge badge-light-danger fs-7" id="lp-delete-project-name">—</div>
                    </div>
                    <div class="modal-footer border-0 pt-0">
                        <button type="button" class="btn btn-light" data-bs-dismiss="modal">انصراف</button>
                        <button type="button" class="btn btn-danger fw-bold" id="btn-confirm-delete-project">حذف پروژه</button>
                    </div>
                </div>
            </div>
        </div>
    `,
  );
  modalEl = byId("kt_modal_delete_project_confirm");
  byId("btn-confirm-delete-project")?.addEventListener(
    "click",
    deleteProjectFromModal,
  );
  return modalEl;
}

// Keep functions reachable when existing HTML uses inline onclick handlers.
Object.assign(window, {
  applyModelFilters,
  applyProjectFilters,
  setModelSort,
  checkProjectName,
  closeRunningModal,
  confirmCloseRunningModal,
  confirmLoadProject,
  confirmModelSelection,
  deleteProjectFromModal,
  deleteSelected,
  goToLabeler,
  handleFileSelect,
  loadMoreProjects,
  renameProjectFromModal,
  runModel,
  saveProject,
  stopInference,
  toggleItemSelection,
  toggleSelectAll,
});
