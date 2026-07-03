"use strict";

var KTModalNewAddress = function () {
    var submitButton;
    var cancelButton;
    var validator;
    var form;
    var modal;
    var modalEl;

    var handleForm = function () {
        validator = FormValidation.formValidation(
            form,
            {
                fields: {
                    'name': {
                        validators: {
                            notEmpty: {
                                message: 'نام کلاس نیاز است'
                            }
                        }
                    },
                    'code': {
                        validators: {
                            notEmpty: {
                                message: 'کد کلاس نیاز است'
                            }
                        }
                    },

                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger(),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: '.fv-row',
                        eleInvalidClass: 'is-invalid',
                        eleValidClass: 'is-valid'
                    })
                }
            }
        );

        submitButton.addEventListener('click', function (e) {
            e.preventDefault();

            if (validator) {
                validator.validate().then(function (status) {
                    if (status === 'Valid') {
                        submitButton.setAttribute('data-kt-indicator', 'on');
                        submitButton.disabled = true;

                        var formData = new FormData(form);
                        var url = form.getAttribute('action');
                        
                        console.log('Sending to:', url);
                        console.log('Form data:', Object.fromEntries(formData));

                        fetch(url, {
                            method: 'POST',
                            body: formData,
                            headers: {
                                'X-CSRFToken': getCookie('csrftoken'),
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        })
                        .then(response => {
                            console.log('Response status:', response.status);
                            console.log('Response headers:', response.headers);
                            return response.json();
                        })
                        .then(data => {
                            console.log('Response data:', data);
                            submitButton.removeAttribute('data-kt-indicator');
                            submitButton.disabled = false;

                            if (data.success) {
                                Swal.fire({
                                    text: data.message || 'با موفقیت ثبت گردید.',
                                    icon: 'success',
                                    buttonsStyling: false,
                                    confirmButtonText: 'تمام',
                                    customClass: {
                                        confirmButton: 'btn btn-primary'
                                    }
                                }).then(function (result) {
                                    if (result.isConfirmed) {
                                        modal.hide();
                                        form.reset();
                                        location.reload();
                                    }
                                });
                            } else {
                                Swal.fire({
                                    text: data.message || 'خطایی رخ داده است.',
                                    icon: 'error',
                                    buttonsStyling: false,
                                    confirmButtonText: 'متوجه شدم',
                                    customClass: {
                                        confirmButton: 'btn btn-primary'
                                    }
                                });
                            }
                        })
                        .catch(error => {
                            console.error('Fetch Error:', error);
                            submitButton.removeAttribute('data-kt-indicator');
                            submitButton.disabled = false;

                            Swal.fire({
                                text: 'خطا در ارتباط با سرور.',
                                icon: 'error',
                                buttonsStyling: false,
                                confirmButtonText: 'متوجه شدم',
                                customClass: {
                                    confirmButton: 'btn btn-primary'
                                }
                            });
                        });

                    } else {
                        Swal.fire({
                            text: 'لطفا تمام فیلدهای الزامی را تکمیل کنید.',
                            icon: 'warning',
                            buttonsStyling: false,
                            confirmButtonText: 'متوجه شدم',
                            customClass: {
                                confirmButton: 'btn btn-primary'
                            }
                        });
                    }
                });
            }
        });

        cancelButton.addEventListener('click', function (e) {
            e.preventDefault();
            Swal.fire({
                text: 'آیا مطمئن هستید که می‌خواهید لغو کنید؟',
                icon: 'warning',
                showCancelButton: true,
                buttonsStyling: false,
                confirmButtonText: 'بله، لغو کن',
                cancelButtonText: 'خیر',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-active-light'
                }
            }).then(function (result) {
                if (result.value) {
                    form.reset();
                    validator.resetForm(true);
                    modal.hide();
                }
            });
        });
    };

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    return {
        init: function () {
            modalEl = document.querySelector('#new_defect');
            if (!modalEl) {
                console.error('Modal element not found!');
                return;
            }

            modal = new bootstrap.Modal(modalEl);
            form = document.querySelector('#new_defect_form');
            submitButton = document.getElementById('new_defect_submit');
            cancelButton = document.getElementById('new_defect_cancel');

            console.log('Form action:', form.getAttribute('action'));
            
            handleForm();

            modalEl.addEventListener('hidden.bs.modal', function () {
                form.reset();
                validator.resetForm(true);
            });
        }
    };
}();

KTUtil.onDOMContentLoaded(function () {
    KTModalNewAddress.init();
});