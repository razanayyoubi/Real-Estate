document.addEventListener('DOMContentLoaded', () => {

    /* ─────────────────────────────────────────────────────────
       2. MOUSE PARALLAX – Luxury panel glass visual tilt
       ───────────────────────────────────────────────────────── */
    document.addEventListener('mousemove', (e) => {
        const panels = document.querySelectorAll('.glass-panel');
        const x = (window.innerWidth - e.pageX * 2) / 100;
        const y = (window.innerHeight - e.pageY * 2) / 100;

        panels.forEach(panel => {
            panel.style.transform = `translate(${x}px, ${y}px)`;
        });
    });

    /* ─────────────────────────────────────────────────────────
       3. CLIENT-SIDE VALIDATION & AJAX SUBMIT
       ───────────────────────────────────────────────────────── */
    const form = document.getElementById('signup-form');
    const btnSubmit = document.getElementById('btn-submit');
    const alertBox = document.getElementById('signup-alert-box');

    if (!form || !btnSubmit || !alertBox) return;

    // Helper: show or hide validation errors on individual input fields
    const toggleFieldError = (inputId, errorId, showMsg) => {
        const input = document.getElementById(inputId);
        const error = document.getElementById(errorId);
        if (!input || !error) return;

        if (showMsg) {
            input.classList.add('input-error');
            error.classList.add('visible');
        } else {
            input.classList.remove('input-error');
            error.classList.remove('visible');
        }
    };

    // Attach listeners to clear error messages immediately as the user starts typing
    const setupErrorClearing = (inputId, errorId) => {
        const input = document.getElementById(inputId);
        if (!input) return;
        const eventType = input.type === 'checkbox' ? 'change' : 'input';
        input.addEventListener(eventType, () => {
            toggleFieldError(inputId, errorId, false);
        });
    };

    setupErrorClearing('full_name', 'err-full-name');
    setupErrorClearing('email', 'err-email');
    setupErrorClearing('phone_number', 'err-phone-number');
    setupErrorClearing('password', 'err-password');
    setupErrorClearing('confirm_password', 'err-confirm-password');
    setupErrorClearing('terms', 'err-terms');

    // Email format validator
    const isValidEmail = (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim());

    // Display top-level alert boxes (Success/Error)
    const showAlert = (message, type) => {
        alertBox.className = 'signup-alert-box'; // reset classes
        alertBox.textContent = message;
        if (type === 'success') {
            alertBox.classList.add('alert-success');
        } else {
            alertBox.classList.add('alert-error');
        }
        
        // Scroll to the alert box smoothly so they see it
        const topOffset = alertBox.getBoundingClientRect().top + window.scrollY - 100;
        window.scrollTo({ top: topOffset, behavior: 'smooth' });
    };

    const hideAlert = () => {
        alertBox.className = 'signup-alert-box';
        alertBox.textContent = '';
    };

    // Handle Form Submit Event
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();

        // 1. Gather input elements
        const fullNameInput = document.getElementById('full_name');
        const emailInput = document.getElementById('email');
        const phoneInput = document.getElementById('phone_number');
        const addressInput = document.getElementById('address');
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm_password');
        const termsCheckbox = document.getElementById('terms');

        let isValid = true;

        // 2. Validate inputs
        if (!fullNameInput.value.trim()) {
            toggleFieldError('full_name', 'err-full-name', true);
            isValid = false;
        }

        if (!isValidEmail(emailInput.value)) {
            toggleFieldError('email', 'err-email', true);
            isValid = false;
        }

        if (phoneInput && phoneInput.value.trim()) {
            const phoneVal = phoneInput.value.trim();
            const phoneRegex = /^\+?[0-9\s\-()]+$/;
            const digitsOnly = phoneVal.replace(/\D/g, '');
            if (!phoneRegex.test(phoneVal) || digitsOnly.length < 6) {
                toggleFieldError('phone_number', 'err-phone-number', true);
                isValid = false;
            }
        }

        if (passwordInput.value.length < 6) {
            toggleFieldError('password', 'err-password', true);
            isValid = false;
        }

        if (passwordInput.value !== confirmInput.value) {
            toggleFieldError('confirm_password', 'err-confirm-password', true);
            isValid = false;
        }

        if (!termsCheckbox.checked) {
            const termsErr = document.getElementById('err-terms');
            if (termsErr) termsErr.style.display = 'block';
            isValid = false;
        } else {
            const termsErr = document.getElementById('err-terms');
            if (termsErr) termsErr.style.display = 'none';
        }

        if (!isValid) {
            // Focus first error element
            const firstErr = form.querySelector('.input-error');
            if (firstErr) firstErr.focus();
            return;
        }

        // 3. Prep data payload
        const payload = {
            full_name: fullNameInput.value.trim(),
            email: emailInput.value.trim(),
            phone_number: phoneInput ? phoneInput.value.trim() : '',
            address: addressInput ? addressInput.value.trim() : '',
            password: passwordInput.value
        };

        // 4. Toggle loader state on submit button
        const originalBtnContent = btnSubmit.innerHTML;
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `
            <svg class="animate-spin" style="width:20px; height:20px; color:#ffffff; animation: float-anim 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle style="opacity:0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path style="opacity:0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Processing...</span>
        `;

        // 5. Submit AJAX request to Flask Backend
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (response.ok) {
                // Success State
                form.reset();
                showAlert('Account created successfully! Redirecting to login page...', 'success');
                btnSubmit.innerHTML = `
                    <span class="material-symbols-outlined" style="font-size:18px;">check_circle</span>
                    <span>Account Created!</span>
                `;
                btnSubmit.style.backgroundColor = '#198754'; // Bootstrap success green

                // Wait 1.8 seconds and redirect to login page
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1800);

            } else {
                // Backend validation failure (e.g. Email exists)
                showAlert(result.error || 'Registration failed. Please check inputs.', 'error');
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = originalBtnContent;
                btnSubmit.style.backgroundColor = ''; // revert to CSS default
            }

        } catch (error) {
            // Network / Server failure
            console.error('Submit registration error:', error);
            showAlert('Network error. Unable to connect to server. Please try again.', 'error');
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = originalBtnContent;
            btnSubmit.style.backgroundColor = '';
        }
    });
});
