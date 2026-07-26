// ======================================================================
// labeling-mvp.js (Integrated with Provided HTML)
// =====================================================================

let imageList = [];
let currentImageIndex = -1;
let isDirty = false;

function markDirty() {
    isDirty = true;
}


document.addEventListener("DOMContentLoaded", () => {
    // -----------------------------------------------------
    // Global App container
    // -----------------------------------------------------
    class LabelingApp {
        constructor() {
            this.canvasEngine = null;
            this.manager = null;
            this.table = null;
            this.store = null;
        }
        loadDataset(datasetId) {
            if (typeof window.loadImageList === "function") {
                window.loadImageList(datasetId);
            }
        }
    }
    window.App = new LabelingApp();
    
    // -----------------------------------------------------
    // Main Initialization
    // -----------------------------------------------------
    const canvas = document.getElementById("labelCanvas");
    canvas.setAttribute("tabindex", "0");
    canvas.style.outline = "none";

    const ctx = canvas.getContext("2d");
    const tableBody = document.querySelector("#annotationTable tbody");
    const imageListTable = document.getElementById("imageTableBody");
    const perfectCheck = document.getElementById("perfectImageCheck");
    const zoomDisplay = document.getElementById("zoomLevelDisplay");
    
    // UI State Variables
    let currentClassLabel = null;
    let currentClassId = null;
    let currentClassColor = null; // *** CHANGE: Store the color of the selected class ***

    // Canvas Engine State
    let state = {
        zoom: 1,
        panX: 0,
        panY: 0
    };
    const HANDLE_SIZE = 8;
    const MIN_BOX_SIZE = 10;
    const MIN_ZOOM = 1;
    const MAX_ZOOM = 5;
    // -----------------------------------------------------
    // Utility
    // -----------------------------------------------------
    function getDatasetId() {
        const params = new URLSearchParams(window.location.search);
        return params.get("dataset");
    }
    function getCSRFToken() {
        const token = document.querySelector("[name=csrfmiddlewaretoken]");
        return token ? token.value : "";
    }

    // -----------------------------------------------------
    // Box Model
    // -----------------------------------------------------
    class Box {
        constructor(id, x, y, w, h, label, color, class_id) {
            this.id = id;
            this.x = x;
            this.y = y;
            this.w = w;
            this.h = h;
            this.label = label;
            this.color = color;
            this.class_id = class_id;
        }
        contains(px, py) {
            return px >= this.x && px <= this.x + this.w &&
                   py >= this.y && py <= this.y + this.h;
        }
        getHandles() {
            const x = this.x;
            const y = this.y;
            const w = this.w;
            const h = this.h;
            return {
                tl: {x:x, y:y, name:"tl"},
                tr: {x:x+w, y:y, name:"tr"},
                bl: {x:x, y:y+h, name:"bl"},
                br: {x:x+w, y:y+h, name:"br"},
                tm: {x:x+w/2, y:y, name:"tm"},
                bm: {x:x+w/2, y:y+h, name:"bm"},
                ml: {x:x, y:y+h/2, name:"ml"},
                mr: {x:x+w, y:y+h/2, name:"mr"}
            };
        }
    }

    // -----------------------------------------------------
    // Box Manager
    // -----------------------------------------------------
    class BoxManager {
        constructor() {
            this.boxes = [];
            this.active = null;
            this.handleActive = null;
            this.dragging = false;
            this.resizing = false;
            this.drawing = false;
            this.offsetX = 0;
            this.offsetY = 0;
            this.nextId = 1;
        }
        addBox(x, y, w, h, label, color, class_id) {
            const box = new Box(this.nextId++, x, y, w, h, label, color, class_id);
            this.boxes.push(box);
            return box;
        }
        removeBox(id) {
            this.boxes = this.boxes.filter(b => b.id !== id);
        }
        getBoxAt(px, py) {
            for(let i = this.boxes.length - 1; i >= 0; i--) {
                if(this.boxes[i].contains(px, py)) {
                    return this.boxes[i];
                }
            }
            return null;
        }
        getHandleAt(sx, sy, scaleToScreen) {
            for(const box of this.boxes) {
                const handles = box.getHandles();
                for(const k in handles) {
                    const h = handles[k];
                    const p = scaleToScreen(h.x, h.y);
                    if(Math.abs(sx - p.x) <= HANDLE_SIZE && Math.abs(sy - p.y) <= HANDLE_SIZE) {
                        return {box, handle: h.name};
                    }
                }
            }
            return null;
        }
    }

    // -----------------------------------------------------
    // Annotation Table Renderer
    // -----------------------------------------------------




class AnnotationTable {
// داخل کلاس AnnotationTable
render(boxes, activeId = null) {
    if (!tableBody) return;
    tableBody.innerHTML = "";
    
    boxes.forEach(box => {
        const row = document.createElement("tr");
        
        // استایل برای سطر انتخاب شده
        if (box.id === activeId) {
            row.style.backgroundColor = "#ffe5c4";
        }
        
        row.style.cursor = "pointer";

        row.innerHTML = `
            <td>${box.label}</td>
            <td>${Math.round(box.x)}</td>
            <td>${Math.round(box.y)}</td>
            <td>${Math.round(box.w)}</td>
            <td>${Math.round(box.h)}</td>
        `;

        // --- تغییر اصلی اینجا است ---
        // استفاده از addEventListener به جای onclick


        row.onmouseenter = () => {
            if (window.canvasEngine) {
                // فعال کردن باکس
                window.canvasEngine.manager.active = box; 
                // رسم مجدد
                window.canvasEngine.draw(); 
            }
        };
        row.onmouseleave = () => {
            if (window.canvasEngine) window.canvasEngine.setHover(null);
        };
        
        tableBody.appendChild(row);
        updateLabelsCount();

    });
}

}



    
    // -----------------------------------------------------
    // Canvas Engine
    // -----------------------------------------------------
    class CanvasEngine {
        constructor(canvas, ctx, manager, table) {
            this.canvas = canvas;
            this.ctx = ctx;
            this.manager = manager;
            this.table = table;
            this.image = null;
            this.imageId = null;
            this.imageLoaded = false;
            this.imageWidth = 0;
            this.imageHeight = 0;
            this.scaleX = 1;
            this.scaleY = 1;
            this.dragging = false;
            this.resizing = false;
            this.drawing = false;
            this.currentHandle = null;
            this.hover = null;
            this.drawStartX = 0;
            this.drawStartY = 0;
            this.dragStartX = 0;
            this.dragStartY = 0;
            this.attachEvents();
            this.updateZoomUI();
        }

        getCSRFToken() {
            const match = document.cookie.match(/(^|;) ?csrftoken=([^;]*)(;|$)/);
            return match ? decodeURIComponent(match[2]) : "";
        }



        attachEvents() {
            this.canvas.addEventListener("mousedown", (e) => {
                this.canvas.focus(); // وقتی کاربر روی عکس کلیک کرد، فوکوس بگیرد
                this.onMouseDown(e);
            });
            this.canvas.addEventListener("mousemove", (e) => this.onMouseMove(e));
            this.canvas.addEventListener("mouseup", (e) => this.onMouseUp(e));
            this.canvas.addEventListener("mouseleave", (e) => this.onMouseUp(e));
            
            this.canvas.addEventListener("wheel", (e) => {
                e.preventDefault();
                if (!this.imageLoaded) return;

                const rect = this.canvas.getBoundingClientRect();
                const sx = (e.clientX - rect.left) * (this.canvas.width / rect.width);
                const sy = (e.clientY - rect.top) * (this.canvas.height / rect.height);

                if (e.deltaY < 0) {
                    this.zoomIn(sx, sy);
                } else {
                    this.zoomOut(sx, sy);
                }
            }, { passive: false });

            this.canvas.addEventListener("keydown", (e) => {
                if (!this.imageLoaded) return;

                const key = e.key;
                const centerX = this.canvas.width / 2;
                const centerY = this.canvas.height / 2;

                if (key === "+" || key === "=") {
                    e.preventDefault();
                    this.zoomIn(centerX, centerY);
                } else if (key === "-" || key === "_") {
                    e.preventDefault();
                    this.zoomOut(centerX, centerY);
                }
            });



            // Mouse move for coordinates display
           this.canvas.addEventListener('mousemove', (e) => {
                if (!this.imageLoaded) return;

                const rect = this.canvas.getBoundingClientRect();
                const scaleX = this.canvas.width / rect.width;
                const scaleY = this.canvas.height / rect.height;

                const canvasX = (e.clientX - rect.left) * scaleX;
                const canvasY = (e.clientY - rect.top) * scaleY;

                const real = this.scaleToReal(canvasX, canvasY);
                const realX = Math.floor(real.x);
                const realY = Math.floor(real.y);

                let intensity = 0;

                if (
                    realX >= 0 &&
                    realX < this.canvas.width &&
                    realY >= 0 &&
                    realY < this.canvas.height
                ) {
                    try {
                        const pixel = this.ctx.getImageData(
                            Math.floor(canvasX),
                            Math.floor(canvasY),
                            1,
                            1
                        ).data;

                        intensity = Math.round((pixel[0] + pixel[1] + pixel[2]) / 3);
                    } catch (err) {
                        console.error("getImageData error:", err);
                    }
                }

                document.getElementById('mousePosDisplay').textContent =
                    `X: ${realX}, Y: ${realY}`;

                document.getElementById('intensityDisplay').textContent =
                    `Int: ${intensity}`;
            });
        }
setImage(imageId) {
    return new Promise((resolve, reject) => {
        state.zoom = 1;
        state.panX = 0;
        state.panY = 0;


        this.manager.active = null;
        this.hover = null;

        const img = new Image();

        img.onload = () => {
            this.image = img;
            this.imageLoaded = true;
            this.imageWidth = img.width;
            this.imageHeight = img.height;

            this.resetZoom();
            this.draw();

            resolve();
        };

        img.onerror = reject;
        img.src = `/server_image/${imageId}?t=${Date.now()}`;
    });
}


scaleToReal(px, py) {
    return {
        x: (px - this.offsetX - state.panX) / (this.scaleX * state.zoom),
        y: (py - this.offsetY - state.panY) / (this.scaleY * state.zoom)
    };
}
scaleToScreen(px, py) {
    return {
        x: px * this.scaleX * state.zoom + this.offsetX + state.panX,
        y: py * this.scaleY * state.zoom + this.offsetY + state.panY
    };
}
        onMouseDown(e) {
            if (!this.imageLoaded) return;
            const rect = this.canvas.getBoundingClientRect();
            const sx = (e.clientX - rect.left) * (this.canvas.width / rect.width);
            const sy = (e.clientY - rect.top) * (this.canvas.height / rect.height);
            const real = this.scaleToReal(sx, sy);
            
            // 1. Check Handle Resize
            const handleHit = this.manager.getHandleAt(sx, sy, (x, y) => this.scaleToScreen(x, y));
            if (handleHit) {
                this.resizing = true;
                this.drawing = false;
                this.currentHandle = handleHit;
                this.manager.active = handleHit.box;
                this.dragStartX = real.x;
                this.dragStartY = real.y;
                this.draw();
                return;
            }
            
            // 2. Check Drag Existing Box
            const box = this.manager.getBoxAt(real.x, real.y);
            if (box) {
                this.dragging = true;
                this.resizing = false;
                this.drawing = false;
                this.manager.active = box;
                this.dragStartX = real.x - box.x;
                this.dragStartY = real.y - box.y;
                this.draw();
                return;
            }
            
            // 3. Create New Box
            if (!currentClassLabel) {
                Swal.fire({ title: 'خطا', text: "لطفا ابتدا از جدول کلاس ها یک کلاس عیب انتخاب کنید.", icon: 'warning', confirmButtonClass: 'btn btn-primary', buttonsStyling: false,confirmButtonText: 'متوجه شدم', });

                return;
            }
            
            // *** CHANGE: Use the stored color for the selected class ***
            const color = currentClassColor || this.getColorForLabel(currentClassLabel);
            
            const newBox = this.manager.addBox(
                real.x, real.y, MIN_BOX_SIZE, MIN_BOX_SIZE,
                currentClassLabel, color, currentClassId
            );
            this.manager.active = newBox;
            this.drawing = true;
            this.dragging = false;
            this.resizing = false;
            this.drawStartX = real.x;
            this.drawStartY = real.y;
            markDirty(); // ✅ اضافه شود
            this.draw();
        }
        onMouseMove(e) {
            if (!this.imageLoaded) return;
            const rect = this.canvas.getBoundingClientRect();
            const sx = (e.clientX - rect.left) * (this.canvas.width / rect.width);
            const sy = (e.clientY - rect.top) * (this.canvas.height / rect.height);
            const real = this.scaleToReal(sx, sy);
            
            // Drawing
            if (this.drawing && this.manager.active) {
                const box = this.manager.active;
                const x1 = this.drawStartX;
                const y1 = this.drawStartY;
                const x2 = real.x;
                const y2 = real.y;
                box.x = Math.min(x1, x2);
                box.y = Math.min(y1, y2);
                box.w = Math.max(MIN_BOX_SIZE, Math.abs(x2 - x1));
                box.h = Math.max(MIN_BOX_SIZE, Math.abs(y2 - y1));
                
                box.x = Math.max(0, Math.min(box.x, this.imageWidth - box.w));
                box.y = Math.max(0, Math.min(box.y, this.imageHeight - box.h));
                this.draw();
                return;
            }
            
            // Dragging
            if (this.dragging && this.manager.active) {
                const box = this.manager.active;
                box.x = real.x - this.dragStartX;
                box.y = real.y - this.dragStartY;
                box.x = Math.max(0, Math.min(box.x, this.imageWidth - box.w));
                box.y = Math.max(0, Math.min(box.y, this.imageHeight - box.h));
                this.draw();
                return;
            }
            
            // Resizing
            if (this.resizing && this.currentHandle) {
                const {box, handle} = this.currentHandle;
                let nx = box.x;
                let ny = box.y;
                let nw = box.w;
                let nh = box.h;
                
                const endX = real.x;
                const endY = real.y;
                const right = box.x + box.w;
                const bottom = box.y + box.h;
                
                switch(handle) {
                    case "tl":
                        nx = Math.min(endX, right - MIN_BOX_SIZE);
                        ny = Math.min(endY, bottom - MIN_BOX_SIZE);
                        nw = right - nx;
                        nh = bottom - ny;
                        break;
                    case "tr":
                        ny = Math.min(endY, bottom - MIN_BOX_SIZE);
                        nw = Math.max(MIN_BOX_SIZE, endX - box.x);
                        nh = bottom - ny;
                        break;
                    case "bl":
                        nx = Math.min(endX, right - MIN_BOX_SIZE);
                        nw = right - nx;
                        nh = Math.max(MIN_BOX_SIZE, endY - box.y);
                        break;
                    case "br":
                        nw = Math.max(MIN_BOX_SIZE, endX - box.x);
                        nh = Math.max(MIN_BOX_SIZE, endY - box.y);
                        break;
                    case "tm":
                        ny = Math.min(endY, bottom - MIN_BOX_SIZE);
                        nh = bottom - ny;
                        break;
                    case "bm":
                        nh = Math.max(MIN_BOX_SIZE, endY - box.y);
                        break;
                    case "ml":
                        nx = Math.min(endX, right - MIN_BOX_SIZE);
                        nw = right - nx;
                        break;
                    case "mr":
                        nw = Math.max(MIN_BOX_SIZE, endX - box.x);
                        break;
                }
                nx = Math.max(0, Math.min(nx, this.imageWidth - nw));
                ny = Math.max(0, Math.min(ny, this.imageHeight - nh));
                box.x = nx;
                box.y = ny;
                box.w = nw;
                box.h = nh;
                this.draw();
                return;
            }
            
            // Cursor update
            const handleHover = this.manager.getHandleAt(sx, sy, (x, y) => this.scaleToScreen(x, y));
            if (handleHover) {
                this.canvas.style.cursor = "nwse-resize";
            } else if (this.manager.getBoxAt(real.x, real.y)) {
                this.canvas.style.cursor = "move";
            } else {
                this.canvas.style.cursor = "crosshair";
            }
        }
        onMouseUp(e) {
            const wasEditing = this.dragging || this.resizing || this.drawing;
            this.dragging = false;
            this.resizing = false;
            this.drawing = false;
            this.currentHandle = null;
            if (wasEditing) {
                markDirty(); // ✅ تغییر جدید
                scheduleAutosave();
                syncStatusFromCanvas();
                this.updateMetadata(this.imageId);

            }

        }
        
async updateMetadata(imageId) {
    try {
        const response = await fetch("/dataset/update-metadata/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.getCSRFToken()
            },
            body: JSON.stringify({
                image_id: imageId,
                annotations: this.getBoxes(),
            })
        });

        const data = await response.json();

        // بررسی اینکه آیا پاسخ موفقیت‌آمیز بوده و حاوی دیکشنری تغییرات است
        if (data.updates) {
            // پیمایش روی تمام کلیدها و مقادیر موجود در دیکشنری ارسالی از جنگو
            Object.entries(data.updates).forEach(([key, value]) => {
                this.updateMetadataUI(key, value);
            });
        } else {
            console.warn("No updates received from server", data);
        }

    } catch (err) {
        console.error("Error updating metadata:", err);
    }
}

updateMetadataUI(key, value) {
    const container = document.getElementById("metadataTableBody");

    if (!container) {
        console.warn("metadataTableBody not found");
        return;
    }

    const safeValue = value ?? "";
    const safeKey = String(key);

    // حذف پیام خالی
    const emptyMessage = container.querySelector(".text-muted");
    if (emptyMessage) {
        emptyMessage.remove();
    }

    // بررسی وجود textarea
    let textarea = container.querySelector(`.metadata-input[data-field="${safeKey}"]`);
    
    if (textarea) {
        // به‌روزرسانی مقدار
        if (textarea.value !== safeValue) {
            textarea.value = safeValue;
            autoResizeTextarea(textarea);
        }
        return;
    }

    // بررسی وجود آیتم
    let item = container.querySelector(`.metadata-item[data-field="${safeKey}"]`);
    if (item) {
        textarea = item.querySelector(".metadata-input");
        if (textarea) {
            textarea.value = safeValue;
            autoResizeTextarea(textarea);
            return;
        }
    }

    // ایجاد آیتم جدید
    item = document.createElement("div");
    item.className = "metadata-item";
    item.setAttribute("data-field", safeKey);

    const escapedKey = escapeHtml(safeKey);
    const escapedValue = escapeHtml(safeValue);

    item.innerHTML = `
        <div class="metadata-key">${escapedKey}</div>
        <div class="metadata-value">
            <textarea 
                class="metadata-input" 
                data-field="${escapedKey}"
                rows="1"
                placeholder="مقدار را وارد کنید..."
            >${escapedValue}</textarea>
        </div>
    `;

    container.appendChild(item);

    // تنظیم ارتفاع و رویدادها برای textarea جدید
    const newTextarea = item.querySelector(".metadata-input");
    if (newTextarea) {
        autoResizeTextarea(newTextarea);
        
        newTextarea.addEventListener('input', function() {
            autoResizeTextarea(this);
            const field = this.dataset.field;
            editedMetadata[field] = this.value;
            markDirty();
        });
        
        newTextarea.addEventListener('blur', function() {
            const field = this.dataset.field;
            editedMetadata[field] = this.value;
            if (isDirty) {
                scheduleAutosave();
            }
        });
    }
}



        // *** CHANGE: This function is now a fallback only if color is not provided ***
        getColorForLabel(label) {
            function simpleHash(str) {
                let hash = 0;
                for(let i = 0; i < str.length; i++) {
                    hash = ((hash << 5) - hash) + str.charCodeAt(i);
                    hash |= 0;
                }
                return Math.abs(hash);
            }
            const base = simpleHash(label);
            const r = 100 + (base % 155);
            const g = 100 + ((base >> 3) % 155);
            const b = 100 + ((base >> 5) % 155);
            return `rgba(${r},${g},${b},0.6)`;
        }
   draw() {
    if (!this.imageLoaded) return;

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    const baseScale = Math.min(
        this.canvas.width / this.imageWidth,
        this.canvas.height / this.imageHeight
    );

    this.scaleX = baseScale;
    this.scaleY = baseScale;

    const drawW = this.imageWidth * baseScale * state.zoom;
    const drawH = this.imageHeight * baseScale * state.zoom;

    this.offsetX = (this.canvas.width - this.imageWidth * baseScale) / 2;
    this.offsetY = (this.canvas.height - this.imageHeight * baseScale) / 2;

    const imageX = this.offsetX + state.panX;
    const imageY = this.offsetY + state.panY;

    // draw image
    this.ctx.drawImage(this.image, imageX, imageY, drawW, drawH);

    // ===== Draw Boxes =====
    for (const box of this.manager.boxes) {

        const screenX = box.x * this.scaleX * state.zoom + this.offsetX + state.panX;
        const screenY = box.y * this.scaleY * state.zoom + this.offsetY + state.panY;
        const screenW = box.w * this.scaleX * state.zoom;
        const screenH = box.h * this.scaleY * state.zoom;


        this.ctx.beginPath();
        this.ctx.lineWidth = (this.manager.active === box ? 3 : 2);

        if (this.hover === box.id) {
            this.ctx.strokeStyle = "#ffa500";
        } else {
            this.ctx.strokeStyle = box.color;
        }

        this.ctx.fillStyle = "rgba(255,165,0,0.1)";

        this.ctx.rect(screenX, screenY, screenW, screenH);
        this.ctx.fill();
        this.ctx.stroke();
    }


    // ===== Draw Handles & Labels =====
    for (const box of this.manager.boxes) {

        const handles = box.getHandles();

        // handles
        this.ctx.save();
        this.ctx.fillStyle = "#ffffff";
        this.ctx.strokeStyle = "#000000";

        for (const k in handles) {

            const h = handles[k];
            const p = this.scaleToScreen(h.x, h.y);

            this.ctx.beginPath();
            this.ctx.rect(
                p.x - HANDLE_SIZE / 2,
                p.y - HANDLE_SIZE / 2,
                HANDLE_SIZE,
                HANDLE_SIZE
            );

            this.ctx.fill();
            this.ctx.stroke();
        }

        this.ctx.restore();


        // label
        const topLeft = this.scaleToScreen(box.x, box.y);
        const text = box.label;

        this.ctx.save();
        this.ctx.font = "14px Arial";

        const textWidth = this.ctx.measureText(text).width;

        const paddingX = 4;
        const paddingY = 3;
        const labelHeight = 16;

        const bgW = textWidth + paddingX * 2;
        const bgX = topLeft.x;
        const bgY = topLeft.y - labelHeight - 2;

        this.ctx.fillStyle = "rgba(0,0,0,0.6)";
        this.ctx.fillRect(bgX, bgY, bgW, labelHeight);

        this.ctx.fillStyle = "#ffffff";
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";

        const textX = bgX + bgW / 2;
        const textY = bgY + labelHeight / 2;

        this.ctx.fillText(text, textX, textY);

        this.ctx.restore();
    }

    this.table.render(
        this.manager.boxes,
        this.manager.active ? this.manager.active.id : null
    );
}
// داخل کلاس CanvasEngine
        setActiveBox(box) {
            if (!box) {
                this.manager.active = null;
            } else {
                this.manager.active = box;
            }
            // رسم مجدد برای اعمال تغییرات (highlight شدن باکس جدید)
            this.draw();
        }
        setHover(boxId) {
            this.hover = boxId;
            this.draw();
        }
        deleteBox(id) {
            this.manager.removeBox(id);
            if(this.manager.active && this.manager.active.id === id) {
                this.manager.active = null;
            }
            markDirty(); // ✅ مهم
            this.draw();
            scheduleAutosave();
        }
        setBoxes(annotations) {
            this.manager.boxes = [];
            this.manager.nextId = 1;
            for(const ann of annotations) {
                // If the saved annotation doesn't have a color, we try to generate one or use a default
                // In a robust system, you'd save the color in the DB too.
                // Here we assume if it's loaded, we might need to recolor or it was saved with color.
                // Since our DB structure in save doesn't send color, we fallback to hash if needed.
                let color = ann.color; 
                if (!color) {
                    color = this.getColorForLabel(ann.class_name);
                }
                
                this.manager.addBox(
                    ann.x, ann.y, ann.width, ann.height,
                    ann.class_name, color, ann.class_id
                );
            }
            this.draw();
        }
        getBoxes() {
            return this.manager.boxes.map(box => ({
                id: box.id,
                x: box.x,
                y: box.y,
                width: box.w,
                height: box.h,
                label: box.label,
                class_id: box.class_id
            }));
        }

setZoom(newZoom, mouseX = null, mouseY = null) {
    const oldZoom = state.zoom;
    const clampedZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom));

    if (clampedZoom === oldZoom) return;

    if (mouseX !== null && mouseY !== null) {
        const worldX = (mouseX - this.offsetX - state.panX) / (this.scaleX * oldZoom);
        const worldY = (mouseY - this.offsetY - state.panY) / (this.scaleY * oldZoom);

        state.zoom = clampedZoom;

        state.panX = mouseX - this.offsetX - worldX * this.scaleX * state.zoom;
        state.panY = mouseY - this.offsetY - worldY * this.scaleY * state.zoom;
    } else {
        state.zoom = clampedZoom;
    }

    if (clampedZoom === MIN_ZOOM) {
        state.panX = 0;
        state.panY = 0;
    }


    this.updateZoomUI();
    this.draw();
}


zoomIn(mouseX = null, mouseY = null) {
    this.setZoom(state.zoom + 0.2, mouseX, mouseY);
}

zoomOut(mouseX = null, mouseY = null) {
    this.setZoom(state.zoom - 0.2, mouseX, mouseY);
}


resetZoom() {
    state.zoom = 1;
    state.panX = 0;
    state.panY = 0;
    this.updateZoomUI();
    this.draw();
}

applyZoom() {
    this.updateZoomUI();
    this.draw();
}
        updateZoomUI() {
            if(zoomDisplay) {
                zoomDisplay.textContent = Math.round(state.zoom * 100) + '%';
            }
        }
    }




    // -----------------------------------------------------
    // Annotation Store
    // -----------------------------------------------------
    class AnnotationStore {
        async load(imageId) {
            const res = await fetch(`/dataset/annotation/load/${imageId}/`);
            if (!res.ok) {
                console.error("Failed to load annotations:", res.status);
                return { annotations: [], is_perfect: false };
            }
            const data = await res.json();
            
            // اطمینان از اینکه metadata یک شیء معتبر است
            const metadata = data.metadata || {};
            renderMetadata(metadata);
            editedMetadata = { ...metadata };
            
            return {
                annotations: data.annotations || [],
                is_perfect: !!data.is_perfect
            };
        }
        async save(imageId, boxes) {
                if (!imageId) return;
                
                // جمع‌آوری تمام مقادیر متادیتا از textareaها
                const metadataFromUI = collectMetadataFromUI();
                
                // ترکیب با editedMetadata (اولویت با مقادیر UI)
                const finalMetadata = {
                    ...editedMetadata,
                    ...metadataFromUI
                };
                
                const payload = {
                    image_id: imageId,
                    is_perfect: isDefectFreeMode || false,
                    annotations: boxes.map(b => ({
                        x: b.x,
                        y: b.y,
                        width: b.width,
                        height: b.height,
                        class_id: b.class_id,
                    })),
                    metadata: finalMetadata  // ارسال تمام متادیتا
                };
                
                try {
                    const res = await fetch("/dataset/annotation/save/", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCSRFToken()
                        },
                        body: JSON.stringify(payload)
                    });
                    if (!res.ok) {
                        console.error("Failed to save annotations:", res.status);
                        const errorData = await res.json();
                        console.error("Error details:", errorData);
                        throw new Error(`Save failed: ${res.status}`);
                    }
                    return res;
                } catch (e) {
                    console.error("Save error:", e);
                    throw e;
                }
            }
        
    }

    // -----------------------------------------------------
    // Instantiation
    // -----------------------------------------------------
    const manager = new BoxManager();
    const table = new AnnotationTable();
    const store = new AnnotationStore();
    const canvasEngine = new CanvasEngine(canvas, ctx, manager, table);
    
    // Expose to window for global access
    window.canvasEngine = canvasEngine;
    window.annotationStore = store;
    window.App.canvasEngine = canvasEngine;
    window.App.manager = manager;
    window.App.table = table;
    window.App.store = store;

    // -----------------------------------------------------
    // Global Functions (Connected to HTML)
    // -----------------------------------------------------
    
    // 1. Set Class
    // *** CHANGE: This function now accepts a color parameter ***
    window.setClass = function(id, name, color) {
        currentClassId = id;
        currentClassLabel = name;
        currentClassColor = color; // Store the color passed from HTML
    };

    // 2. Set Canvas Image
    window.setCanvasImage = async function(imageUrl, imageId, imageName = "",datasetName="") {
        if (isDirty) {
            const result = await Swal.fire({
                title: "تغییرات ذخیره نشده",
                text: "برای این تصویر تغییرات ذخیره نشده دارید. آیا می‌خواهید ادامه دهید؟",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "ادامه",
                cancelButtonText: "لغو"
            });

            if (!result.isConfirmed) {
                return; // ❌ تغییر تصویر لغو شود
            }
        }
        
        
        
        // Save previous image if exists
        editedMetadata = {}; // ✅ RESET PER IMAGE
        if(canvasEngine.imageId !== null) {
            const boxes = canvasEngine.getBoxes();
            await store.save(canvasEngine.imageId, boxes);
        }
        const canvas = document.getElementById('labelCanvas');
        const defaultImg = document.getElementById('imgDefault');
        console.log('Image selected');
        // 3. مخفی کردن تصویر پیش‌فرض
        defaultImg.style.display = 'none';
        // 4. نمایش بوم
        canvas.style.display = 'block';
        
        // --- شروع تغییرات وضعیت ---
        const statusMsgDiv = document.getElementById('status-message');
        const statusSuccessDiv = document.getElementById('status-test');
        const statusTextSpan = document.getElementById('status-text');
        const currentImageNameSpan = document.getElementById('current-image-name');
        const datasetNameBadge = document.getElementById('dataset-name-badge');
        const displayName = imageName || `تصویر ${imageId}`;
        
        canvasEngine.imageId = imageId;
        await canvasEngine.setImage(imageId);
        isDirty = false; // ✅ چون تازه لود شده
        canvasEngine.resetZoom();
        const data = await store.load(imageId);
        canvasEngine.setBoxes(data.annotations || []);
        
        if (perfectCheck) {
            perfectCheck.checked = !!data.is_perfect;
        }
        
        statusMsgDiv.style.display = 'none';
        statusTextSpan.style.display = 'none';
        
        // نمایش پیام موفقیت
        statusSuccessDiv.style.display = 'flex';
        currentImageNameSpan.textContent = displayName;
        datasetNameBadge.textContent = datasetName|| "دیتاست فعلی";
        
        const isLabeled = !!data.is_perfect || (data.annotations || []).length > 0;
        updateRowStatus(imageId, isLabeled);
        resetZoom();


        updateLabelsCount();

        console.log('imageId',imageId);
        if (imageList.length > 0) {
            currentImageIndex = imageList.findIndex(i => String(i.id) === String(imageId));
        } else {
            // اگر لیست خالی بود (مثلاً لود اولیه)، لیست را بساز
            updateImageListFromTable();
        }

        console.log('currentImageIndex',currentImageIndex);



    };

    // 3. Load Image List
    window.loadImageList = async function(datasetId) {
        const res = await fetch(`/api/dataset/${datasetId}/images/`);
        if (!res.ok) {
            console.error("Failed to load dataset images:", res.status);
            return;
        }
        const images = await res.json();
        renderImageTable(images);

        setTimeout(() => {
            updateImageListFromTable();
        }, 100);

    };





window.saveAnnotations = async function() {
    if (!canvasEngine.imageId) {
        toastr.error("تصویر انتخاب نشده");
        return;
    }
    
    // جمع‌آوری متادیتا از UI قبل از ذخیره
    const metadataFromUI = collectMetadataFromUI();
    Object.assign(editedMetadata, metadataFromUI);
    
    const boxes = canvasEngine.getBoxes();
    
    try {
        const res = await store.save(canvasEngine.imageId, boxes);
        if (res && res.ok) {
            const responseData = await res.json();
            toastr.success("لیبل‌ها و متادیتا با موفقیت ذخیره شدند.");
            isDirty = false;
            
            // به‌روزرسانی UI با داده‌های برگشتی از سرور
            if (responseData.metadata) {
                renderMetadata(responseData.metadata);
                editedMetadata = { ...responseData.metadata };
            }
        } else {
            toastr.error("خطا در ذخیره‌سازی");
        }
    } catch (error) {
        console.error("Save error:", error);
        toastr.error("خطا در ارتباط با سرور");
    }
};

    // 5. Toolbar Actions
    window.deleteSelectedLabel = function() {
        if(canvasEngine.manager.active) {
            canvasEngine.deleteBox(canvasEngine.manager.active.id);
        } else {
            Swal.fire({ title: 'خطا', text: 'لطفا یک لیبل را جهت حذف انتخاب کنید', icon: 'warning', confirmButtonClass: 'btn btn-primary', buttonsStyling: false,confirmButtonText: 'متوجه شدم', });

        }
    };
    window.addNewLabel = function() {
        Swal.fire({ title: 'خطا', text: 'جهت ایجاد لیبل جدید بر روی تصویر کلیک نمایید.',
                 icon: 'info',
                  confirmButtonClass: 'btn btn-primary', 
                  buttonsStyling: false,
                  confirmButtonText: 'متوجه شدم',
                 });
    };
    window.editSelectedLabel = function() {
        if(canvasEngine.manager.active) {
            Swal.fire({ title: 'خطا', text: 'جهت ویرایش میتوانید بر روی لیبل کلیک کرده و آن را جابجا کنید و یا از اطراف آن اقدام به تغییر اندازه نمایید.',
                 icon: 'info',
                  confirmButtonClass: 'btn btn-primary', 
                  buttonsStyling: false,
                  confirmButtonText: 'متوجه شدم',
                 });

        } else {
            Swal.fire({ title: 'خطا', text: 'لطفا در ابتدا یک لیبل را انتخاب کنید',
                 icon: 'info',
                  confirmButtonClass: 'btn btn-primary', 
                  buttonsStyling: false,
                  confirmButtonText: 'متوجه شدم',
                 });
        }
    };
    window.zoomIn = function() {
        canvasEngine.zoomIn();
    };
    window.zoomOut = function() {
        canvasEngine.zoomOut();
    };
    window.resetZoom = function() {
        canvasEngine.resetZoom();
    };

    // -----------------------------------------------------
    // Helpers & Event Listeners
    // -----------------------------------------------------
    function scheduleAutosave() {
        if (!canvasEngine || !store) return;
        if (!canvasEngine.imageId) return;
        return;
        clearTimeout(window.autosaveTimer);
        window.autosaveTimer = setTimeout(() => {
            const boxes = canvasEngine.getBoxes();
            store.save(canvasEngine.imageId, boxes);
        }, 1000); // Debounce 1s
    }

    function updateRowStatus(imageId, isLabeled) {
        if (!imageListTable || !imageId) return;
        const row = imageListTable.querySelector(`tr[data-image-id="${imageId}"]`);
        if (!row) return;
        
        // Add active class
        document.querySelectorAll(".image-row").forEach(r => r.classList.remove("image-active"));
        row.classList.add("image-active");
        
        const badge = row.querySelector(".badge");
        if (badge) {
            badge.textContent = isLabeled ? "لیبل زده" : "بدون لیبل";
            badge.classList.remove("badge-light-success", "badge-light-danger");
            badge.classList.add(isLabeled ? "badge-light-success" : "badge-light-danger");
        }
    }

    function syncStatusFromCanvas() {
        const imageId = canvasEngine?.imageId;
        if (!imageId) return;
        const hasBoxes = (canvasEngine.getBoxes() || []).length > 0;
        const isPerfect = !!(perfectCheck && perfectCheck.checked);
        updateRowStatus(imageId, isPerfect || hasBoxes);
    }

    // پیدا کردن این بخش در انتهای کد و جایگزینی با این نسخه:
    document.addEventListener("click", (e) => {
        const row = e.target.closest(".image-row");
        if (!row) return;
        if (e.target.closest('.btn-light-danger')) return; // نادیده گرفتن دکمه حذف
        
        // ۱. ابتدا لیست را از روی جدول موجود در صفحه بروز کن
        updateImageListFromTable();
        
        // ۲. پیدا کردن ایندکس سطری که روی آن کلیک شده است
        const allRows = Array.from(document.querySelectorAll('#imageTableBody tr.image-row'));
        currentImageIndex = allRows.indexOf(row);
        
        const id = row.dataset.imageId;
        const url = row.dataset.imageUrl;
        const name_ = row.dataset.imageName;
        const datasetName_ = row.dataset.datasetName;
        
        if (id && url && window.setCanvasImage) {
            window.setCanvasImage(url, id, name_, datasetName_);
        }
    });

    // Handle Delete Image Button
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-light-danger');
        if (!btn) return;
        e.stopPropagation(); // Prevent row click
        const id = btn.dataset.id || btn.getAttribute('href').split('/').pop(); // Handle both cases
        
        if (!confirm('آیا از حذف این تصویر اطمینان دارید؟')) return;
        
        try {
            const res = await fetch(`/dataset/delete-file/${id}/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCSRFToken() }
            });
            if (res.ok) {
                const row = btn.closest('tr');
                if (row) row.remove();
                
                // If current image was deleted, load next or clear
                if (String(canvasEngine.imageId) === String(id)) {
                    const nextRow = row.nextElementSibling || row.previousElementSibling;
                    if (nextRow) {
                        const nextId = nextRow.dataset.imageId;
                        const nextUrl = nextRow.dataset.imageUrl;
                        if (nextId && nextUrl) {
                            window.setCanvasImage(nextUrl, nextId);
                        }
                    } else {
                        canvasEngine.imageId = null;
                        canvasEngine.imageLoaded = false;
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                    }
                }
            } else {
                alert("خطا در حذف تصویر");
            }
        } catch (err) {
            alert("خطا در ارتباط با سرور");
        }
    });

    // Handle Perfect Check Change
    if (perfectCheck) {
        perfectCheck.addEventListener("change", () => {
            scheduleAutosave();
            syncStatusFromCanvas();
        });
    }

    // Initialize
    const datasetId = getDatasetId();
    if (datasetId) {
        window.App.loadDataset(datasetId);
    }

    // تابع برای نمایش مجدد تصویر پیش‌فرض (در صورت نیاز به ریست)
    function showDefaultImage() {
        const canvas = document.getElementById('labelCanvas');
        const defaultImg = document.getElementById('defaultImage');
        canvas.style.display = 'none';
        defaultImg.style.display = 'block';
        resetZoom()
    }



    // ======================================================================
    // منطق تغییر وضعیت "بدون عیب" (کم کردن روشنایی و تغییر رنگ)
    // ======================================================================
    
    // 1. متغیر برای ذخیره رنگ‌های اصلی تا بتوانیم بعداً برگردانیم
    let originalBoxColors = [];
    let isDefectFreeMode = false;

    // 2. شنونده رویداد روی چک‌باکس

    perfectCheck.addEventListener('change', function() {
        isDefectFreeMode = this.checked;
        const canvas = document.getElementById('labelCanvas');
        const defaultImg = document.getElementById('imgDefault');

        if (isDefectFreeMode) {
            // 1. غیرفعال کردن تعامل با بوم (غیرفعال کردن کلیک و درگ)
            if (canvas) {
                canvas.style.pointerEvents = 'none'; // جلوگیری از کلیک
                canvas.style.opacity = '0.3';        // تیره کردن تصویر
            }
            if (defaultImg) {
                defaultImg.style.opacity = '0.3';
            }

            // 2. تغییر ظاهر باکس‌ها (خاکستری و کم‌رنگ)
            originalBoxColors = window.canvasEngine.manager.boxes.map(b => b.color);
            window.canvasEngine.manager.boxes.forEach(box => {
                box.color = "rgba(128, 128, 128, 0.3)"; 
            });
            
            // 3. بازگرداندن مدیریت ماوس به حالت عادی (برای نمایش کرسر)
            window.canvasEngine.draw();
            
        } else {
            // 1. فعال کردن تعامل با بوم
            if (canvas) {
                canvas.style.pointerEvents = 'auto'; // فعال کردن کلیک
                canvas.style.opacity = '1';          // روشن کردن تصویر
            }
            if (defaultImg) {
                defaultImg.style.opacity = '1';
            }

            // 2. بازگرداندن رنگ اصلی باکس‌ها
            window.canvasEngine.manager.boxes.forEach((box, index) => {
                if (originalBoxColors[index]) {
                    box.color = originalBoxColors[index];
                }
            });
            
            // 3. رسم مجدد
            window.canvasEngine.draw();
        }
    });


});


function loadInitialImage() {


        if (INITIAL_IMAGE_DATA) {

            showImagesInTable(INITIAL_IMAGE_DATA,{
                ok: true,
                status: 200,
                json: () => Promise.resolve({})
            });
            window.setCanvasImage(INITIAL_IMAGE_DATA.url, INITIAL_IMAGE_DATA.id,INITIAL_IMAGE_DATA.name,INITIAL_IMAGE_DATA.dataset_name);
        }
    }

document.addEventListener('DOMContentLoaded', function() {
        // کمی صبر کنیم تا همه اسکریپت‌ها لود شوند
        setTimeout(loadInitialImage, 100);
    });




function updateLabelsCount() {
    const rows =
        document.querySelectorAll('#annotationTable tbody tr').length;

    document.getElementById('labelsCountBadge').innerText = rows;
    document.getElementById('labelsCountBadgeInline').innerText = rows;

}



document.addEventListener('keydown', function(e){

    // کلید H برای help
    if(e.key.toLowerCase() === 'h'){

        const modal = new bootstrap.Modal(
            document.getElementById('helpModal')
        );

        modal.show();
    }
});


function updateImageListFromTable() {
    const rows = document.querySelectorAll('#imageTableBody tr.image-row');
    imageList = [];
    
    rows.forEach((row, index) => {
        imageList.push({
            id: String(row.dataset.imageId), // تبدیل به رشته برای مقایسه دقیق‌تر
            url: row.dataset.imageUrl,
            name: row.dataset.imageName,
            dataset: row.dataset.datasetName,
            element: row
        });
        
        // پیدا کردن ایندکس بر اساس کلاس active
        if (row.classList.contains('image-active')) {
            currentImageIndex = index; // اصلاح نام متغیر از currentImgIndex به currentImageIndex
        }
    });
}

function openImageByIndex(index) {
    if (!imageList || imageList.length === 0) {
        updateImageListFromTable(); // اگر لیست خالی بود تلاش مجدد برای خواندن از جدول
    }
    if (index < 0 || index >= imageList.length) return;

    const img = imageList[index];
    currentImageIndex = index;

    window.setCanvasImage(
        img.url,
        img.id,
        img.name,
        img.dataset // مطابق با فیلد ذخیره شده در updateImageListFromTable
    );


}

function nextImage() {
    const start = (image_table_state.currentPage - 1) * image_table_state.itemsPerPage;
    const end = start + image_table_state.itemsPerPage;
    const pageImages = image_table_state.allImages.slice(start, end);

    let currentIndex = pageImages.findIndex(img => img.id == image_table_state.currentImageId);

    // اگر در همین صفحه تصویر بعدی وجود دارد
    if (currentIndex < pageImages.length - 1) {
        const nextImage = pageImages[currentIndex + 1];
        window.setCanvasImage(nextImage.url, nextImage.id, nextImage.name, nextImage.dataset_name);
        image_table_state.currentImageId = nextImage.id;
        renderTable();
        return;
    }

    // اگر به آخر صفحه رسیدیم → برو صفحه بعد
    const totalPages = Math.ceil(image_table_state.allImages.length / image_table_state.itemsPerPage);

    if (image_table_state.currentPage < totalPages) {
        image_table_state.currentPage++;

        renderTable();
        renderPagination();

        const newStart = (image_table_state.currentPage - 1) * image_table_state.itemsPerPage;
        const nextImage = image_table_state.allImages[newStart];

        if (nextImage) {
            window.setCanvasImage(nextImage.url, nextImage.id, nextImage.name, nextImage.dataset_name);
            image_table_state.currentImageId = nextImage.id;
        }
    }
}
function prevImage() {
    const start = (image_table_state.currentPage - 1) * image_table_state.itemsPerPage;
    const end = start + image_table_state.itemsPerPage;
    const pageImages = image_table_state.allImages.slice(start, end);

    let currentIndex = pageImages.findIndex(img => img.id == image_table_state.currentImageId);

    if (currentIndex > 0) {
        const prevImage = pageImages[currentIndex - 1];
        window.setCanvasImage(prevImage.url, prevImage.id, prevImage.name, prevImage.dataset_name);
        image_table_state.currentImageId = prevImage.id;
        renderTable();
        return;
    }

    if (image_table_state.currentPage > 1) {
        image_table_state.currentPage--;

        renderTable();
        renderPagination();

        const newStart = (image_table_state.currentPage - 1) * image_table_state.itemsPerPage;
        const pageImages = image_table_state.allImages.slice(newStart, newStart + image_table_state.itemsPerPage);
        const prevImage = pageImages[pageImages.length - 1];

        if (prevImage) {
            window.setCanvasImage(prevImage.url, prevImage.id, prevImage.name, prevImage.dataset_name);
            image_table_state.currentImageId = prevImage.id;
        }
    }
}
//  (فلش چپ و راست)
document.addEventListener('keydown', function(e) {
        // اگر کاربر در حال تایپ در فیلد ورودی نیست
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
        return;
    }

    const key = e.key.toLowerCase();

    // جابجایی بین تصاویر (Next / Prev)
    if (key === 'd' || key === 'ی') { // کلید D یا ی فارسی
        window.nextImage();
    } else if (key === 'a' || key === 'ش') { // کلید A یا ش فارسی
        window.prevImage();
    }

});

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderMetadata(metadata) {
    const container = document.getElementById("metadataTableBody");

    if (!container) {
        console.warn("metadataTableBody not found");
        return;
    }

    if (!metadata || Object.keys(metadata).length === 0) {
        container.innerHTML = `
            <div class="text-muted text-center w-100 py-4">
                <i class="ki-duotone ki-data fs-2x text-muted mb-2 d-block"></i>
                <span>هیچ داده‌ای موجود نیست</span>
            </div>
        `;
        return;
    }

    container.innerHTML = Object.entries(metadata)
        .map(([key, value]) => `
            <div class="metadata-item" data-field="${escapeHtml(key)}">
                <div class="metadata-key">${escapeHtml(key)}</div>
                <div class="metadata-value">
                    <textarea 
                        class="metadata-input" 
                        data-field="${escapeHtml(key)}"
                        rows="1"
                        placeholder="مقدار را وارد کنید..."
                    >${escapeHtml(value)}</textarea>
                </div>
            </div>
        `).join("");

    // تنظیم ارتفاع خودکار برای همه textareaها
    document.querySelectorAll('.metadata-value textarea').forEach(textarea => {
        autoResizeTextarea(textarea);
        
        // رویداد برای تغییر ارتفاع هنگام تایپ
        textarea.addEventListener('input', function() {
            autoResizeTextarea(this);
            // ذخیره تغییرات در editedMetadata
            const field = this.dataset.field;
            editedMetadata[field] = this.value;
            markDirty();
        });
        
        // رویداد برای ذخیره هنگام از دست دادن فوکوس
        textarea.addEventListener('blur', function() {
            const field = this.dataset.field;
            editedMetadata[field] = this.value;
            if (isDirty) {
                scheduleAutosave();
            }
        });
    });
}

// تابع کمکی برای تنظیم ارتفاع خودکار textarea
function autoResizeTextarea(textarea) {
    if (!textarea) return;
    
    // ریست ارتفاع برای محاسبه صحیح
    textarea.style.height = 'auto';
    
    // تنظیم ارتفاع بر اساس محتوای scrollHeight
    const newHeight = Math.max(32, textarea.scrollHeight);
    textarea.style.height = newHeight + 'px';
    
    // اگر ارتفاع از حد مشخصی بیشتر شد، اسکرول فعال می‌شود
    if (newHeight > 200) {
        textarea.style.maxHeight = '200px';
        textarea.style.overflowY = 'auto';
    } else {
        textarea.style.maxHeight = 'none';
        textarea.style.overflowY = 'hidden';
    }
}


let editedMetadata = {};


document.addEventListener("input", function (e) {
    if (e.target.classList.contains("metadata-input")) {
        const field = e.target.dataset.field;
        editedMetadata[field] = e.target.value;
        markDirty(); // ✅ اضافه شود

    }
});



window.addEventListener("beforeunload", function (e) {
    if (isDirty) {
        e.preventDefault();
        e.returnValue = "";
    }
});

function toggleSelectAll(checkbox) {
    const isChecked = checkbox.checked;

    if (isChecked) {
        // ✅ SELECT ALL IMAGES (ALL PAGES)
        image_table_state.selectedImageIds =
            image_table_state.allImages.map(img => img.id);
    } else {
        // ❌ CLEAR ALL SELECTIONS
        image_table_state.selectedImageIds = [];
    }

    syncCheckboxUI();
}
function syncCheckboxUI() {
    const tbody = document.getElementById("imageTableBody");

    // sync row checkboxes
    tbody.querySelectorAll("tr.image-row").forEach(row => {
        const id = parseInt(row.dataset.imageId);
        const checkbox = row.querySelector("input[type='checkbox']");
        if (checkbox) {
            checkbox.checked = image_table_state.selectedImageIds.includes(id);
        }
    });

    // sync master checkbox (global state)
    const master = document.getElementById("selectAllImages");

    const total = image_table_state.allImages.length;
    const selected = image_table_state.selectedImageIds.length;

    if (selected === 0) {
        master.checked = false;
        master.indeterminate = false;
    } 
    else if (selected === total) {
        master.checked = true;
        master.indeterminate = false;
    } 
    else {
        // 🔥 partial selection state (VERY IMPORTANT UX)
        master.checked = false;
        master.indeterminate = true;
    }
    updateRemoveButton()
}
function updateRemoveButton() {
    const btn = document.getElementById('removeSelectedImagesBtn');

    if (!btn) return;

    btn.style.display =
        image_table_state.selectedImageIds.length > 0
        ? 'inline-block'
        : 'none';
}


document.getElementById('removeSelectedImagesBtn')?.addEventListener('click', function () {

    const selectedIds = image_table_state.selectedImageIds;

    if (!selectedIds.length) {
        Swal.fire({
            icon: 'warning',
            title: 'هیچ تصویری انتخاب نشده',
            confirmButtonText: 'باشه'
        });
        return;
    }

    Swal.fire({
        title: 'حذف از لیست',
        text: `آیا می‌خواهید ${selectedIds.length} تصویر از لیست حذف شوند؟`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'بله، حذف شود',
        cancelButtonText: 'انصراف',
        confirmButtonColor: '#d33'
    }).then((result) => {

        if (!result.isConfirmed) return;

        // حذف از جدول
        selectedIds.forEach(id => {
            const row = document.querySelector(`tr[data-image-id="${id}"]`);
            if (row) row.remove();
        });

        // حذف از state
        image_table_state.allImages =
            image_table_state.allImages.filter(img => !selectedIds.includes(img.id));

        image_table_state.selectedImageIds = [];

        syncCheckboxUI();

        Swal.fire({
            icon: 'success',
            title: 'انجام شد',
            text: 'تصاویر از لیست حذف شدند',
            timer: 1500,
            showConfirmButton: false
        });

    });

});




// تابع برای جمع‌آوری تمام مقادیر متادیتا از textareaها
function collectMetadataFromUI() {
    const metadata = {};
    const textareas = document.querySelectorAll('.metadata-input');
    
    textareas.forEach(textarea => {
        const field = textarea.dataset.field;
        if (field) {
            metadata[field] = textarea.value;
        }
    });
    
    return metadata;
}