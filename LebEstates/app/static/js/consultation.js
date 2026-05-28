

document.addEventListener('DOMContentLoaded', () => {

    /* ─────────────────────────────────────────────────────────
       1. NAVBAR – Hamburger menu toggle (same pattern as all pages)
    ───────────────────────────────────────────────────────── */
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            const icon = hamburger.querySelector('.material-symbols-outlined');
            icon.textContent = navMenu.classList.contains('active') ? 'close' : 'menu';
        });
    }


    /* ─────────────────────────────────────────────────────────
       2. SMOOTH SCROLL – Hero CTA → form section
    ───────────────────────────────────────────────────────── */
    const heroCta = document.getElementById('hero-cta-btn');
    const formSection = document.getElementById('consultation-form-section');

    if (heroCta && formSection) {
        heroCta.addEventListener('click', (e) => {
            e.preventDefault();
            const offset = 80; // account for sticky navbar height
            const top = formSection.getBoundingClientRect().top + window.scrollY - offset;
            window.scrollTo({ top, behavior: 'smooth' });
        });
    }


    /* ─────────────────────────────────────────────────────────
       3. FAQ ACCORDION – One open at a time
    ───────────────────────────────────────────────────────── */
    const faqItems = document.querySelectorAll('.consult-faq-item');

    faqItems.forEach((item) => {
        const question = item.querySelector('.consult-faq-question');

        question.addEventListener('click', () => {
            const isOpen = item.classList.contains('open');

            // Close all items
            faqItems.forEach((other) => {
                other.classList.remove('open');
                other.querySelector('.consult-faq-question').setAttribute('aria-expanded', 'false');
            });

            // If it wasn't open, open it now
            if (!isOpen) {
                item.classList.add('open');
                question.setAttribute('aria-expanded', 'true');
            }
        });
    });


    /* ─────────────────────────────────────────────────────────
       4. FORM VALIDATION & SUCCESS DISPLAY
    ───────────────────────────────────────────────────────── */
    const form = document.getElementById('consult-form');
    const formCard = form ? form.closest('.consult-form-card') : null;
    const successMsg = document.getElementById('consult-success-msg');

    if (!form || !formCard || !successMsg) return;

    // Helper: show / hide error message for a field
    const showError = (fieldId, errorId, show) => {
        const field = document.getElementById(fieldId);
        const error = document.getElementById(errorId);
        if (!field || !error) return;

        if (show) {
            field.classList.add('consult-input-error');
            error.classList.add('visible');
        } else {
            field.classList.remove('consult-input-error');
            error.classList.remove('visible');
        }
    };

    // Clear individual error on user interaction
    const clearErrorOnInput = (fieldId, errorId) => {
        const field = document.getElementById(fieldId);
        if (!field) return;
        const event = field.tagName === 'SELECT' ? 'change' : 'input';
        field.addEventListener(event, () => showError(fieldId, errorId, false));
    };

    clearErrorOnInput('full-name', 'err-full-name');
    clearErrorOnInput('email', 'err-email');
    clearErrorOnInput('phone', 'err-phone');
    clearErrorOnInput('consult-type', 'err-consult-type');

    // Clear contact method error when any radio is chosen
    document.querySelectorAll('input[name="contact_method"]').forEach((radio) => {
        radio.addEventListener('change', () => {
            const group = document.getElementById('err-contact-method');
            if (group) group.classList.remove('visible');
        });
    });

    // Email format validator
    const isValidEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        let valid = true;

        // Full Name
        const name = document.getElementById('full-name');
        if (!name || !name.value.trim()) {
            showError('full-name', 'err-full-name', true);
            valid = false;
        } else {
            showError('full-name', 'err-full-name', false);
        }

        // Email
        const email = document.getElementById('email');
        if (!email || !isValidEmail(email.value)) {
            showError('email', 'err-email', true);
            valid = false;
        } else {
            showError('email', 'err-email', false);
        }

        // Phone
        const phone = document.getElementById('phone');
        if (!phone || !phone.value.trim()) {
            showError('phone', 'err-phone', true);
            valid = false;
        } else {
            showError('phone', 'err-phone', false);
        }

        // Consultation Type
        const consultType = document.getElementById('consult-type');
        if (!consultType || !consultType.value) {
            showError('consult-type', 'err-consult-type', true);
            valid = false;
        } else {
            showError('consult-type', 'err-consult-type', false);
        }

        // Preferred Contact Method
        const contactMethodChosen = document.querySelector('input[name="contact_method"]:checked');
        const contactMethodError = document.getElementById('err-contact-method');
        if (!contactMethodChosen) {
            if (contactMethodError) contactMethodError.classList.add('visible');
            valid = false;
        } else {
            if (contactMethodError) contactMethodError.classList.remove('visible');
        }

        if (!valid) {
            // Scroll to the first visible error
            const firstError = form.querySelector('.consult-input-error, .consult-error-msg.visible');
            if (firstError) {
                const top = firstError.getBoundingClientRect().top + window.scrollY - 120;
                window.scrollTo({ top, behavior: 'smooth' });
            }
            return;
        }

        // ── All valid: show success state ──
        form.reset();
        formCard.classList.add('submitted');

        // Scroll success card into view
        const top = formCard.getBoundingClientRect().top + window.scrollY - 100;
        window.scrollTo({ top, behavior: 'smooth' });
    });

});
