"use strict";

// Class definition


var currentDatasetId = null;
var currentDatasetName = null;

// تابع تنظیم اطلاعات dataset قبل از باز شدن مودال
function setDatasetInfo(datasetId, datasetName) {
    currentDatasetId = datasetId;
    currentDatasetName = datasetName;
    console.log('Dataset info set:', datasetId, datasetName);
}


var KTFileManagerList = function () {
    // Define shared variables
    var datatable;
    var table

    // Define template element variables
    var uploadTemplate;
    var renameTemplate;
    var actionTemplate;
    var checkboxTemplate;


    // Private functions
    const initTemplates = () => {
        uploadTemplate = document.querySelector('[data-kt-filemanager-template="upload"]');
        renameTemplate = document.querySelector('[data-kt-filemanager-template="rename"]');
        actionTemplate = document.querySelector('[data-kt-filemanager-template="action"]');
        checkboxTemplate = document.querySelector('[data-kt-filemanager-template="checkbox"]');
    }

    const initDatatable = () => {
        // Set date data order
        const tableRows = table.querySelectorAll('tbody tr');

        tableRows.forEach(row => {
            const dateRow = row.querySelectorAll('td');
            const dateCol = dateRow[3]; // select date from 4th column in table
            const realDate = moment(dateCol.innerHTML, "DD MMM YYYY, LT").format();
            dateCol.setAttribute('data-order', realDate);
        });

        const foldersListOptions = {
            "info": false,
            'order': [],
            "scrollY": "700px",
            "scrollCollapse": true,
            "paging": false,
            'ordering': false,
            'columns': [
                { data: 'checkbox' },
                { data: 'name' },
                { data: 'size' },
                { data: 'date' },
                { data: 'action' },
            ],
            'language': {
                emptyTable: `<div class="d-flex flex-column flex-center">
                    <img src="${hostUrl}media/illustrations/sketchy-1/5.png" class="mw-400px" />
                    <div class="fs-1 fw-bolder text-dark">No items found.</div>
                    <div class="fs-6">Start creating new folders or uploading a new file!</div>
                </div>`
            }
        };

        const filesListOptions = {
            "info": false,
            'order': [],
            'pageLength': 10,
            "lengthChange": false,
            'ordering': false,
            'columns': [
                { data: 'checkbox' },
                { data: 'name' },
                { data: 'size' },
                { data: 'date' },
                { data: 'action' },
            ],
            'language': {
                emptyTable: `<div class="d-flex flex-column flex-center">
                    <img src="${hostUrl}media/illustrations/sketchy-1/5.png" class="mw-400px" />
                    <div class="fs-1 fw-bolder text-dark mb-4">No items found.</div>
                    <div class="fs-6">Start creating new folders or uploading a new file!</div>
                </div>`
            },
            conditionalPaging: true
        };

        // Define datatable options to load
        var loadOptions;
        if (table.getAttribute('data-kt-filemanager-table') === 'folders') {
            loadOptions = foldersListOptions;
        } else {
            loadOptions = filesListOptions;
        }

        // Init datatable --- more info on datatables: https://datatables.net/manual/
        datatable = $(table).DataTable(loadOptions);

        // Re-init functions on every table re-draw -- more info: https://datatables.net/reference/event/draw
        datatable.on('draw', function () {
            initToggleToolbar();
            handleDeleteRows();
            toggleToolbars();
            resetNewFolder();
            KTMenu.createInstances();
            initCopyLink();
            countTotalItems();
            handleRename();
        });
    }

    // Search Datatable --- official docs reference: https://datatables.net/reference/api/search()
    const handleSearchDatatable = () => {
        const filterSearch = document.querySelector('[data-kt-filemanager-table-filter="search"]');
        filterSearch.addEventListener('keyup', function (e) {
            datatable.search(e.target.value).draw();
        });
    }

    // Delete customer
    const handleDeleteRows = () => {
        // Select all delete buttons
        const deleteButtons = table.querySelectorAll('[data-kt-filemanager-table-filter="delete_row"]');

        deleteButtons.forEach(d => {
            // Delete button on click
            d.addEventListener('click', function (e) {
                e.preventDefault();

                // Select parent row
                const parent = e.target.closest('tr');

                // Get customer name
                const fileName = parent.querySelectorAll('td')[1].innerText;

                // SweetAlert2 pop up --- official docs reference: https://sweetalert2.github.io/
                Swal.fire({
                    text: "Are you sure you want to delete " + fileName + "?",
                    icon: "warning",
                    showCancelButton: true,
                    buttonsStyling: false,
                    confirmButtonText: "Yes, delete!",
                    cancelButtonText: "No, cancel",
                    customClass: {
                        confirmButton: "btn fw-bold btn-danger",
                        cancelButton: "btn fw-bold btn-active-light-primary"
                    }
                }).then(function (result) {
                    if (result.value) {
                        Swal.fire({
                            text: "You have deleted " + fileName + "!.",
                            icon: "success",
                            buttonsStyling: false,
                            confirmButtonText: "Ok, got it!",
                            customClass: {
                                confirmButton: "btn fw-bold btn-primary",
                            }
                        }).then(function () {
                            // Remove current row
                            datatable.row($(parent)).remove().draw();
                        });
                    } else if (result.dismiss === 'cancel') {
                        Swal.fire({
                            text: customerName + " was not deleted.",
                            icon: "error",
                            buttonsStyling: false,
                            confirmButtonText: "Ok, got it!",
                            customClass: {
                                confirmButton: "btn fw-bold btn-primary",
                            }
                        });
                    }
                });
            })
        });
    }

    // Init toggle toolbar
    const initToggleToolbar = () => {
        // Toggle selected action toolbar
        // Select all checkboxes
        var checkboxes = table.querySelectorAll('[type="checkbox"]');
        if (table.getAttribute('data-kt-filemanager-table') === 'folders') {
            checkboxes = document.querySelectorAll('#kt_file_manager_list_wrapper [type="checkbox"]');
        }

        // Select elements
        const deleteSelected = document.querySelector('[data-kt-filemanager-table-select="delete_selected"]');

        // Toggle delete selected toolbar
        checkboxes.forEach(c => {
            // Checkbox on click event
            c.addEventListener('click', function () {
                console.log(c);
                setTimeout(function () {
                    toggleToolbars();
                }, 50);
            });
        });

        // Deleted selected rows
        deleteSelected.addEventListener('click', function () {
            // SweetAlert2 pop up --- official docs reference: https://sweetalert2.github.io/
            Swal.fire({
                text: "Are you sure you want to delete selected files or folders?",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "Yes, delete!",
                cancelButtonText: "No, cancel",
                customClass: {
                    confirmButton: "btn fw-bold btn-danger",
                    cancelButton: "btn fw-bold btn-active-light-primary"
                }
            }).then(function (result) {
                if (result.value) {
                    Swal.fire({
                        text: "You have deleted all selected  files or folders!.",
                        icon: "success",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn fw-bold btn-primary",
                        }
                    }).then(function () {
                        // Remove all selected customers
                        checkboxes.forEach(c => {
                            if (c.checked) {
                                datatable.row($(c.closest('tbody tr'))).remove().draw();
                            }
                        });

                        // Remove header checked box
                        const headerCheckbox = table.querySelectorAll('[type="checkbox"]')[0];
                        headerCheckbox.checked = false;
                    });
                } else if (result.dismiss === 'cancel') {
                    Swal.fire({
                        text: "Selected  files or folders was not deleted.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn fw-bold btn-primary",
                        }
                    });
                }
            });
        });
    }

    // Toggle toolbars
    const toggleToolbars = () => {
        // Define variables
        const toolbarBase = document.querySelector('[data-kt-filemanager-table-toolbar="base"]');
        const toolbarSelected = document.querySelector('[data-kt-filemanager-table-toolbar="selected"]');
        const selectedCount = document.querySelector('[data-kt-filemanager-table-select="selected_count"]');

        // Select refreshed checkbox DOM elements 
        const allCheckboxes = table.querySelectorAll('tbody [type="checkbox"]');

        // Detect checkboxes state & count
        let checkedState = false;
        let count = 0;

        // Count checked boxes
        allCheckboxes.forEach(c => {
            if (c.checked) {
                checkedState = true;
                count++;
            }
        });

        // Toggle toolbars
        if (checkedState) {
            selectedCount.innerHTML = count;
            toolbarBase.classList.add('d-none');
            toolbarSelected.classList.remove('d-none');
        } else {
            toolbarBase.classList.remove('d-none');
            toolbarSelected.classList.add('d-none');
        }
    }

    // Handle new folder
    const handleNewFolder = () => {
        // Select button
        const newFolder = document.getElementById('kt_file_manager_new_folder');

        // Handle click action
        newFolder.addEventListener('click', e => {
            e.preventDefault();

            // Ignore if input already exist
            if (table.querySelector('#kt_file_manager_new_folder_row')) {
                return;
            }

            // Add new blank row to datatable
            const tableBody = table.querySelector('tbody');
            const rowElement = uploadTemplate.cloneNode(true); // Clone template markup
            tableBody.prepend(rowElement);

            // Define template interactive elements
            const rowForm = rowElement.querySelector('#kt_file_manager_add_folder_form');
            const rowButton = rowElement.querySelector('#kt_file_manager_add_folder');
            const cancelButton = rowElement.querySelector('#kt_file_manager_cancel_folder');
            const folderIcon = rowElement.querySelector('#kt_file_manager_folder_icon');
            const rowInput = rowElement.querySelector('[name="new_folder_name"]');

            // Define validator
            // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
            var validator = FormValidation.formValidation(
                rowForm,
                {
                    fields: {
                        'new_folder_name': {
                            validators: {
                                notEmpty: {
                                    message: 'Folder name is required'
                                }
                            }
                        },
                    },
                    plugins: {
                        trigger: new FormValidation.plugins.Trigger(),
                        bootstrap: new FormValidation.plugins.Bootstrap5({
                            rowSelector: '.fv-row',
                            eleInvalidClass: '',
                            eleValidClass: ''
                        })
                    }
                }
            );

            // Handle add new folder button
            rowButton.addEventListener('click', e => {
                e.preventDefault();

                // Activate indicator
                rowButton.setAttribute("data-kt-indicator", "on");

                // Validate form before submit
                if (validator) {
                    validator.validate().then(function (status) {
                        console.log('validated!');

                        if (status == 'Valid') {
                            // Simulate process for demo only
                            setTimeout(function () {
                                // Create folder link
                                const folderLink = document.createElement('a');
                                const folderLinkClasses = ['text-gray-800', 'text-hover-primary'];
                                folderLink.setAttribute('href', '?page=apps/file-manager/blank');
                                folderLink.classList.add(...folderLinkClasses);
                                folderLink.innerText = rowInput.value;

                                const newRow = datatable.row.add({
                                    'checkbox': checkboxTemplate.innerHTML,
                                    'name': folderIcon.outerHTML + folderLink.outerHTML,
                                    "size": '-',
                                    "date": '-',
                                    'action': actionTemplate.innerHTML
                                }).node();
                                $(newRow).find('td').eq(4).attr('data-kt-filemanager-table', 'action_dropdown');
                                $(newRow).find('td').eq(4).addClass('text-end'); // Add custom class to last 'td' element --- more info: https://datatables.net/forums/discussion/22341/row-add-cell-class

                                // Re-sort datatable to allow new folder added at the top
                                var index = datatable.row(0).index(),
                                    rowCount = datatable.data().length - 1,
                                    insertedRow = datatable.row(rowCount).data(),
                                    tempRow;

                                for (var i = rowCount; i > index; i--) {
                                    tempRow = datatable.row(i - 1).data();
                                    datatable.row(i).data(tempRow);
                                    datatable.row(i - 1).data(insertedRow);
                                }

                                toastr.options = {
                                    "closeButton": true,
                                    "debug": false,
                                    "newestOnTop": false,
                                    "progressBar": false,
                                    "positionClass": "toastr-top-right",
                                    "preventDuplicates": false,
                                    "showDuration": "300",
                                    "hideDuration": "1000",
                                    "timeOut": "5000",
                                    "extendedTimeOut": "1000",
                                    "showEasing": "swing",
                                    "hideEasing": "linear",
                                    "showMethod": "fadeIn",
                                    "hideMethod": "fadeOut"
                                };

                                toastr.success(rowInput.value + ' was created!');

                                // Disable indicator
                                rowButton.removeAttribute("data-kt-indicator");

                                // Reset input
                                rowInput.value = '';

                                datatable.draw(false);

                            }, 2000);
                        } else {
                            // Disable indicator
                            rowButton.removeAttribute("data-kt-indicator");
                        }
                    });
                }
            });

            // Handle cancel new folder button
            cancelButton.addEventListener('click', e => {
                e.preventDefault();

                // Activate indicator
                cancelButton.setAttribute("data-kt-indicator", "on");

                setTimeout(function () {
                    // Disable indicator
                    cancelButton.removeAttribute("data-kt-indicator");

                    // Toggle toastr
                    toastr.options = {
                        "closeButton": true,
                        "debug": false,
                        "newestOnTop": false,
                        "progressBar": false,
                        "positionClass": "toastr-top-right",
                        "preventDuplicates": false,
                        "showDuration": "300",
                        "hideDuration": "1000",
                        "timeOut": "5000",
                        "extendedTimeOut": "1000",
                        "showEasing": "swing",
                        "hideEasing": "linear",
                        "showMethod": "fadeIn",
                        "hideMethod": "fadeOut"
                    };

                    toastr.error('Cancelled new folder creation');
                    resetNewFolder();
                }, 1000);
            });
        });
    }

    // Reset add new folder input
    const resetNewFolder = () => {
        const newFolderRow = table.querySelector('#kt_file_manager_new_folder_row');

        if (newFolderRow) {
            newFolderRow.parentNode.removeChild(newFolderRow);
        }
    }

    // Handle rename file or folder
    const handleRename = () => {
        const renameButton = table.querySelectorAll('[data-kt-filemanager-table="rename"]');     

        renameButton.forEach(button => {
            button.addEventListener('click', renameCallback);
        });
    }

    // Rename callback
    const renameCallback = (e) => {
        e.preventDefault();

        // Define shared value
        let nameValue;

        // Stop renaming if there's an input existing
        if (table.querySelectorAll('#kt_file_manager_rename_input').length > 0) {
            Swal.fire({
                text: "Unsaved input detected. Please save or cancel the current item",
                icon: "warning",
                buttonsStyling: false,
                confirmButtonText: "Ok, got it!",
                customClass: {
                    confirmButton: "btn fw-bold btn-danger"
                }
            });

            return;
        }

        // Select parent row
        const parent = e.target.closest('tr');

        // Get name column
        const nameCol = parent.querySelectorAll('td')[1];
        const colIcon = nameCol.querySelector('.icon-wrapper');
        nameValue = nameCol.innerText;

        // Set rename input template
        const renameInput = renameTemplate.cloneNode(true);
        renameInput.querySelector('#kt_file_manager_rename_folder_icon').innerHTML = colIcon.outerHTML;

        // Swap current column content with input template
        nameCol.innerHTML = renameInput.innerHTML;

        // Set input value with current file/folder name
        parent.querySelector('#kt_file_manager_rename_input').value = nameValue;

        // Rename file / folder validator
        var renameValidator = FormValidation.formValidation(
            nameCol,
            {
                fields: {
                    'rename_folder_name': {
                        validators: {
                            notEmpty: {
                                message: 'Name is required'
                            }
                        }
                    },
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
                    })
                }
            }
        );

        // Rename input button action
        const renameInputButton = document.querySelector('#kt_file_manager_rename_folder');
        renameInputButton.addEventListener('click', e => {
            e.preventDefault();

            // Detect if valid
            if (renameValidator) {
                renameValidator.validate().then(function (status) {
                    console.log('validated!');

                    if (status == 'Valid') {
                        // Pop up confirmation
                        Swal.fire({
                            text: "Are you sure you want to rename " + nameValue + "?",
                            icon: "warning",
                            showCancelButton: true,
                            buttonsStyling: false,
                            confirmButtonText: "Yes, rename it!",
                            cancelButtonText: "No, cancel",
                            customClass: {
                                confirmButton: "btn fw-bold btn-danger",
                                cancelButton: "btn fw-bold btn-active-light-primary"
                            }
                        }).then(function (result) {
                            if (result.value) {
                                Swal.fire({
                                    text: "You have renamed " + nameValue + "!.",
                                    icon: "success",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn fw-bold btn-primary",
                                    }
                                }).then(function () {
                                    // Get new file / folder name value
                                    const newValue = document.querySelector('#kt_file_manager_rename_input').value;

                                    // New column data template
                                    const newData = `<div class="d-flex align-items-center">
                                        ${colIcon.outerHTML}
                                        <a href="?page=apps/file-manager/files/" class="text-gray-800 text-hover-primary">${newValue}</a>
                                    </div>`;

                                    // Draw datatable with new content -- Add more events here for any server-side events
                                    datatable.cell($(nameCol)).data(newData).draw();
                                });
                            } else if (result.dismiss === 'cancel') {
                                Swal.fire({
                                    text: nameValue + " was not renamed.",
                                    icon: "error",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn fw-bold btn-primary",
                                    }
                                });
                            }
                        });
                    }
                });
            }
        });

        // Cancel rename input
        const cancelInputButton = document.querySelector('#kt_file_manager_rename_folder_cancel');
        cancelInputButton.addEventListener('click', e => {
            e.preventDefault();

            // Simulate process for demo only
            cancelInputButton.setAttribute("data-kt-indicator", "on");

            setTimeout(function () {
                const revertTemplate = `<div class="d-flex align-items-center">
                    ${colIcon.outerHTML}
                    <a href="?page=apps/file-manager/files/" class="text-gray-800 text-hover-primary">${nameValue}</a>
                </div>`;

                // Remove spinner
                cancelInputButton.removeAttribute("data-kt-indicator");

                // Draw datatable with new content -- Add more events here for any server-side events
                datatable.cell($(nameCol)).data(revertTemplate).draw();

                // Toggle toastr
                toastr.options = {
                    "closeButton": true,
                    "debug": false,
                    "newestOnTop": false,
                    "progressBar": false,
                    "positionClass": "toastr-top-right",
                    "preventDuplicates": false,
                    "showDuration": "300",
                    "hideDuration": "1000",
                    "timeOut": "5000",
                    "extendedTimeOut": "1000",
                    "showEasing": "swing",
                    "hideEasing": "linear",
                    "showMethod": "fadeIn",
                    "hideMethod": "fadeOut"
                };

                toastr.error('Cancelled rename function');
            }, 1000);
        });
    }

    // Init dropzone
    const initDropzone = () => {
        const id = "#kt_modal_upload_dropzone";
        const dropzone = document.querySelector(id);
        
        if (!dropzone) return;
        
        var previewNode = dropzone.querySelector(".dropzone-item");
        previewNode.id = "";
        var previewTemplate = previewNode.parentNode.innerHTML;
        previewNode.parentNode.removeChild(previewNode);
        
        var myDropzone = new Dropzone(id, {
            url: "/infrence/api/upload_images",
            parallelUploads: 10,
            uploadMultiple: true,
            chunking: false,
            retryChunks: true,
            retryChunksLimit: 3,
            previewTemplate: previewTemplate,
            maxFiles: 50,
            maxFilesize: 10,
            acceptedFiles: ".jpeg,.jpg,.png,.pdf,.doc,.docx,.xls,.xlsx,.zip,.rar",
            autoProcessQueue: true,
            addRemoveLinks: true,
            timeout: 0,
            
            // ارسال CSRF Token و اطلاعات Dataset
            sending: function(file, xhr, formData) {
                // CSRF Token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfToken) {
                    formData.append('csrfmiddlewaretoken', csrfToken.value);
                }
                

            },
            
            // موفقیت آمیز
            success: function(file, response) {
                toastr.options = {
                    "closeButton": true,
                    "debug": false,
                    "newestOnTop": false,
                    "progressBar": false,
                    "positionClass": "toastr-top-right",
                    "preventDuplicates": false,
                    "showDuration": "300",
                    "hideDuration": "1000",
                    "timeOut": "5000",
                    "extendedTimeOut": "1000",
                    "showEasing": "swing",
                    "hideEasing": "linear",
                    "showMethod": "fadeIn",
                    "hideMethod": "fadeOut"
                };
                
                if (response.status === 'success') {
                    toastr.success(response.message || file.name + ' با موفقیت آپلود شد!');
                    file.previewElement.setAttribute('data-file-id', response.file_id || '');
                    file.previewElement.classList.add('dz-success');
                    fetchUploadedImages();
                } else {
                    toastr.error(response.message || 'خطا در آپلود ' + file.name);
                    file.previewElement.classList.add('dz-error');
                }
            },
            
            // خطا
            error: function(file, errorMessage) {
                toastr.options = {
                    "closeButton": true,
                    "debug": false,
                    "newestOnTop": false,
                    "progressBar": false,
                    "positionClass": "toastr-top-right",
                    "preventDuplicates": false,
                    "showDuration": "300",
                    "hideDuration": "1000",
                    "timeOut": "5000",
                    "extendedTimeOut": "1000",
                    "showEasing": "swing",
                    "hideEasing": "linear",
                    "showMethod": "fadeIn",
                    "hideMethod": "fadeOut"
                };
                
                let errorMsg = 'خطا در آپلود فایل';
                if (file.size > this.options.maxFilesize * 1024 * 1024) {
                    errorMsg = 'حجم فایل بیش از حد مجاز است';
                } else if (typeof errorMessage === 'string') {
                    errorMsg = errorMessage;
                }
                
                toastr.error(file.name + ': ' + errorMsg);
                file.previewElement.classList.add('dz-error');
            },
            
            // پیشرفت
            uploadprogress: function(file, progress, bytesSent) {
                const progressBar = file.previewElement.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.opacity = "1";
                    progressBar.style.width = Math.round(progress) + '%';
                }
            },
            
            // تکمیل
            complete: function(file) {
                const progressBar = file.previewElement.querySelector('.progress-bar');
                const progress = file.previewElement.querySelector('.progress');
                
                setTimeout(function () {
                    if (progressBar) progressBar.style.opacity = "0";
                    if (progress) progress.style.opacity = "0";
                }, 300);
            },
            
            // کل فایل‌ها تکمیل شدند
            queuecomplete: function(progress) {
                const uploadIcons = dropzone.querySelectorAll('.dropzone-upload');
                uploadIcons.forEach(uploadIcon => {
                    uploadIcon.style.display = "none";
                });
                
                const successFiles = myDropzone.getAcceptedFiles();
                const errorFiles = myDropzone.getRejectedFiles();
                
                toastr.options = {
                    "closeButton": true,
                    "debug": false,
                    "newestOnTop": false,
                    "progressBar": false,
                    "positionClass": "toastr-top-right",
                    "preventDuplicates": false,
                    "showDuration": "300",
                    "hideDuration": "1000",
                    "timeOut": "5000",
                    "extendedTimeOut": "1000",
                    "showEasing": "swing",
                    "hideEasing": "linear",
                    "showMethod": "fadeIn",
                    "hideMethod": "fadeOut"
                };
                
                if (successFiles.length > 0 && errorFiles.length > 0) {
                    toastr.warning(successFiles.length + ' فایل آپلود شد، ' + errorFiles.length + ' فایل با خطا مواجه شد');
                } else if (errorFiles.length > 0) {
                    toastr.error('هیچ فایلی آپلود نشد');
                }
                
                // ریست کردن اطلاعات dataset
                currentDatasetId = null;
                currentDatasetName = null;
                fetchUploadedImages();
            },
            
            previewsContainer: id + " .dropzone-items",
            clickable: id + " .dropzone-select"
        });
        
        myDropzone.on("addedfile", function (file) {
            const dropzoneItems = dropzone.querySelectorAll('.dropzone-item');
            dropzoneItems.forEach(dropzoneItem => {
                dropzoneItem.style.display = '';
            });
            dropzone.querySelector('.dropzone-upload').style.display = "inline-block";
            dropzone.querySelector('.dropzone-remove-all').style.display = "inline-block";
        });
        
        myDropzone.on("removedfile", function (file) {
            if (myDropzone.files.length < 1) {
                dropzone.querySelector('.dropzone-upload').style.display = "none";
                dropzone.querySelector('.dropzone-remove-all').style.display = "none";
            }
        });
        
        dropzone.querySelector(".dropzone-upload").addEventListener('click', function () {
            myDropzone.processQueue();
        });
        
        dropzone.querySelector(".dropzone-remove-all").addEventListener('click', function () {
            Swal.fire({
                text: "آیا مطمئن هستید که می‌خواهید همه فایل‌ها را حذف کنید؟",
                icon: "warning",
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: "بله، حذف شود",
                cancelButtonText: "خیر",
                customClass: {
                    confirmButton: "btn btn-primary",
                    cancelButton: "btn btn-active-light"
                }
            }).then(function (result) {
                if (result.value) {
                    dropzone.querySelector('.dropzone-upload').style.display = "none";
                    dropzone.querySelector('.dropzone-remove-all').style.display = "none";
                    myDropzone.removeAllFiles(true);
                }
            });
        });
    }
    // Init copy link
    const initCopyLink = () => {
        // Select all copy link elements
        const elements = table.querySelectorAll('[data-kt-filemanger-table="copy_link"]');

        elements.forEach(el => {
            // Define elements
            const button = el.querySelector('button');
            const generator = el.querySelector('[data-kt-filemanger-table="copy_link_generator"]');
            const result = el.querySelector('[data-kt-filemanger-table="copy_link_result"]');
            const input = el.querySelector('input');

            // Click action
            button.addEventListener('click', e => {
                e.preventDefault();

                // Reset toggle
                generator.classList.remove('d-none');
                result.classList.add('d-none');

                var linkTimeout;
                clearTimeout(linkTimeout);
                linkTimeout = setTimeout(() => {
                    generator.classList.add('d-none');
                    result.classList.remove('d-none');
                    input.select();
                }, 2000);
            });
        });
    }

    // Handle move to folder
    const handleMoveToFolder = () => {
        const element = document.querySelector('#kt_modal_move_to_folder');
        const form = element.querySelector('#kt_modal_move_to_folder_form');
        const saveButton = form.querySelector('#kt_modal_move_to_folder_submit');
        const moveModal = new bootstrap.Modal(element);

        // Init form validation rules. For more info check the FormValidation plugin's official documentation:https://formvalidation.io/
        var validator = FormValidation.formValidation(
            form,
            {
                fields: {
                    'move_to_folder': {
                        validators: {
                            notEmpty: {
                                message: 'Please select a folder.'
                            }
                        }
                    },
                },

                plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
                    })
                }
            }
        );

        saveButton.addEventListener('click', e => {
            e.preventDefault();

            saveButton.setAttribute("data-kt-indicator", "on");

            if (validator) {
                validator.validate().then(function (status) {
                    console.log('validated!');

                    if (status == 'Valid') {
                        // Simulate process for demo only
                        setTimeout(function () {

                            Swal.fire({
                                text: "Are you sure you would like to move to this folder",
                                icon: "warning",
                                showCancelButton: true,
                                buttonsStyling: false,
                                confirmButtonText: "Yes, move it!",
                                cancelButtonText: "خیر",
                                customClass: {
                                    confirmButton: "btn btn-primary",
                                    cancelButton: "btn btn-active-light"
                                }
                            }).then(function (result) {
                                if (result.isConfirmed) {
                                    form.reset(); // Reset form	
                                    moveModal.hide(); // Hide modal			

                                    toastr.options = {
                                        "closeButton": true,
                                        "debug": false,
                                        "newestOnTop": false,
                                        "progressBar": false,
                                        "positionClass": "toastr-top-right",
                                        "preventDuplicates": false,
                                        "showDuration": "300",
                                        "hideDuration": "1000",
                                        "timeOut": "5000",
                                        "extendedTimeOut": "1000",
                                        "showEasing": "swing",
                                        "hideEasing": "linear",
                                        "showMethod": "fadeIn",
                                        "hideMethod": "fadeOut"
                                    };

                                    toastr.success('1 item has been moved.');

                                    saveButton.removeAttribute("data-kt-indicator");
                                } else {
                                    Swal.fire({
                                        text: "Your action has been cancelled!.",
                                        icon: "error",
                                        buttonsStyling: false,
                                        confirmButtonText: "Ok, got it!",
                                        customClass: {
                                            confirmButton: "btn btn-primary",
                                        }
                                    });

                                    saveButton.removeAttribute("data-kt-indicator");
                                }
                            });
                        }, 500);
                    } else {
                        saveButton.removeAttribute("data-kt-indicator");
                    }
                });
            }
        });
    }

    // Count total number of items
    const countTotalItems = () => {
        const counter = document.getElementById('kt_file_manager_items_counter');

        // Count total number of elements in datatable --- more info: https://datatables.net/reference/api/count()
        counter.innerText = datatable.rows().count() + ' items';
    }

    // Public methods
    return {
        init: function () {
            initDropzone();
            return
            table = document.querySelector('#kt_file_manager_list');

            if (!table) {
                return;
            }

            initTemplates();
            initDatatable();
            initToggleToolbar();
            handleSearchDatatable();
            handleDeleteRows();
            handleNewFolder();
            initDropzone();
            initCopyLink();
            handleRename();
            handleMoveToFolder();
            countTotalItems();
            KTMenu.createInstances();
        }
    }
}();

// On document ready
KTUtil.onDOMContentLoaded(function () {
    KTFileManagerList.init();
});


// تابع دریافت تصاویر از سرور
function fetchUploadedImages() {
    fetch('/infrence/api/get_uploaded_images')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.images.length > 0) {
                renderCarousel(data.images);
            }
        })
        .catch(error => {
            console.error('Error fetching images:', error);
        });
}

// متغیرهای سراسری برای مدیریت صفحات
let currentPage = 0;
const itemsPerPage = 5;
let allImages = [];

// تابع رندر کردن لیست تصاویر
function renderCarousel(images) {
    const container = document.getElementById('images_carousel_container');
    const imagesListContainer = document.getElementById('images_list_container');
    const prevBtn = document.getElementById('prev_images_btn');
    const nextBtn = document.getElementById('next_images_btn');
    const counter = document.getElementById('images_counter');
    
    if (!container || !imagesListContainer) return;
    
    // ذخیره تمام تصاویر
    allImages = images;
    currentPage = 0;
    
    // پاک کردن محتوای قبلی
    imagesListContainer.innerHTML = '';
    
    // نمایش کانتینر
    container.style.display = 'block';
    
    // رندر صفحه اول
    renderCurrentPage();
    
    // تنظیم دکمه‌ها
    updateButtons();
    
    // رویداد کلیک دکمه‌ها
    prevBtn.onclick = () => {
        if (currentPage > 0) {
            currentPage--;
            renderCurrentPage();
            updateButtons();
        }
    };
    
    nextBtn.onclick = () => {
        const totalPages = Math.ceil(allImages.length / itemsPerPage);
        if (currentPage < totalPages - 1) {
            currentPage++;
            renderCurrentPage();
            updateButtons();
        }
    };
}

// تابع رندر صفحه جاری
function renderCurrentPage() {
    const imagesListContainer = document.getElementById('images_list_container');
    const counter = document.getElementById('images_counter');
    
    // پاک کردن محتوای قبلی
    imagesListContainer.innerHTML = '';
    
    // محاسبه ایندکس شروع و پایان
    const startIndex = currentPage * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, allImages.length);
    
    // دریافت تصاویر صفحه جاری
    const currentImages = allImages.slice(startIndex, endIndex);
    
    // ساخت تصاویر - همه با سایز ثابت
    // ساخت کانتینر با flex-wrap: nowrap برای نمایش در یک ردیف
    imagesListContainer.style.cssText = 'display: flex; flex-wrap: nowrap; gap: 16px; overflow-x: auto; padding: 10px;';

    // ساخت تصاویر - همه با سایز ثابت
    currentImages.forEach((image, index) => {
        const imageWrapper = document.createElement('div');
        imageWrapper.className = 'image-item';
        imageWrapper.style.cssText = 'flex: 0 0 auto; width: 150px; text-align: center;';
        imageWrapper.innerHTML = `
            <div class="symbol symbol-150px" style="width: 150px; height: 150px; cursor: pointer; border-radius: 8px; overflow: hidden;" 
                onclick="showImagePreview('${image.url}', '${image.name}')"
                ondblclick="showImagePreview('${image.url}', '${image.name}')">
                <img src="${image.url}" alt="${image.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;"
                    onerror="this.outerHTML='<div class=\"symbol symbol-150px bg-light-secondary rounded d-flex align-items-center justify-content-center\" style=\"width: 100%; height: 100%;\"><i class=\"ki-duotone ki-image fs-2x text-gray-400\"></i></div>'">
            </div>
            <span class="text-gray-600 fs-7 mt-2 d-block text-truncate" style="width: 150px;" title="${image.name}">${image.name}</span>
        `;
        imagesListContainer.appendChild(imageWrapper);
    });
    // به‌روزرسانی شمارنده
    if (counter) {
        counter.textContent = `${startIndex + 1} - ${endIndex} از ${allImages.length}`;
    }
}

// تابع به‌روزرسانی وضعیت دکمه‌ها
function updateButtons() {
    const prevBtn = document.getElementById('prev_images_btn');
    const nextBtn = document.getElementById('next_images_btn');
    const totalPages = Math.ceil(allImages.length / itemsPerPage);
    
    // غیرفعال/فعال کردن دکمه قبلی
    if (currentPage === 0) {
        prevBtn.classList.add('disabled');
        prevBtn.setAttribute('disabled', 'true');
    } else {
        prevBtn.classList.remove('disabled');
        prevBtn.removeAttribute('disabled');
    }
    
    // غیرفعال/فعال کردن دکمه بعدی
    if (currentPage >= totalPages - 1) {
        nextBtn.classList.add('disabled');
        nextBtn.setAttribute('disabled', 'true');
    } else {
        nextBtn.classList.remove('disabled');
        nextBtn.removeAttribute('disabled');
    }
}

// ✅ تابع نمایش پیش نمایش تصویر بزرگ - با دیباگ
function showImagePreview(imageUrl, imageName) {
    console.log('Image URL:', imageUrl);
    console.log('Image Name:', imageName);
    
    const modal = document.getElementById('image_preview_modal');
    const previewImg = document.getElementById('preview_image');
    const title = document.getElementById('image_preview_title');
    const errorDiv = document.getElementById('preview_error');
    
    // تنظیم عنوان و تصویر
    title.textContent = imageName;
    previewImg.src = imageUrl;
    
    // مخفی کردن پیام خطا
    previewImg.style.display = 'block';
    if (errorDiv) errorDiv.style.display = 'none';
    
    // نمایش مودال
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}



fetchUploadedImages()






// متغیرهای زوم
let currentScale = 1;
let minScale = 0.5;
let maxScale = 5;
let translateX = 0;
let translateY = 0;
let isDragging = false;
let startX = 0;
let startY = 0;

// تابع نمایش پیش نمایش تصویر بزرگ
function showImagePreview(imageUrl, imageName) {
    const modal = document.getElementById('image_preview_modal');
    const previewImg = document.getElementById('preview_image');
    const title = document.getElementById('image_preview_title');
    const errorDiv = document.getElementById('preview_error');
    const imageWrapper = document.getElementById('image_wrapper');
    
    // ریست زوم
    resetZoomValues();
    
    // تنظیم عنوان و تصویر
    title.textContent = imageName;
    previewImg.src = imageUrl;
    
    // مخفی کردن پیام خطا
    previewImg.style.display = 'block';
    if (errorDiv) errorDiv.style.display = 'none';
    
    // نمایش مودال
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
}

// ریست کردن مقادیر زوم
function resetZoomValues() {
    currentScale = 1;
    translateX = 0;
    translateY = 0;
    updateTransform();
}

// ریست زوم با دکمه
function resetZoom() {
    resetZoomValues();
}

// به‌روزرسانی transform تصویر
function updateTransform() {
    const imageWrapper = document.getElementById('image_wrapper');
    if (imageWrapper) {
        imageWrapper.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
    }
    
    // به‌روزرسانی نمایش درصد زوم
    const zoomLevel = document.getElementById('zoom_level');
    if (zoomLevel) {
        zoomLevel.textContent = `زوم: ${Math.round(currentScale * 100)}%`;
    }
}

// مدیریت زوم با اسکرول موس
function handleZoom(event) {
    event.preventDefault();
    
    const delta = event.deltaY > 0 ? -0.1 : 0.1;
    const newScale = Math.max(minScale, Math.min(maxScale, currentScale + delta));
    
    if (newScale !== currentScale) {
        currentScale = newScale;
        
        // اگر زوم شد، موقعیت را مرکز کن
        if (currentScale > 1) {
            // حفظ موقعیت دراگ
        } else {
            translateX = 0;
            translateY = 0;
        }
        
        updateTransform();
    }
}

// شروع دراگ
function startDrag(event) {
    if (event.button !== 0) return; // فقط کلیک چپ
    isDragging = true;
    startX = event.clientX - translateX;
    startY = event.clientY - translateY;
    
    const imageWrapper = document.getElementById('image_wrapper');
    if (imageWrapper) {
        imageWrapper.style.cursor = 'grabbing';
        imageWrapper.style.transition = 'none';
    }
}

// دراگ کردن
function drag(event) {
    if (!isDragging) return;
    
    event.preventDefault();
    translateX = event.clientX - startX;
    translateY = event.clientY - startY;
    
    updateTransform();
}

// توقف دراگ
function stopDrag(event) {
    isDragging = false;
    
    const imageWrapper = document.getElementById('image_wrapper');
    if (imageWrapper) {
        imageWrapper.style.cursor = 'grab';
        imageWrapper.style.transition = 'transform 0.1s ease-out';
    }
}

// ریست زوم هنگام بسته شدن مودال
document.getElementById('image_preview_modal').addEventListener('hidden.bs.modal', function () {
    resetZoomValues();
});