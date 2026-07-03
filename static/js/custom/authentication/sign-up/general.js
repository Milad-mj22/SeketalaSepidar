"use strict";

// تعریف کلاس ثبت‌نام
var KTSignupGeneral = function () {
    // المان‌ها
    var form;
    var submitButton;
    var validator;
    var passwordMeter;

    // دریافت توکن CSRF
    var getCsrfToken = function() {
        return document.querySelector('meta[name="csrf-token"]') 
            ? document.querySelector('meta[name="csrf-token"]').getAttribute('content') 
            : '';
    };

    // مدیریت فرم (حالت شبیه‌سازی - بدون ارسال واقعی)
    var handleForm = function (e) {
        // قوانین اعتبارسنجی فرم
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
                    'new_password2': {
                        validators: {
                            notEmpty: {
                                message: 'کلمه عبور الزامی است'
                            },
                            stringLength: {
                                min: 8,
                                message: 'کلمه عبور باید حداقل 8 کاراکتر باشد'
                            },
                            callback: {
                                message: 'کلمه عبور باید قدرت متوسط یا بیشتر داشته باشد',
                                callback: function (input) {
                                    if (input.value.length > 0) {
                                        return validatePassword();
                                    }
                                }
                            }
                        }
                    },
                    'confirm-password': {
                        validators: {
                            notEmpty: {
                                message: 'تکرار کلمه عبور الزامی است'
                            },
                            identical: {
                                compare: function () {
                                    return form.querySelector('[name="password"]').value;
                                },
                                message: 'کلمه عبور و تکرار آن یکسان نیستند'
                            }
                        }
                    },
                    'toc': {
                        validators: {
                            notEmpty: {
                                message: 'پذیرش قوانین و مقررات الزامی است'
                            }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger({
                        event: {
                            password: false
                        }
                    }),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
                    })
                }
            }
        );

        // مدیریت کلیک دکمه ثبت‌نام
        submitButton.addEventListener('click', function (e) {
            e.preventDefault();
            
            // بررسی مجدد فیلدها
            validator.revalidateField('new_password2');
            validator.revalidateField('password_confirmation');
            
            validator.validate().then(function (status) {
                if (status === 'Valid') {
                    // نمایش لودینگ
                    submitButton.setAttribute('data-kt-indicator', 'on');
                    submitButton.disabled = true;

                    // دریافت آدرس action فرم
                    var actionUrl = form.getAttribute('action');
                    
                    // بررسی وجود آدرس
                    if (!actionUrl || actionUrl === '#' || actionUrl === '') {
                        submitButton.removeAttribute('data-kt-indicator');
                        submitButton.disabled = false;
                        Swal.fire({
                            text: "آدرس ثبت‌نام تعریف نشده است.",
                            icon: "error",
                            buttonsStyling: false,
                            confirmButtonText: "متوجه شدم",
                            customClass: {
                                confirmButton: "btn btn-primary"
                            }
                        });
                        return;
                    }
                    
                    // ایجاد FormData
                    var formData = new FormData(form);
                    
                    // ارسال درخواست به سرور
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
                        if (response.data.status === 'success' || response.status === 200 || response.status === 201) {
                            // نمایش پیغام موفقیت
                            Swal.fire({
                                text: response.data.message || "ثبت‌نام با موفقیت انجام شد!",
                                icon: "success",
                                buttonsStyling: false,
                                confirmButtonText: "متوجه شدم",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            }).then(function (result) {
                                if (result.isConfirmed) {
                                    // ریست فرم
                                    form.reset();
                                    if (passwordMeter) {
                                        passwordMeter.reset();
                                    }
                                    
                                    // ریدایرکت به صفحه مقصد
                                    var redirectUrl = response.data.redirect_url || form.getAttribute('data-kt-redirect-url');
                                    if (redirectUrl) {
                                        location.href = redirectUrl;
                                    }
                                }
                            });
                        } else {
                            // پاسخ ناموفق از سرور
                            Swal.fire({
                                text: response.data.message || "ثبت‌نام ناموفق بود. لطفاً دوباره تلاش کنید.",
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
                            // خطا از سمت سرور
                            if (error.response.data.errors) {
                                // نمایش تمام خطاهای اعتبارسنجی
                                var errors = error.response.data.errors;
                                var firstErrorField = Object.keys(errors)[0];
                                var firstError = errors[firstErrorField];
                                errorMessage = Array.isArray(firstError) ? firstError[0] : firstError;
                                
                                // نمایش خطا در فیلد مربوطه
                                if (firstErrorField) {
                                    validator.updateFieldStatus(firstErrorField, 'Invalid', errorMessage);
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
                            // خطای شبکه
                            errorMessage = "خطا در ارتباط با سرور. لطفاً اتصال شبکه خود را بررسی کنید.";
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
                        text: "لطفاً تمام فیلدهای الزام را به درستی تکمیل کنید.",
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


        // مدیریت ورودی رمز عبور برای اعتبارسنجی زنده
        form.querySelector('input[name="new_password2"]').addEventListener('input', function () {
            if (this.value.length > 0) {
                validator.updateFieldStatus('new_password2', 'NotValidated');
            }
        });
    };

    // مدیریت فرم با ارسال واقعی به سرور
    var handleFormAjax = function (e) {
        // قوانین اعتبارسنجی فرم
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
                    'new_password2': {
                        validators: {
                            notEmpty: {
                                message: 'کلمه عبور الزامی است'
                            },
                            stringLength: {
                                min: 8,
                                message: 'کلمه عبور باید حداقل 8 کاراکتر باشد'
                            },
                            callback: {
                                message: 'کلمه عبور باید قدرت متوسط یا بیشتر داشته باشد',
                                callback: function (input) {
                                    if (input.value.length > 0) {
                                        return validatePassword();
                                    }
                                }
                            }
                        }
                    },
                    'confirm-password': {
                        validators: {
                            notEmpty: {
                                message: 'تکرار کلمه عبور الزامی است'
                            },
                            identical: {
                                compare: function () {
                                    return form.querySelector('[name="password"]').value;
                                },
                                message: 'کلمه عبور و تکرار آن یکسان نیستند'
                            }
                        }
                    },
                    'toc': {
                        validators: {
                            notEmpty: {
                                message: 'پذیرش قوانین و مقررات الزامی است'
                            }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger({
                        event: {
                            password: false
                        }
                    }),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: '',
                        eleValidClass: ''
                    })
                }
            }
        );

        // مدیریت کلیک دکمه ثبت‌نام
        submitButton.addEventListener('click', function (e) {
            e.preventDefault();
            
            // بررسی مجدد فیلدها
            validator.revalidateField('new_password2');
            validator.revalidateField('password_confirmation');
            
            validator.validate().then(function (status) {
                if (status === 'Valid') {
                    // نمایش لودینگ
                    submitButton.setAttribute('data-kt-indicator', 'on');
                    submitButton.disabled = true;

                    // دریافت آدرس action فرم
                    var actionUrl = form.getAttribute('action');
                    
                    // ایجاد FormData
                    var formData = new FormData(form);
                    
                    // ارسال درخواست به سرور
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
                        if (response.data.status === 'success' || response.status === 200 || response.status === 201) {
                            // نمایش پیغام موفقیت
                            Swal.fire({
                                text: response.data.message || "ثبت‌نام با موفقیت انجام شد!",
                                icon: "success",
                                buttonsStyling: false,
                                confirmButtonText: "متوجه شدم",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            }).then(function (result) {
                                if (result.isConfirmed) {
                                    // ریست فرم
                                    form.reset();
                                    if (passwordMeter) {
                                        passwordMeter.reset();
                                    }
                                    
                                    // ریدایرکت به صفحه مقصد
                                    var redirectUrl = response.data.redirect_url || form.getAttribute('data-kt-redirect-url');
                                    if (redirectUrl) {
                                        location.href = redirectUrl;
                                    }
                                }
                            });
                        } else {
                            // پاسخ ناموفق از سرور
                            Swal.fire({
                                text: response.data.message || "ثبت‌نام ناموفق بود. لطفاً دوباره تلاش کنید.",
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
                            // خطا از سمت سرور
                            if (error.response.data.errors) {
                                // نمایش اولین خطای اعتبارسنجی
                                var errors = error.response.data.errors;
                                var firstErrorField = Object.keys(errors)[0];
                                var firstError = errors[firstErrorField];
                                errorMessage = Array.isArray(firstError) ? firstError[0] : firstError;
                                
                                // نمایش خطا در فیلد مربوطه
                                if (firstErrorField) {
                                    validator.updateFieldStatus(firstErrorField, 'Invalid', errorMessage);
                                }
                            } else if (error.response.data.message) {
                                errorMessage = error.response.data.message;
                            } else if (error.response.status === 401) {
                                errorMessage = "اطلاعات وارد شده صحیح نیست.";
                            } else if (error.response.status === 422) {
                                errorMessage = "لطفاً اطلاعات را به درستی وارد کنید.";
                            } else if (error.response.status === 500) {
                                errorMessage = "خطای سرور. لطفاً بعداً تلاش کنید.";
                            }
                        } else if (error.request) {
                            // خطای شبکه
                            errorMessage = "خطا در ارتباط با سرور. لطفاً اتصال شبکه خود را بررسی کنید.";
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
                        text: "لطفاً تمام فیلدهای الزام را به درستی تکمیل کنید.",
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

        // مدیریت ورودی رمز عبور برای اعتبارسنجی زنده
        form.querySelector('input[name="new_password2"]').addEventListener('input', function () {
            if (this.value.length > 0) {
                validator.updateFieldStatus('new_password2', 'NotValidated');
            }
        });
    };

    // اعتبارسنجی قدرت رمز عبور
    var validatePassword = function () {
        if (!passwordMeter) {
            return true; // اگر متر وجود نداشت، رد کن
        }
        var score = passwordMeter.getScore();
        return score > 50; // حداقل امتیاز 50
    };

    // بررسی معتبر بودن URL
    var isValidUrl = function(url) {
        if (!url || url === '#' || url === '') {
            return false;
        }
        try {
            new URL(url);
            return true;
        } catch (e) {
            // بررسی نسبی
            return url.startsWith('/') || url.startsWith('http');
        }
    };

    // تابع عمومی
    return {
        // مقداردهی اولیه
        init: function () {
            // دریافت المان‌ها
            form = document.querySelector('#kt_sign_up_form2');
            console.log(form)
            submitButton = document.querySelector('#kt_sign_up_submit');
            
            // دریافت متر رمز عبور
            var passwordMeterElement = form.querySelector('[data-kt-password-meter="true"]');
            if (passwordMeterElement) {
                passwordMeter = KTPasswordMeter.getInstance(passwordMeterElement);
            }

            // بررسی نوع ارسال فرم
            var actionUrl = form.getAttribute('action');
            
            if (isValidUrl(actionUrl)) {
                // ارسال واقعی به سرور
                handleFormAjax();
            } else {
                // حالت شبیه‌سازی
                handleForm();
            }
        }
    };
}();

// اجرای کد پس از آماده شدن DOM
KTUtil.onDOMContentLoaded(function () {
    KTSignupGeneral.init();
});