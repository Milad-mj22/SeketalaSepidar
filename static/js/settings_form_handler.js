document.addEventListener('DOMContentLoaded', function() {
    
   // مدیریت دکمه‌های لغو و بازنشانی با SweetAlert2
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        
        const action = btn.dataset.action;
        const formType = btn.dataset.formType;
        
        if (action === 'cancel') {
            // نمایش SweetAlert2 برای لغو
            Swal.fire({
                title: 'تایید عملیات',
                html: 'آیا می‌خواهید تنظیمات را به آخرین تغییرات بازگردانید؟',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'بله، بازگردان شود',
                cancelButtonText: 'خیر',
                confirmButtonClass: 'btn btn-primary',
                cancelButtonClass: 'btn btn-active-light',
                buttonsStyling: false,
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    handleCancel(formType);
                }
            });
            
        } else if (action === 'reset') {
            // نمایش SweetAlert2 برای بازنشانی
            Swal.fire({
                title: 'تایید عملیات',
                html: 'آیا می‌خواهید تنظیمات را به مقادیر پیش‌فرض بازگردانید؟',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'بله، بازنشانی شود',
                cancelButtonText: 'خیر',
                confirmButtonClass: 'btn btn-primary',
                cancelButtonClass: 'btn btn-active-light',
                buttonsStyling: false,
                reverseButtons: true
            }).then((result) => {
                if (result.isConfirmed) {
                    handleReset(formType);
                }
            });
        }
    });
    
   
    
    // تابع پر کردن فرم با داده‌ها
    function populateForm(formType, data) {
        const form = document.querySelector(`form[data-form-type="${formType}"]`);
        if (!form) return;
        
        for (const [fieldName, value] of Object.entries(data)) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.value = value;
                
                // برای checkbox
                if (field.type === 'checkbox') {
                    field.checked = value;
                }
                
                // برای select
                if (field.tagName === 'SELECT') {
                    field.value = value;
                }
            }
        }
    }
    
    // تابع لغو (بازگشت به آخرین رکورد)
    function handleCancel(formType) {
        fetch(`api/get-last-record/${formType}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    populateForm(formType, data.data);
                    toastr.success('تنظیمات به آخرین تغییرات بازگردانده شد');

                    
                } else {
                    toastr.error('خطا در دریافت اطلاعات');

                }
            })
            .catch(error => {
                console.error('Error:', error);
                toastr.error('خطا در ارتباط با سرور');
            });
    }
    
    // تابع بازنشانی (بازگشت به مقادیر پیش‌فرض)
    function handleReset(formType) {
        fetch(`api/reset-to-defaults/${formType}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateForm(formType, data.data);
                toastr.success('تنظیمات به مقادیر پیش‌فرض بازگردانده شد');
            } else {
                console.log(data.message);
                toastr.error('خطا در بازنشانی');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastr.error('خطا در ارتباط با سرور');
            
        });
    }
    
    // دریافت CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    
    
    // مدیریت ارسال فرم (SAVE)
    function setupFormSubmit(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formType = form.dataset.formType;
            const messageId = formType + '-message';
            const submitBtn = form.querySelector('button[type="submit"]');
            
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> در حال ذخیره...';
            
            const formData = new FormData(form);
            formData.append('form_type', formType);
            
            fetch('api/save-settings', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastr.success(data.message);

                } else {
                    let errorText = '';
                    for (const [field, errors] of Object.entries(data.errors)) {
                        errorText += `${field}: ${errors.join(', ')}<br>`;
                    }
                    toastr.error(errorText);

                }
            })
            .catch(error => {
                console.error('Error:', error);
                toastr.error('خطا در ارتباط با سرور');

            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="ki-duotone ki-check fs-2"><span class="path1"></span><span class="path2"></span></i> ذخیره';
            });
        });
    }
    
    // راه‌اندازی فرم‌ها
    const forms = document.querySelectorAll('form[data-form-type]');
    forms.forEach(form => setupFormSubmit(form));
    
});