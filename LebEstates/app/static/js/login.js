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
    const form = document.getElementById('login-form');
    const btnSubmit = document.getElementById('btn-submit');
    const alertBox = document.getElementById('login-alert-box');

    if (!form || !btnSubmit || !alertBox) return;

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

    const setupErrorClearing = (inputId, errorId) => {
        const input = document.getElementById(inputId);
        if (!input) return;
        input.addEventListener('input', () => {
            toggleFieldError(inputId, errorId, false);
        });
    };

    setupErrorClearing('email', 'err-email');
    setupErrorClearing('password', 'err-password');
    setupErrorClearing('code', 'err-code');

    const isValidEmail = (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val.trim());

    const showAlert = (message, type) => {
        alertBox.className = 'signup-alert-box';
        alertBox.textContent = message;
        if (type === 'success') {
            alertBox.classList.add('alert-success');
        } else {
            alertBox.classList.add('alert-error');
        }
    };

    const hideAlert = () => {
        alertBox.className = 'signup-alert-box';
        alertBox.textContent = '';
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();

        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const codeInput = document.getElementById('code');
        const fieldGroup2fa = document.getElementById('2fa-field-group');

        let isValid = true;

        if (!isValidEmail(emailInput.value)) {
            toggleFieldError('email', 'err-email', true);
            isValid = false;
        }

        if (!passwordInput.value) {
            toggleFieldError('password', 'err-password', true);
            isValid = false;
        }

        const is2faVisible = fieldGroup2fa && fieldGroup2fa.style.display !== 'none';
        if (is2faVisible && (!codeInput.value || codeInput.value.length !== 6)) {
            toggleFieldError('code', 'err-code', true);
            isValid = false;
        }

        if (!isValid) {
            const firstErr = form.querySelector('.input-error');
            if (firstErr) firstErr.focus();
            return;
        }

        const payload = {
            email: emailInput.value.trim(),
            password: passwordInput.value
        };

        if (is2faVisible) {
            payload.code = codeInput.value.trim();
        }

        const originalBtnContent = btnSubmit.innerHTML;
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `
            <svg class="animate-spin" style="width:20px; height:20px; color:#ffffff; animation: float-anim 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle style="opacity:0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path style="opacity:0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Authenticating...</span>
        `;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (response.ok) {
                if (result.two_factor_required) {
                    // Show 2FA input
                    showAlert('Two-Factor Authentication is required. Please check your Authenticator app.', 'success');
                    fieldGroup2fa.style.display = 'block';
                    codeInput.setAttribute('required', 'true');
                    btnSubmit.disabled = false;
                    btnSubmit.innerHTML = `
                        <span>Verify & Login</span>
                        <span class="material-symbols-outlined arrow-icon">verified_user</span>
                    `;
                    btnSubmit.style.backgroundColor = '';
                    codeInput.focus();
                } else {
                    // Success State
                    showAlert('Login successful! Redirecting to dashboard...', 'success');
                    btnSubmit.innerHTML = `
                        <span class="material-symbols-outlined" style="font-size:18px;">check_circle</span>
                        <span>Success</span>
                    `;
                    btnSubmit.style.backgroundColor = '#198754';

                    // Redirect to dashboard (defaulting to / for now until dashboard exists)
                    setTimeout(() => {
                        window.location.href = result.redirect_url || '/';
                    }, 1200);
                }

            } else {
                showAlert(result.error || 'Invalid credentials. Please try again.', 'error');
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = originalBtnContent;
                btnSubmit.style.backgroundColor = '';
            }

        } catch (error) {
            console.error('Submit login error:', error);
            showAlert('Network error. Unable to connect to server.', 'error');
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = originalBtnContent;
            btnSubmit.style.backgroundColor = '';
        }
    });
});
