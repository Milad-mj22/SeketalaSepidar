var datasetIds = [];
var modelId;
var weightId;

function update_dataset_ids() {
    const datasetSelect = document.getElementById('dataset_select');
    datasetIds = Array.from(datasetSelect.selectedOptions).map(option => option.value);
    console.log(datasetIds);
}

function update_model_ids() {
    modelId = document.getElementById('model_select').value;
    weightId = document.getElementById('weight_select').value;
}

function update_model_ids() {
    modelId = document.getElementById('model_select').value;
    weightId = document.getElementById('weight_select').value;
}
// ساخت درخت از لیست تخت
function buildDefectTree(defects) {
    const tree = [];
    const map = {};
    const rootNodes = [];

    // ساخت map از همه عیوب
    defects.forEach(d => {
        map[d.id] = { ...d, children: [] };
    });

    // مرتب‌سازی درخت
    defects.forEach(d => {
        if (d.parent_id && map[d.parent_id]) {
            map[d.parent_id].children.push(map[d.id]);
        } else {
            rootNodes.push(map[d.id]);
        }
    });

    // مرتب‌سازی بر اساس نام
    const sortChildren = (nodes) => {
        nodes.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'fa'));
        nodes.forEach(n => sortChildren(n.children));
    };
    sortChildren(rootNodes);

    return rootNodes;
}
function renderTree(nodes, parentNode, level = 0) {
    nodes.forEach(node => {
        const hasChildren = node.children && node.children.length > 0;
        const itemId = `tree-item-${node.id}`;

        // ساخت آیتم
        const itemHtml = `
            <div class="tree-node" data-node-id="${node.id}" data-parent-id="${node.parent_id || ''}">
                <div class="tree-item ${hasChildren ? 'has-children' : ''}" id="${itemId}">
                    <span class="tree-toggle ${hasChildren ? '' : 'hidden'}" onclick="toggleBranch('${node.id}')">
                        <i class="ki-duotone ki-right fs-6"></i>
                    </span>
                    <input type="checkbox"
                           class="tree-checkbox"
                           id="defect_${node.id}"
                           value="${node.id}"
                           data-name="${node.name || ''}"
                           data-parent-id="${node.parent_id || ''}"
                           data-parent-name="${node.parent_name || ''}"
                           data-has-children="${hasChildren}"
                           onclick="handleTreeCheckbox(this, '${node.id}')">
                    <span class="tree-color" style="background-color: ${node.color || '#ccc'}"></span>
                    <span class="tree-label">${node.name || ''}</span>
                    <span class="branch-indicator" id="indicator_${node.id}" style="display: none;"></span>
                    ${hasChildren ? `<span class="branch-toggle" onclick="toggleBranch('${node.id}')">
                        <span id="toggle_text_${node.id}">(${node.children.length})</span>
                    </span>` : ''}
                </div>
                ${hasChildren ? `
                    <div class="tree-branch" id="branch_${node.id}">
                        <div class="tree-children"></div>
                    </div>
                ` : ''}
            </div>
        `;

        // اضافه کردن به والد
        parentNode.insertAdjacentHTML('beforeend', itemHtml);

        // رندر فرزندان - پیدا کردن المنت صحیح
        if (hasChildren) {
            const branch = document.getElementById(`branch_${node.id}`);
            const childrenContainer = branch.querySelector('.tree-children');
            renderTree(node.children, childrenContainer, level + 1);
        }
    });
}

    // باز/بسته کردن شاخه
    function toggleBranch(nodeId) {
        const branch = document.getElementById(`branch_${nodeId}`);
        const toggle = document.querySelector(`.tree-node[data-node-id="${nodeId}"] .tree-toggle`);
        const toggleText = document.getElementById(`toggle_text_${nodeId}`);

        if (branch && branch.classList.contains('expanded')) {
            branch.classList.remove('expanded');
            if (toggle) toggle.classList.remove('expanded');
        } else {
            if (branch) branch.classList.add('expanded');
            if (toggle) toggle.classList.add('expanded');
        }
    }

    // باز کردن همه شاخه‌ها
    function expandAll() {
        document.querySelectorAll('.tree-branch').forEach(b => b.classList.add('expanded'));
        document.querySelectorAll('.tree-toggle:not(.hidden)').forEach(t => t.classList.add('expanded'));
    }

    // بستن همه شاخه‌ها
    function collapseAll() {
        document.querySelectorAll('.tree-branch').forEach(b => b.classList.remove('expanded'));
        document.querySelectorAll('.tree-toggle').forEach(t => t.classList.remove('expanded'));
    }

    // مدیریت انتخاب چک‌باکس درخت
    function handleTreeCheckbox(checkbox, nodeId) {
        const isChecked = checkbox.checked;
        const node = document.querySelector(`.tree-node[data-node-id="${nodeId}"]`);
        const branch = document.getElementById(`branch_${nodeId}`);
        const item = document.getElementById(`tree-item-${nodeId}`);

        // بروزرسانی ظاهر آیتم
        if (isChecked) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }

        // باز کردن شاخه‌های فرزندان هنگام انتخاب
        if (isChecked && branch) {
            branch.classList.add('expanded');
            branch.querySelectorAll('.tree-toggle').forEach(t => t.classList.add('expanded'));
        }

        // انتخاب/لغو انتخاب همه فرزندان
        if (branch) {
            const childCheckboxes = branch.querySelectorAll('.tree-checkbox');
            childCheckboxes.forEach(child => {
                child.checked = isChecked;
                const childId = child.value;
                const childItem = document.getElementById(`tree-item-${childId}`);
                if (isChecked) {
                    childItem.classList.add('selected');
                } else {
                    childItem.classList.remove('selected');
                }
            });
        }

        // بروزرسانی نشانگر والد
        updateParentIndicators(nodeId);

        // بروزرسانی شمارنده
        updateSelectedCount();
    }

    // بروزرسانی نشانگرهای والد
    function updateParentIndicators(nodeId) {
        const node = document.querySelector(`.tree-node[data-node-id="${nodeId}"]`);
        if (!node) return;

        const parentId = node.dataset.parentId;
        if (!parentId) return;

        const parentNode = document.querySelector(`.tree-node[data-node-id="${parentId}"]`);
        if (!parentNode) return;

        const parentBranch = parentNode.querySelector('.tree-children');
        const parentIndicator = document.getElementById(`indicator_${parentId}`);
        const parentCheckbox = document.getElementById(`defect_${parentId}`);
        const parentItem = document.getElementById(`tree-item-${parentId}`);

        if (parentBranch) {
            const allChildren = parentBranch.querySelectorAll('.tree-checkbox');
            const checkedChildren = parentBranch.querySelectorAll('.tree-checkbox:checked');

            if (checkedChildren.length === 0) {
                parentIndicator.style.display = 'none';
                parentCheckbox.checked = false;
                parentItem.classList.remove('selected');
            } else if (checkedChildren.length === allChildren.length) {
                parentIndicator.style.display = 'inline-block';
                parentIndicator.className = 'branch-indicator full';
                parentIndicator.textContent = '✓';
                parentCheckbox.checked = true;
                parentItem.classList.add('selected');
            } else {
                parentIndicator.style.display = 'inline-block';
                parentIndicator.className = 'branch-indicator partial';
                parentIndicator.textContent = `${checkedChildren.length}/${allChildren.length}`;
                parentCheckbox.checked = false;
                parentItem.classList.remove('selected');
            }
        }

        // بازگشت به بالا
        updateParentIndicators(parentId);
    }

    // بروزرسانی شمارنده انتخاب‌ها
    function updateSelectedCount() {
        const checked = document.querySelectorAll('.tree-checkbox:checked');
        const count = checked.length;

        document.getElementById('selected_count_badge').textContent =
            `${toPersianNum(count)} عیب انتخاب شده`;

        // برای شمارش تصاویر نیاز به اطلاعات اضافی از سرور دارید
        // اینجا فعلاً یک عدد نمونه نمایش می‌دهیم
        // document.getElementById('selected_images').textContent = toPersianNum(count * 125);
    }

function openSplitModal() {
    update_dataset_ids();
    update_model_ids();
    
    console.log('Dataset IDs:', datasetIds);
    console.log('Model ID:', modelId);
    console.log('Weight ID:', weightId);

    if (!datasetIds || datasetIds.length === 0) {
        Swal.fire({
            title: 'خطا',
            text: 'باید حتماً دیتاست انتخاب شده باشد',
            icon: 'warning',
            confirmButtonText: 'باشه'
        });
        return;
    }

    if (!modelId) {
        Swal.fire({
            title: 'خطا',
            text: 'باید حتماً یک مدل انتخاب شده باشد',
            icon: 'warning',
            confirmButtonText: 'باشه'
        });
        return;
    }

    if (!weightId) {
        Swal.fire({
            title: 'خطا',
            text: 'باید حتماً یک وزن انتخاب شده باشد',
            icon: 'warning',
            confirmButtonText: 'باشه'
        });
        return;
    }

    // ✅ بررسی انتخاب دیتاست
    if (!datasetIds || datasetIds.length === 0) {
        Swal.fire({
            title: 'خطا',
            text: 'باید حتماً دیتاست انتخاب شده باشد',
            icon: 'warning',
            confirmButtonText: 'باشه'
        });
        return;
    }
    
    document.getElementById('train_percent').value = 80;
    document.getElementById('val_percent').value = 20;
    document.getElementById('summary_section').style.display = 'none';
    document.getElementById('defects_table_section').style.display = 'none';
    document.getElementById('modal_footer').style.display = 'none';
    document.getElementById('defects_table_body').innerHTML = '';

    // ریست چک‌باکس‌ها
    document.querySelectorAll('.tree-checkbox').forEach(cb => {
        cb.checked = false;
        cb.disabled = false;
    });
    document.querySelectorAll('.tree-item').forEach(item => {
        item.classList.remove('selected');
    });

    // بازسازی درخت عیوب
    const container = document.getElementById('defects_tree');
    container.innerHTML = '';

    const tree = buildDefectTree(ALL_DEFECTS);
    
    // ✅ تغییر: پاس دادن المنت container به جای null
    renderTree(tree, container);

    // باز کردن همه شاخه‌ها به صورت پیش‌فرض
    expandAll();

    updateSelectedCount();

    const modal = new bootstrap.Modal(document.getElementById('split_modal'));
    modal.show();
}

    // انتخاب همه
    function selectAllDefects() {
        document.querySelectorAll('.tree-checkbox').forEach(cb => {
            cb.checked = true;
            const item = document.getElementById(`tree-item-${cb.value}`);
            if (item) item.classList.add('selected');
        });
        updateSelectedCount();
    }

    // لغو همه
    function deselectAllDefects() {
        document.querySelectorAll('.tree-checkbox').forEach(cb => {
            cb.checked = false;
            const item = document.getElementById(`tree-item-${cb.value}`);
            if (item) item.classList.remove('selected');
        });
        document.querySelectorAll('.branch-indicator').forEach(ind => {
            ind.style.display = 'none';
        });
        updateSelectedCount();
    }

    // محاسبه تقسیم
    function calculateSplit() {
        const trainPercent = parseInt(document.getElementById('train_percent').value) || 80;
        const valPercent = parseInt(document.getElementById('val_percent').value) || 20;

        if (trainPercent + valPercent !== 100) {
            Swal.fire({
                title: 'خطا',
                text: 'مجموع درصدها باید ۱۰۰ باشد',
                icon: 'warning',
                confirmButtonText: 'باشه'
            });
            return;
        }

        // جمع‌آوری عیوب انتخاب شده
        const selectedDefects = [];
        document.querySelectorAll('.tree-checkbox:checked').forEach(cb => {
            selectedDefects.push({
                id: parseInt(cb.value),
                name: cb.dataset.name,
                parent_id: cb.dataset.parentId ? parseInt(cb.dataset.parentId) : null
            });
        });

        if (selectedDefects.length === 0) {
            Swal.fire({
                title: 'خطا',
                text: 'لطفاً حداقل یک عیب انتخاب کنید',
                icon: 'warning',
                confirmButtonText: 'باشه'
            });
            return;
        }

        fetch('/ai/calculate-split/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                dataset_ids: datasetIds,
                model_id : modelId,
                weight_id : weightId,
                train_percent: trainPercent,
                val_percent: valPercent,
                selected_defects: selectedDefects
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderResults(data);
            } else {
                showError(data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('خطا در برقراری ارتباط با سرور');
        });
    }

    // نمایش نتایج
    function renderResults(data) {
        document.getElementById('summary_section').style.display = 'flex';
        document.getElementById('total_count').textContent = formatNumber(data.summary.total);
        document.getElementById('train_count').textContent = formatNumber(data.summary.train);
        document.getElementById('val_count').textContent = formatNumber(data.summary.val);

        document.getElementById('defects_table_section').style.display = 'block';
        document.getElementById('modal_footer').style.display = 'flex';

        const tbody = document.getElementById('defects_table_body');
        tbody.innerHTML = data.defects.map(defect => `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <span class="badge rounded-circle me-2"
                              style="background-color: ${defect.color}; width: 10px; height: 10px;">
                        </span>
                        <span class="fw-bold">${defect.name}</span>
                        ${defect.parent_name ? `
                            <span class="badge bg-secondary ms-2" style="font-size: 10px;">
                                والد ${defect.parent_name}
                            </span>
                        ` : ''}
                    </div>
                </td>
                <td class="text-center fw-bold">${formatNumber(defect.total)}</td>
                <td class="text-center bg-success bg-opacity-10">
                    <span class="text-success fw-bold">${formatNumber(defect.train)}</span>
                </td>
                <td class="text-center bg-warning bg-opacity-10">
                    <span class="text-warning fw-bold">${formatNumber(defect.val)}</span>
                </td>
            </tr>
        `).join('');
    }

    // تأیید
function confirmSplit() {
    const trainPercent = parseInt(document.getElementById('train_percent').value);
    const valPercent = parseInt(document.getElementById('val_percent').value);
    const model_id = parseInt(document.getElementById('model_select').value);

    const selectedDefects = [];
    document.querySelectorAll('.tree-checkbox:checked').forEach(cb => {
        selectedDefects.push({
            id: parseInt(cb.value),
            name: cb.dataset.name,
            parent_id: cb.dataset.parentId ? parseInt(cb.dataset.parentId) : null
        });
    });

    const data = {
        dataset_ids: datasetIds,
        train_percent: trainPercent,
        val_percent: valPercent,
        selected_defects: selectedDefects,
        model_id: modelId,
        weight_id: weightId,
    };

    // ۱. بستن مودال تقسیم
    bootstrap.Modal.getInstance(document.getElementById('split_modal')).hide();

    // ۲. نمایش پیام موفقیت ۱ ثانیه‌ای
    Swal.fire({
        title: 'موفق',
        text: 'تقسیم دیتاست با موفقیت ذخیره شد',
        icon: 'success',
        timer: 1000,
        showConfirmButton: false,
        timerProgressBar: true,
        didClose: () => {
            // ۳. باز کردن مودال پیشرفت
            startDatasetCreation(data);
        }
    });
}

    // همزمان کردن درصدها
    document.getElementById('train_percent').addEventListener('input', function() {
        document.getElementById('val_percent').value = 100 - parseInt(this.value || 0);
    });

    document.getElementById('val_percent').addEventListener('input', function() {
        document.getElementById('train_percent').value = 100 - parseInt(this.value || 0);
    });

    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    function toPersianNum(num) {
        const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
        return num.toString().replace(/\d/g, d => persianDigits[d]);
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    function showError(message) {
        Swal.fire({
            title: 'خطا',
            text: message,
            icon: 'error',
            confirmButtonText: 'باشه'
        });
    }









let eventSource = null;
// ========== شروع ایجاد دیتاست ==========

function startDatasetCreation(data) {
    // نمایش مودال پیشرفت
    const progressModal = new bootstrap.Modal(document.getElementById('progress_modal'));
    progressModal.show();
    
    // ریست کردن مقادیر
    document.getElementById('progress_bar').style.width = '0%';
    document.getElementById('progress_percent').textContent = toPersianNum(0);
    document.getElementById('progress_message').textContent = 'در حال آماده‌سازی...';
    document.getElementById('current_defect').textContent = '-';
    document.getElementById('progress_stats').style.display = 'none';

    // ارسال درخواست برای شروع پروسه
    fetch('api/preparing-train/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // شروع اتصال SSE برای پیشرفت
            tmID = document.getElementById('trainingModelID')
            tmID.dataset.train_model_id = result.train_model_id
            startProgressSSE(result.train_model_id);
        } else {
            // خطا
            document.getElementById('progress_message').textContent = 'خطا: ' + result.error;
            document.getElementById('progress_message').classList.add('text-danger');
            
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('progress_modal')).hide();
            }, 2000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('progress_message').textContent = 'خطا در برقراری ارتباط';
        setTimeout(() => {
            bootstrap.Modal.getInstance(document.getElementById('progress_modal')).hide();
        }, 2000);
    });
}

// ========== اتصال SSE برای پیشرفت ==========
function startProgressSSE(trainModelId) {
    // بستن اتصال قبلی اگر وجود دارد
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`/ai/sse/create-dataset/${trainModelId}/`);

    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        switch (data.status) {
            case 'started':
                document.getElementById('progress_message').textContent = data.message;
                break;

            case 'progress':
                updateDatasetGenProgress(data);
                break;

            case 'completed':
                showCompletionStats(data);
                eventSource.close();
                
                // بستن مودال بعد از ۲ ثانیه
                setTimeout(() => {
                    bootstrap.Modal.getInstance(document.getElementById('progress_modal')).hide();
                    
                    // نمایش پیام نهایی
                    Swal.fire({
                        title: 'تکمیل شد!',
                        html: `
                            <div class="text-start">
                                <p class="mb-2">دیتاست با موفقیت ایجاد شد.</p>
                                <div class="bg-light p-3 rounded text-dark">
                                    <div class="mb-1">
                                        <i class="ki-duotone ki-folder text-primary me-1"></i>
                                        <strong>مسیر:</strong> ${data.output_dir}
                                    </div>
                                    <div class="mb-1">
                                        <i class="ki-duotone ki-check-circle text-success me-1"></i>
                                        <strong>آموزش:</strong> ${toPersianNum(data.train_count)} تصویر
                                    </div>
                                    <div>
                                        <i class="ki-duotone ki-check-circle text-warning me-1"></i>
                                        <strong>ارزیابی:</strong> ${toPersianNum(data.val_count)} تصویر
                                    </div>
                                </div>
                            </div>
                        `,
                        icon: 'success',
                        timer: 2000, // 2 ثانیه (بر حسب میلی‌ثانیه)
                        timerProgressBar: true,
                        showConfirmButton: false, // دکمه «متوجه شدم» نمایش داده نشود
                        buttonsStyling: false,
                    });
                }, 2000);
                handleStartTrainingClick()

                break;

            case 'error':
                document.getElementById('progress_message').textContent = 'خطا: ' + data.message;
                document.getElementById('progress_message').classList.add('text-danger');
                eventSource.close();
                
                setTimeout(() => {
                    bootstrap.Modal.getInstance(document.getElementById('progress_modal')).hide();
                }, 3000);
                break;
        }
    };

    eventSource.onerror = function() {
        console.error('SSE Error');
        eventSource.close();
        
        // تلاش مجدد یا نمایش خطا
        setTimeout(() => {
            bootstrap.Modal.getInstance(document.getElementById('progress_modal')).hide();
        }, 2000);
    };
}

// ========== بروزرسانی نوار پیشرفت ==========
function updateDatasetGenProgress(data) {
    const progressBar = document.getElementById('progress_bar');
    const progressPercent = document.getElementById('progress_percent');
    const progressMessage = document.getElementById('progress_message');
    const currentDefect = document.getElementById('current_defect');

    // بروزرسانی نوار
    progressBar.style.width = data.progress + '%';
    progressBar.setAttribute('aria-valuenow', data.progress);
    
    // بروزرسانی درصد
    progressPercent.textContent = toPersianNum(data.progress);
    
    // بروزرسانی پیام
    progressMessage.textContent = data.message;
    
    // بروزرسانی عیب فعلی
    if (data.defect_name) {
        currentDefect.textContent = data.defect_name;
    }
}

// ========== نمایش آمار نهایی ==========
function showCompletionStats(data) {
    document.getElementById('progress_message').textContent = 'تکمیل شد! ✓';
    document.getElementById('progress_message').classList.remove('text-danger');
    document.getElementById('progress_bar').classList.remove('progress-bar-animated');
    document.getElementById('progress_bar').style.width = '100%';
    document.getElementById('progress_percent').textContent = toPersianNum(100);
    document.getElementById('progress_details').style.display = 'none';
    
    // نمایش آمار
    document.getElementById('progress_stats').style.display = 'flex';
    document.getElementById('stat_train').textContent = toPersianNum(data.train_count);
    document.getElementById('stat_val').textContent = toPersianNum(data.val_count);
}

// ========== تبدیل اعداد به فارسی ==========
function toPersianNum(num) {
    if (num === undefined || num === null) return '-';
    const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    return num.toString().replace(/\d/g, d => persianDigits[d]);
}