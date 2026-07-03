/**
 * inference_panel.js
 * All client-side logic for the AI Inference Panel.
**/

"use strict";

// ─────────────────────────────────────────────────────────────────────────────
// CONFIG (injected from Django template via window.INFERENCE_CONFIG)
// ─────────────────────────────────────────────────────────────────────────────
const CFG = window.INFERENCE_CONFIG || {};
const CSRF = CFG.csrfToken || getCookie("csrftoken");

// ─────────────────────────────────────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────────────────────────────────────
let imageItems = [];
let previewId = null;
let selectedModel = null;
let tempSelectedModel = null;
let selectedProject = null;
let inferenceComplete = false;

// ─────────────────────────────────────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file-input");
    if (fileInput) {
        fileInput.addEventListener("change", () => handleFileSelect(fileInput));
    }

    document.getElementById("lp-search")?.addEventListener("input", debounce(applyProjectFilters, 350));
    document.getElementById("lp-date-filter")?.addEventListener("change", applyProjectFilters);
    document.getElementById("lp-inferred-filter")?.addEventListener("change", applyProjectFilters);

    const lpModal = document.getElementById("kt_modal_load_project");
    if (lpModal) {
        lpModal.addEventListener("show.bs.modal", () => {
            resetProjectModal();
            fetchProjects();
        });
    }

    document.getElementById("model-search")?.addEventListener("input", debounce(applyModelFilters, 350));
    document.getElementById("model-filter-accuracy")?.addEventListener("input", debounce(applyModelFilters, 350));
    document.getElementById("model-filter-iou")?.addEventListener("input", debounce(applyModelFilters, 350));
    document.getElementById("model-filter-date")?.addEventListener("change", applyModelFilters);

    const modelModal = document.getElementById("kt_modal_select_model");
    if (modelModal) {
        modelModal.addEventListener("show.bs.modal", () => {
            resetModelModal();
            fetchModels();
        });
    }
});

// ─────────────────────────────────────────────────────────────────────────────
// PROJECT NAME CHECK
// ─────────────────────────────────────────────────────────────────────────────
async function checkProjectName(name) {
    const errorEl = document.getElementById("project-name-error");
    if (!name || !CFG.checkProjectNameUrl) return;

    try {
        const res = await fetch(`${CFG.checkProjectNameUrl}?name=${encodeURIComponent(name)}`, {
            headers: { "X-CSRFToken": CSRF }
        });
        const data = await res.json();
        if (data.exists) {
            errorEl.classList.remove("d-none");
        } else {
            errorEl.classList.add("d-none");
        }
    } catch (_) {
        errorEl.classList.add("d-none");
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// LOAD PROJECT MODAL
// ─────────────────────────────────────────────────────────────────────────────
let lpAllProjects = [];
let lpPage = 1;
const LP_PAGE_SIZE = 15;
let lpHasMore = false;

function resetProjectModal() {
    lpAllProjects = [];
    lpPage = 1;
    lpHasMore = false;
    selectedProject = null;
    document.getElementById("lp-search").value = "";
    document.getElementById("lp-date-filter").value = "";
    document.getElementById("lp-inferred-filter").value = "";
    document.getElementById("btn-confirm-load-project").disabled = true;
    showLpLoading();
}

function showLpLoading() {
    document.getElementById("lp-loading").classList.remove("d-none");
    document.getElementById("lp-empty").classList.add("d-none");
    document.getElementById("lp-list").classList.add("d-none");
    document.getElementById("lp-load-more-wrap").classList.add("d-none");
}

async function fetchProjects(append = false) {
    if (!append) showLpLoading();
    const url = new URL(CFG.loadProjectsUrl, location.origin);
    url.searchParams.set("page", lpPage);
    url.searchParams.set("page_size", LP_PAGE_SIZE);

    try {
        const res = await fetch(url);
        const data = await res.json();
        const projects = data.results || data;
        lpHasMore = !!data.next;
        if (append) {
            lpAllProjects = lpAllProjects.concat(projects);
        } else {
            lpAllProjects = projects;
        }
        document.getElementById("lp-loading").classList.add("d-none");
        renderProjectList(lpAllProjects);
        document.getElementById("lp-load-more-wrap").classList.toggle("d-none", !lpHasMore);
    } catch (err) {
        document.getElementById("lp-loading").classList.add("d-none");
        showToast("خطا در بارگذاری پروژه‌ها: " + err.message, "danger");
    }
}

function loadMoreProjects() {
    lpPage++;
    fetchProjects(true);
}

function applyProjectFilters() {
    const search = (document.getElementById("lp-search")?.value || "").toLowerCase();
    const date = document.getElementById("lp-date-filter")?.value || "";
    const inferred = document.getElementById("lp-inferred-filter")?.value || "";
    const filtered = lpAllProjects.filter(p => {
        const matchName = !search || p.project_name.toLowerCase().includes(search);
        const matchDate = !date || (p.created_date || "").startsWith(date);
        const matchInferred = !inferred || String(p.is_inferred) === inferred;
        return matchName && matchDate && matchInferred;
    });
    renderProjectList(filtered);
}

function renderProjectList(projects) {
    const list = document.getElementById("lp-list");
    const empty = document.getElementById("lp-empty");
    list.innerHTML = "";
    if (!projects.length) {
        empty.classList.remove("d-none");
        list.classList.add("d-none");
        return;
    }
    empty.classList.add("d-none");
    list.classList.remove("d-none");

    projects.forEach(p => {
        const isSelected = selectedProject?.id === p.id;
        const createdDate = p.created_date ? new Date(p.created_date).toLocaleDateString("fa-IR") : "—";
        const lastLoaded = p.last_loaded ? new Date(p.last_loaded).toLocaleDateString("fa-IR") : "هرگز";
        const div = document.createElement("div");
        div.className = "lp-item d-flex align-items-center gap-4 p-4 rounded mb-2 cursor-pointer";
        div.dataset.projectId = p.id;
        div.style.cssText = `
            border: 1.5px solid ${isSelected ? "var(--bs-warning)" : "var(--bs-gray-200)"};
            background: ${isSelected ? "rgba(var(--bs-warning-rgb),.08)" : "var(--bs-white)"};
            transition: all 0.15s;
        `;
        div.innerHTML = `
            <div class="form-check form-check-custom form-check-solid flex-shrink-0">
                <input class="form-check-input" type="radio" name="lp_project_radio" value="${p.id}" ${isSelected ? "checked" : ""} />
            </div>
            <div class="flex-grow-1 min-w-0">
                <div class="fw-bold text-gray-800 fs-6 text-truncate">${escHtml(p.project_name)}</div>
                <div class="d-flex gap-4 mt-1 flex-wrap">
                    <span class="text-gray-500 fs-7"><i class="ki-duotone ki-calendar fs-7 me-1"></i>${createdDate}</span>
                    <span class="text-gray-500 fs-7"><i class="ki-duotone ki-time fs-7 me-1"></i>آخرین باز: ${lastLoaded}</span>
                </div>
            </div>
            <span class="badge ${p.is_inferred ? "badge-light-success" : "badge-light-secondary"} flex-shrink-0">
                ${p.is_inferred ? "استنتاج‌شده ✓" : "استنتاج‌نشده"}
            </span>
        `;
        div.addEventListener("click", () => selectProjectInModal(p, div));
        list.appendChild(div);
    });
}

function selectProjectInModal(project, clickedEl) {
    selectedProject = project;
    document.querySelectorAll(".lp-item").forEach(el => {
        const isThis = el.dataset.projectId == project.id;
        el.style.border = `1.5px solid ${isThis ? "var(--bs-warning)" : "var(--bs-gray-200)"}`;
        el.style.background = isThis ? "rgba(var(--bs-warning-rgb),.08)" : "var(--bs-white)";
        const radio = el.querySelector("input[type=radio]");
        if (radio) radio.checked = isThis;
    });
    document.getElementById("btn-confirm-load-project").disabled = false;
}

async function confirmLoadProject() {
    if (!selectedProject) return;
    const projectName = selectedProject.project_name;
    const nameInput = document.getElementById("project-name");
    if (nameInput) nameInput.value = projectName;
    document.getElementById("project-name-error")?.classList.add("d-none");

    try {
        const response = await fetch(`${CFG.loadImages}?project_name=${encodeURIComponent(projectName)}`);
        if (!response.ok) throw new Error('خطا در دریافت اطلاعات پروژه');
        const data = await response.json();

        imageItems.forEach(item => { if (item.objectUrl) URL.revokeObjectURL(item.objectUrl); });
        imageItems.length = 0;

        const fetchPromises = data.images.map(async (imgData) => {
            const fixedUrl = imgData.url.startsWith('/') ? imgData.url : '/' + imgData.url;
            const imgResponse = await fetch(fixedUrl);
            const blob = await imgResponse.blob();
            const file = new File([blob], imgData.name, { type: blob.type });
            return {
                file: file,
                id: `${imgData.id}`,
                selected: false,
                objectUrl: URL.createObjectURL(blob),
                defects: imgData.defects || []
            };
        });

        const newImages = await Promise.all(fetchPromises);
        imageItems.push(...newImages);
        renderImageList();
        if (typeof updateBadge === 'function') updateBadge();
        if (imageItems.length > 0) showPreview(imageItems[0]);
        showToast(`پروژه «${projectName}» با ${data.images.length} تصویر بارگذاری شد`, "success");
    } catch (error) {
        console.error("Error loading project images:", error);
        showToast("خطا در بارگذاری تصاویر پروژه", "danger");
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// MODEL MODAL
// ─────────────────────────────────────────────────────────────────────────────
let allModels = [];

function resetModelModal() {
    tempSelectedModel = null;
    document.getElementById("model-search").value = "";
    document.getElementById("model-filter-accuracy").value = "";
    document.getElementById("model-filter-iou").value = "";
    document.getElementById("model-filter-date").value = "";
    document.getElementById("btn-confirm-model").disabled = true;
    const container = document.getElementById("model-list-container");
    document.getElementById("model-loading").classList.remove("d-none");
    document.getElementById("model-empty").classList.add("d-none");
    container.querySelectorAll(".model-item").forEach(el => el.remove());
}

async function fetchModels() {
    try {
        const res = await fetch(CFG.loadModelsUrl);
        const data = await res.json();
        allModels = data.results || data;
        document.getElementById("model-loading").classList.add("d-none");
        renderModelList(allModels);
    } catch (err) {
        document.getElementById("model-loading").classList.add("d-none");
        showToast("خطا در بارگذاری مدل‌ها: " + err.message, "danger");
    }
}

function applyModelFilters() {
    const search = (document.getElementById("model-search")?.value || "").toLowerCase();
    const minAcc = parseFloat(document.getElementById("model-filter-accuracy")?.value) || 0;
    const minIou = parseFloat(document.getElementById("model-filter-iou")?.value) || 0;
    const minDate = document.getElementById("model-filter-date")?.value || "";
    const filtered = allModels.filter(m => {
        const acc = m.metrics?.accuracy ?? null;
        const iou = m.metrics?.iou ?? null;
        return (!search || m.name.toLowerCase().includes(search)) &&
               (!minAcc || (acc !== null && acc * 100 >= minAcc)) &&
               (!minIou || (iou !== null && iou * 100 >= minIou)) &&
               (!minDate || (m.training_date && m.training_date >= minDate));
    });
    renderModelList(filtered);
}

function renderModelList(models) {
    const container = document.getElementById("model-list-container");
    const emptyEl = document.getElementById("model-empty");
    container.querySelectorAll(".model-item").forEach(el => el.remove());
    if (!models.length) {
        emptyEl.classList.remove("d-none");
        return;
    }
    emptyEl.classList.add("d-none");
    models.forEach(model => {
        const isSelected = tempSelectedModel?.id === model.id;
        const accVal = model.metrics?.accuracy != null ? `${(model.metrics.accuracy * 100).toFixed(1)}٪` : "—";
        const iouVal = model.metrics?.iou != null ? `${(model.metrics.iou * 100).toFixed(1)}٪` : "—";
        const trainDate = model.training_date ? new Date(model.training_date).toLocaleDateString("fa-IR") : "—";
        const div = document.createElement("div");
        div.className = "model-item d-flex align-items-center gap-4 p-4 rounded mb-2 cursor-pointer";
        div.dataset.modelId = model.id;
        div.style.cssText = `
            border: 1.5px solid ${isSelected ? "var(--bs-primary)" : "var(--bs-gray-200)"};
            background: ${isSelected ? "var(--bs-primary-light, rgba(var(--bs-primary-rgb),.08))" : "var(--bs-white)"};
            transition: all 0.15s;
        `;
        div.innerHTML = `
            <div class="form-check form-check-custom form-check-solid flex-shrink-0">
                <input class="form-check-input" type="radio" name="modal_model_radio" value="${model.id}" ${isSelected ? "checked" : ""} />
            </div>
            <div class="flex-grow-1 min-w-0">
                <div class="fw-bold text-gray-800 fs-6 text-truncate">${escHtml(model.name)}</div>
                <div class="d-flex gap-4 mt-1 flex-wrap">
                    <span class="text-gray-500 fs-7"><i class="ki-duotone ki-chart-line-up fs-7 me-1"></i>Acc: ${accVal}</span>
                    <span class="text-gray-500 fs-7">IOU: ${iouVal}</span>
                    <span class="text-gray-500 fs-7"><i class="ki-duotone ki-calendar fs-7 me-1"></i>${trainDate}</span>
                </div>
            </div>
        `;
        div.addEventListener("click", () => selectModelInModal(model, div));
        container.appendChild(div);
    });
}

function selectModelInModal(model, clickedEl) {
    tempSelectedModel = model;
    document.querySelectorAll(".model-item").forEach(el => {
        const isThis = el.dataset.modelId == model.id;
        el.style.border = `1.5px solid ${isThis ? "var(--bs-primary)" : "var(--bs-gray-200)"}`;
        el.style.background = isThis ? "var(--bs-primary-light, rgba(var(--bs-primary-rgb),.08))" : "var(--bs-white)";
        const radio = el.querySelector("input[type=radio]");
        if (radio) radio.checked = isThis;
    });
    document.getElementById("btn-confirm-model").disabled = false;
}

function confirmModelSelection() {
    if (!tempSelectedModel) {
        showToast("لطفاً یک مدل انتخاب کنید", "warning");
        return;
    }
    selectedModel = tempSelectedModel;
    document.getElementById("model-name").value = selectedModel.name;
    document.getElementById("model-id").value = selectedModel.id;
    showToast(`مدل «${selectedModel.name}» انتخاب شد`, "success");
}

// ─────────────────────────────────────────────────────────────────────────────
// FILE UPLOAD
// ─────────────────────────────────────────────────────────────────────────────
function handleFileSelect(input) {
    const files = Array.from(input.files);
    if (!files.length) return;
    let added = 0;
    files.forEach(file => {
        const duplicate = imageItems.some(item => item.file.name === file.name && item.file.size === file.size);
        if (!duplicate) {
            imageItems.push({
                file,
                id: `img-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
                selected: false,
                objectUrl: null,
            });
            added++;
        }
    });
    input.value = "";
    renderImageList();
    updateBadge();
    if (added === 0) {
        showToast("هیچ تصویر جدیدی اضافه نشد (تکراری)", "warning");
    } else {
        showToast(`${added} تصویر اضافه شد`, "success");
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// IMAGE LIST RENDERING
// ─────────────────────────────────────────────────────────────────────────────
function renderImageList() {
    const ul = document.getElementById("image-list-ul");
    const emptyMsg = document.getElementById("image-list-empty");
    ul.innerHTML = "";
    if (imageItems.length === 0) {
        emptyMsg.classList.remove("d-none");
        clearPreview();
        return;
    }
    emptyMsg.classList.add("d-none");
    imageItems.forEach(item => {
        if (!item.objectUrl) item.objectUrl = URL.createObjectURL(item.file);
        const li = document.createElement("li");
        li.className = "image-list-item d-flex align-items-center gap-3 p-3 rounded mb-2 cursor-pointer";
        li.dataset.id = item.id;
        li.style.cssText = `
            transition: background 0.15s;
            border: 1.5px solid ${item.selected ? "var(--bs-primary)" : "var(--bs-gray-200)"};
            background: ${item.selected ? "var(--bs-primary-light, rgba(var(--bs-primary-rgb),.08))" : "var(--bs-white)"};
        `;
        const thumb = document.createElement("img");
        thumb.className = "rounded flex-shrink-0";
        thumb.style.cssText = "width:44px; height:44px; object-fit:cover; border:1px solid var(--bs-gray-200);";
        thumb.alt = item.file.name;
        thumb.src = item.objectUrl;
        const infoDiv = document.createElement("div");
        infoDiv.className = "flex-grow-1";
        const nameSpan = document.createElement("span");
        nameSpan.className = "text-gray-800 fw-semibold fs-7 text-truncate d-block";
        nameSpan.style.maxWidth = "180px";
        nameSpan.textContent = item.file.name;
        nameSpan.title = item.file.name;
        const defectsContainer = document.createElement("div");
        defectsContainer.className = "d-flex gap-1 mt-1 flex-wrap";
        if (item.defects && item.defects.length > 0) {
            const defectGroups = {};
            item.defects.forEach(defect => {
                if (!defectGroups[defect.class_name]) {
                    defectGroups[defect.class_name] = { count: 0, color: defect.color };
                }
                defectGroups[defect.class_name].count++;
            });
            for (const [className, info] of Object.entries(defectGroups)) {
                const defectBadge = document.createElement("span");
                const color = info.color && !info.color.startsWith('#') ? `#${info.color}` : (info.color || '#3498db');
                defectBadge.className = "badge me-1";
                defectBadge.style.backgroundColor = color;
                defectBadge.style.color = getContrastColor(color);
                defectBadge.style.fontSize = "10px";
                defectBadge.style.padding = "2px 6px";
                defectBadge.textContent = `${className}: ${info.count}`;
                defectsContainer.appendChild(defectBadge);
            }
        } else {
            const noDefectBadge = document.createElement("span");
            noDefectBadge.className = "badge badge-light-secondary fs-8";
            noDefectBadge.textContent = "بدون عیب";
            defectsContainer.appendChild(noDefectBadge);
        }
        infoDiv.appendChild(nameSpan);
        infoDiv.appendChild(defectsContainer);
        
        const btnDetails = document.createElement("button");
        btnDetails.type = "button";
        btnDetails.className = "btn btn-sm btn-light-info me-2 fs-8";
        btnDetails.innerHTML = "توضیحات";
        btnDetails.style.padding = "2px 8px";
        btnDetails.addEventListener("click", e => {
            e.stopPropagation();
            openImageMetaModal(item.id,item.objectUrl); // تابعی که باید در مرحله بعد بسازیم
        });
                
        
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "form-check-input ms-auto flex-shrink-0";
        checkbox.checked = item.selected;
        checkbox.style.cssText = "width:18px; height:18px;";
        checkbox.addEventListener("change", e => {
            e.stopPropagation();
            toggleItemSelection(item.id);
        });
        li.addEventListener("click", e => {
            if (e.target === checkbox || e.target === btnDetails) return;
            showPreview(item);
        });
        li.appendChild(thumb);
        li.appendChild(infoDiv);
        // li.appendChild(btnDetails); // د
        li.appendChild(checkbox);
        ul.appendChild(li);
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// PREVIEW - FETCH IMAGE WITH DEFECTS FROM BACKEND
// ─────────────────────────────────────────────────────────────────────────────
async function showPreview(item) {
    if (!item) return;
    previewId = item.id;
    
    // Show loading
    const img = document.getElementById("preview-image");
    const placeholder = document.getElementById("preview-placeholder");
    const filenameDiv = document.getElementById("preview-filename");
    
    if (img) img.classList.add("d-none");
    if (placeholder) {
        placeholder.classList.remove("d-none");
        placeholder.innerHTML = `
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="text-gray-400 fw-semibold fs-6">در حال بارگذاری تصویر...</span>
        `;
    }
    if (filenameDiv) {
        filenameDiv.textContent = item.file?.name || "بدون نام";
        filenameDiv.classList.remove("d-none");
    }
    
    try {
        const response = await fetch(`${CFG.gerDrawImage}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF
            },
            body: JSON.stringify({ image_id: item.id })
        });
        
        if (!response.ok) throw new Error('خطا در دریافت تصویر');
        
        const data = await response.json();
        
        if (data.success && data.image_base64) {
            if (img) {
                img.src = data.image_base64;
                img.classList.remove("d-none");
                img.style.display = "block";
                img.style.maxWidth = "100%";
                img.style.height = "auto";
            }
            if (placeholder) {
                placeholder.classList.add("d-none");
                placeholder.innerHTML = `
                    <i class="ki-duotone ki-picture fs-3tx text-gray-300 mb-3"></i>
                    <span class="text-gray-400 fw-semibold fs-6">پیش‌نمایش تصویر</span>
                `;
            }
        } else {
            throw new Error(data.error || 'خطای ناشناخته');
        }
    } catch (error) {
        console.error('Error fetching image with defects:', error);
        showToast('خطا در بارگذاری تصویر: ' + error.message, 'danger');
        // Fallback to original image
        if (img && item.objectUrl) {
            img.src = item.objectUrl;
            img.classList.remove("d-none");
        }
        if (placeholder) placeholder.classList.add("d-none");
    }
}

function clearPreview() {
    previewId = null;
    const img = document.getElementById("preview-image");
    const placeholder = document.getElementById("preview-placeholder");
    const filenameDiv = document.getElementById("preview-filename");
    if (img) {
        img.src = "";
        img.classList.add("d-none");
    }
    if (placeholder) placeholder.classList.remove("d-none");
    if (filenameDiv) filenameDiv.classList.add("d-none");
}

function refreshCurrentImage() {
    if (!previewId) {
        showToast("هیچ تصویری انتخاب نشده است", "warning");
        return;
    }
    const currentItem = imageItems.find(item => item.id === previewId);
    if (currentItem) showPreview(currentItem);
}

// ─────────────────────────────────────────────────────────────────────────────
// SELECTION & DELETE
// ─────────────────────────────────────────────────────────────────────────────
function toggleItemSelection(id) {
    const item = imageItems.find(i => i.id === id);
    if (item) {
        item.selected = !item.selected;
        renderImageList();
    }
}

let allSelected = false;
function toggleSelectAll() {
    allSelected = !allSelected;
    imageItems.forEach(i => i.selected = allSelected);
    renderImageList();
    const btn = document.getElementById("btn-select-all");
    btn.innerHTML = allSelected
        ? `<i class="ki-duotone ki-cross-square fs-4"></i><span>لغو انتخاب</span>`
        : `<i class="ki-duotone ki-check-square fs-4"></i><span>انتخاب همه</span>`;
}

function deleteSelected() {
    const before = imageItems.length;
    imageItems.filter(i => i.selected && i.objectUrl).forEach(i => URL.revokeObjectURL(i.objectUrl));
    imageItems = imageItems.filter(i => !i.selected);
    allSelected = false;
    const btn = document.getElementById("btn-select-all");
    btn.innerHTML = `<i class="ki-duotone ki-check-square fs-4"></i><span>انتخاب همه</span>`;
    if (previewId && !imageItems.find(i => i.id === previewId)) clearPreview();
    renderImageList();
    updateBadge();
    const removed = before - imageItems.length;
    if (removed > 0) showToast(`${removed} تصویر حذف شد`, "danger");
    else showToast("هیچ تصویری انتخاب نشده بود", "warning");
}

function updateBadge() {
    const badge = document.getElementById("image-count-badge");
    if (badge) badge.textContent = imageItems.length;
}

// ─────────────────────────────────────────────────────────────────────────────
// RUN MODEL
// ─────────────────────────────────────────────────────────────────────────────
let _progressInterval = null;

function runModel() {
    const projectName = document.getElementById("project-name").value.trim();
    const nameErrorEl = document.getElementById("project-name-error");
    if (imageItems.length === 0) {
        showToast("لطفاً ابتدا تصاویر را بارگذاری کنید", "danger");
        return;
    }
    if (!selectedModel) {
        showToast("لطفاً یک مدل انتخاب کنید", "danger");
        return;
    }
    if (nameErrorEl && !nameErrorEl.classList.contains("d-none")) {
        showToast("نام پروژه تکراری است. لطفاً نام دیگری انتخاب کنید", "danger");
        return;
    }
    const accuracy = parseFloat(document.getElementById("accuracy").value) / 100;
    const iou = parseFloat(document.getElementById("iou").value) / 100;
    const imgWidth = parseInt(document.getElementById("img-width").value, 10);
    const imgHeight = parseInt(document.getElementById("img-height").value, 10);
    const processor = document.querySelector('input[name="processor"]:checked')?.value || "cpu";
    openRunningModal();
    const formData = new FormData();
    formData.append("project_name", projectName || CFG.defaultProjectName);
    formData.append("model_id", selectedModel.id);
    formData.append("accuracy", accuracy);
    formData.append("iou", iou);
    formData.append("img_width", imgWidth);
    formData.append("img_height", imgHeight);
    formData.append("processor", processor);
    imageItems.forEach(item => formData.append("images", item.file));
    fetch(CFG.runInferenceUrl, {
        method: "POST",
        headers: { "X-CSRFToken": CSRF },
        body: formData,
    })
    .then(res => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
    .then(data => { closeRunningModal(); onInferenceComplete(data); })
    .catch(err => {
        closeRunningModal();
        console.error(err);
        showToast("خطا در اجرای مدل: " + err.message, "danger");
        document.getElementById("run-status-label").textContent = "خطا در اجرا";
    });
}

function openRunningModal() {
    const el = document.getElementById("kt_modal_running");
    if (!el) return;
    const modal = bootstrap.Modal.getOrCreateInstance(el);
    modal.show();
    let pct = 0;
    const steps = ["در حال بارگذاری تصاویر...", "در حال آماده‌سازی مدل...", "در حال استنتاج...", "در حال پردازش نتایج...", "تقریباً تمام شد..."];
    clearInterval(_progressInterval);
    _progressInterval = setInterval(() => {
        pct = Math.min(pct + Math.random() * 4 + 1, 95);
        setRunProgress(pct, steps[Math.floor(pct / 20)]);
    }, 600);
}

function closeRunningModal() {
    clearInterval(_progressInterval);
    setRunProgress(100, "کامل شد!");
    setTimeout(() => {
        const el = document.getElementById("kt_modal_running");
        if (el) bootstrap.Modal.getInstance(el)?.hide();
    }, 600);
}

function setRunProgress(pct, stepLabel) {
    const bar = document.getElementById("run-progress-bar");
    const label = document.getElementById("run-progress-label");
    const stepEl = document.getElementById("run-step-label");
    const timeEl = document.getElementById("run-time-remaining");
    if (!bar) return;
    const p = Math.round(pct);
    bar.style.width = p + "%";
    bar.setAttribute("aria-valuenow", p);
    if (label) label.textContent = `${p}٪ تکمیل شده`;
    if (stepEl) stepEl.textContent = stepLabel || "";
    if (timeEl) {
        if (p >= 100) timeEl.textContent = "تمام شد";
        else if (p > 5) timeEl.textContent = `~${Math.round(((100 - p) / p) * 10)} ثانیه مانده`;
        else timeEl.textContent = "محاسبه زمان...";
    }
}

function onInferenceComplete(data) {
    inferenceComplete = true;
    const statusLabel = document.getElementById("run-status-label");
    const btnRun = document.getElementById("btn-run-model");
    const btnLabeler = document.getElementById("btn-go-to-labeler");
    if (statusLabel) statusLabel.textContent = "اجرا کامل شد ✓";
    if (btnRun) btnRun.classList.replace("btn-success", "btn-primary");
    if (btnLabeler) btnLabeler.classList.remove("d-none");
    showToast("استنتاج با موفقیت انجام شد", "success");
}

function goToLabeler() {
    console.log("goToLabeler() called – implement redirect to labeler here.");
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────────────────
function getCookie(name) {
    let value = "";
    if (document.cookie) {
        document.cookie.split(";").forEach(c => {
            const t = c.trim();
            if (t.startsWith(name + "=")) value = decodeURIComponent(t.slice(name.length + 1));
        });
    }
    return value;
}

function escHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
}

function debounce(fn, delay) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

function showToast(message, type = "success") {
    const container = document.getElementById("kt_app_content_container") || document.body;
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show fw-semibold fs-7 mb-4`;
    alertDiv.role = "alert";
    alertDiv.innerHTML = `${escHtml(message)}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="بستن"></button>`;
    container.insertAdjacentElement("afterbegin", alertDiv);
    setTimeout(() => {
        alertDiv.classList.remove("show");
        setTimeout(() => alertDiv.remove(), 300);
    }, 3500);
}

function getContrastColor(hexColor) {
    if (!hexColor) return '#ffffff';
    let color = hexColor.startsWith('#') ? hexColor.slice(1) : hexColor;
    if (color.length === 3) color = color.split('').map(c => c + c).join('');
    if (color.length !== 6) return '#ffffff';
    try {
        const r = parseInt(color.slice(0, 2), 16);
        const g = parseInt(color.slice(2, 4), 16);
        const b = parseInt(color.slice(4, 6), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        return brightness > 128 ? '#000000' : '#ffffff';
    } catch (e) {
        return '#ffffff';
    }
}

async function saveProject(isSure = false) {
    let projectForm = new FormData();
    const projectName = document.getElementById("project-name").value.trim() || document.getElementById("project-name").getAttribute('value');
    const nameErrorEl = document.getElementById("project-name-error");
    if (imageItems.length === 0) {
        showToast("لطفاً ابتدا تصاویر را بارگذاری کنید", "danger");
        return;
    }
    if (!isSure && nameErrorEl && !nameErrorEl.classList.contains("d-none")) {
        showToast("نام پروژه تکراری است. لطفاً نام دیگری انتخاب کنید", "danger");
        return;
    }
    projectForm.append("project_name", projectName || CFG.defaultProjectName);
    projectForm.append("isSure", isSure);
    imageItems.forEach(item => projectForm.append("images", item.file));
    try {
        const res = await fetch(CFG.saveProjectUrl, {
            method: "POST",
            headers: { "X-CSRFToken": CSRF },
            body: projectForm,
        });
        let data = null;
        try { data = await res.json(); } catch {}
        if (res.ok && data?.requires_isSure) {
            showOverwriteConfirmModal();
            return;
        }
        if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
        showToast(data?.message || "پروژه با موفقیت ذخیره شد", "success");
    } catch (err) {
        console.error("Save project error:", err);
        showToast("خطا در ذخیره‌سازی پروژه: " + err.message, "danger");
    }
}

function showOverwriteConfirmModal() {
    let modalEl = document.getElementById('overwriteConfirmModal');
    if (!modalEl) {
        const modalHtml = `
        <div class="modal fade" id="overwriteConfirmModal" tabindex="-1" aria-hidden="true" dir="rtl">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">هشدار: پروژه تکراری</h5>
                <button type="button" class="btn-close m-0" data-bs-dismiss="modal" aria-label="Close"></button>
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
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modalEl = document.getElementById('overwriteConfirmModal');
        document.getElementById('confirmOverwriteBtn').addEventListener('click', () => {
            bootstrap.Modal.getInstance(modalEl).hide();
            saveProject(true);
        });
    }
    new bootstrap.Modal(modalEl).show();
}




document.addEventListener("DOMContentLoaded", () => {

    imageItems = (window.INITIAL_IMAGES || []).map(img => ({
        id: img.id,
        file: {
            name: img.name
        },
        objectUrl: img.url,
        selected: false,
        defects: []
    }));

    renderImageList();
    updateBadge();

    if (imageItems.length > 0) {
        showPreview(imageItems[0]);
    }
});