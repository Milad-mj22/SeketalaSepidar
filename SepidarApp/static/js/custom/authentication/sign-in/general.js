"use strict";

// کلاس مدیریت فرم ورود
var KTSigninGeneral = function () {
    // المان‌ها
    var form;
    var submitButton;
    var validator;

    // دریافت توکن CSRF
    var getCsrfToken = function() {
        var tokenEl = document.querySelector('meta[name="csrf-token"]');
        return tokenEl ? tokenEl.getAttribute('content') : '';
    };

    // اعتبارسنجی فرم
    var handleValidation = function () {
        validator = FormValidation.formValidation(
            form,
            {
                fields: {
                    'phone': {
                        validators: {
                            notEmpty: {
                                message: 'نام کاربری یا شماره تماس الزامی است'
                            },
                            regexp: {
                                regexp: /^(09[0-9]{9}|[a-zA-Z0-9_]{3,20})$/,
                                message: 'شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود یا نام کاربری معتبر وارد کنید (حداقل ۳ کاراکتر)'
                            }
                        }
                    },
                    'password': {
                        validators: {
                            notEmpty: {
                                message: 'کلمه عبور الزامی است'
                            }
                        }
                    }
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
    };

    // ارسال واقعی به سرور
    var handleSubmitAjax = function () {
        submitButton.addEventListener('click', function (e) {
            e.preventDefault();
            
            validator.validate().then(function (status) {
                if (status === 'Valid') {
                    // نمایش لودینگ
                    submitButton.setAttribute('data-kt-indicator', 'on');
                    submitButton.disabled = true;

                    var actionUrl = form.getAttribute('action');
                    var formData = new FormData(form);

                    // ارسال به سرور
                    axios.post(actionUrl, formData, {
                        headers: {
                            'Accept': 'application/json',
                            'X-CSRF-TOKEN': getCsrfToken()
                        }
                    })
                    .then(function (response) {
                        // مخفی کردن لودینگ
                        submitButton.removeAttribute('data-kt-indicator');
                        submitButton.disabled = false;

                        // بررسی پاسخ سرور
                        if (response.data.status === 'success' || response.status === 200) {
                            // نمایش پیغام موفقیت
                            Swal.fire({
                                text: response.data.message || "ورود با موفقیت انجام شد!",
                                icon: "success",
                                timer: 2000, // 2 ثانیه (بر حسب میلی‌ثانیه)
                                timerProgressBar: true,
                                showConfirmButton: false, // دکمه «متوجه شدم» نمایش داده نشود
                                buttonsStyling: false,
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            }).then(function (result) {
                                // بعد از تمام شدن تایمر (یعنی auto-close)
                                // ریست فرم
                                form.reset();

                                // ریدایرکت
                                var redirectUrl = response.data.redirect_url || form.getAttribute('data-kt-redirect-url');
                                if (redirectUrl) {
                                    location.href = redirectUrl;
                                }
                            });

                        } else {
                            // پاسخ ناموفق
                            Swal.fire({
                                text: response.data.message || "ورود ناموفق بود.",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "متوجه شدم",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                        }
                    })
                    .catch(function (error) {
                        // مخفی کردن لودینگ
                        submitButton.removeAttribute('data-kt-indicator');
                        submitButton.disabled = false;

                        // مدیریت خطاها
                        var errorMessage = "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.";
                        
                        if (error.response) {
                            if (error.response.data.errors) {
                                // خطاهای اعتبارسنجی
                                var errors = error.response.data.errors;
                                var firstField = Object.keys(errors)[0];
                                errorMessage = Array.isArray(errors[firstField]) ? errors[firstField][0] : errors[firstField];
                                
                                // نمایش خطا در فیلد
                                if (firstField) {
                                    validator.updateFieldStatus(firstField, 'Invalid', errorMessage);
                                }
                            } else if (error.response.data.message) {
                                errorMessage = error.response.data.message;
                            } else if (error.response.status === 401) {
                                errorMessage = "شماره موبایل یا کلمه عبور اشتباه است.";
                            } else if (error.response.status === 422) {
                                errorMessage = "لطفاً اطلاعات را به درستی وارد کنید.";
                            } else if (error.response.status === 500) {
                                errorMessage = "خطای سرور. لطفاً بعداً تلاش کنید.";
                            }
                        } else if (error.request) {
                            errorMessage = "خطا در ارتباط با سرور. اتصال شبکه را بررسی کنید.";
                        }

                        // نمایش پیغام خطا
                        Swal.fire({
                            text: errorMessage,
                            icon: "error",
                            buttonsStyling: false,
                            confirmButtonText: "متوجه شدم",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            }
                        });
                    });
                } else {
                    // اعتبارسنجی ناموفق
                    Swal.fire({
                        text: "لطفاً تمام فیلدهای الزام را تکمیل کنید.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "متوجه شدم",
                        customClass: {
                            confirmButton: "btn btn-primary"
                        }
                    });
                }
            });
        });
    };

    // بررسی URL معتبر
    var isValidUrl = function(url) {
        if (!url || url === '#' || url === '') {
            return false;
        }
        try {
            new URL(url);
            return true;
        } catch (e) {
            return url.startsWith('/') || url.startsWith('http');
        }
    };

    // تابع عمومی
    return {
        init: function () {
            form = document.querySelector('#kt_sign_in_form');
            submitButton = document.querySelector('#kt_sign_in_submit');

            if (!form || !submitButton) {
                console.error('فرم یا دکمه ورود یافت نشد!');
                return;
            }

            handleValidation();
            
            var actionUrl = form.getAttribute('action');
            if (isValidUrl(actionUrl)) {
                handleSubmitAjax();
            } else {
                // حالت آفلاین (دمو)
                console.log('آدرس فرم معتبر نیست. از حالت دمو استفاده می‌شود.');
            }
        }
    };
}();

// اجرا پس از آماده شدن DOM
KTUtil.onDOMContentLoaded(function () {
    KTSigninGeneral.init();
});