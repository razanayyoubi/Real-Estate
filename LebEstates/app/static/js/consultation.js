

document.addEventListener('DOMContentLoaded', () => {

    /* ─────────────────────────────────────────────────────────
       1. DYNAMIC CONTROLS & INTERACTIONS (Mouse Parallax & Stats Counter)
       ───────────────────────────────────────────────────────── */

    // Mouse Parallax for Glass Panel
    document.addEventListener('mousemove', (e) => {
        const panels = document.querySelectorAll('.glass-panel');
        const x = (window.innerWidth - e.pageX * 2) / 60;
        const y = (window.innerHeight - e.pageY * 2) / 60;

        panels.forEach(panel => {
            panel.style.transform = `translate(${x}px, ${y}px)`;
        });
    });

    // Stats Counter Animation
    const statsElements = document.querySelectorAll('[data-target]');
    
    const animateValue = (element) => {
        const target = parseInt(element.getAttribute('data-target'), 10);
        const suffix = element.getAttribute('data-suffix') || '';
        const duration = 1500; // 1.5 seconds
        let startTimestamp = null;
        
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            // Ease out quad
            const ease = progress * (2 - progress);
            const current = Math.floor(ease * target);
            element.textContent = current + suffix;
            
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                element.textContent = target + suffix;
            }
        };
        
        window.requestAnimationFrame(step);
    };

    const countObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateValue(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    statsElements.forEach(el => {
        countObserver.observe(el);
    });


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

    // Toggle In Person schedule fields
    const inPersonWrapper = document.getElementById('in-person-schedule-wrapper');
    const prefDateInput = document.getElementById('pref-date');
    if (prefDateInput) {
        const todayStr = new Date().toISOString().split('T')[0];
        prefDateInput.min = todayStr;
    }

    document.querySelectorAll('input[name="contact_method"]').forEach((radio) => {
        radio.addEventListener('change', () => {
            const group = document.getElementById('err-contact-method');
            if (group) group.classList.remove('visible');
            
            if (inPersonWrapper) {
                if (radio.value === 'In Person') {
                    inPersonWrapper.style.display = 'flex';
                } else {
                    inPersonWrapper.style.display = 'none';
                }
            }
        });
    });

    // Email format validator
    const isValidEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        let valid = true;

        const isVisible = (el) => el && (el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0) && window.getComputedStyle(el).display !== 'none' && !el.closest('[style*="display: none"]');

        // Full Name
        const name = document.getElementById('full-name');
        if (isVisible(name) && (!name || !name.value.trim())) {
            showError('full-name', 'err-full-name', true);
            valid = false;
        } else {
            showError('full-name', 'err-full-name', false);
        }

        // Email
        const email = document.getElementById('email');
        if (isVisible(email) && (!email || !isValidEmail(email.value))) {
            showError('email', 'err-email', true);
            valid = false;
        } else {
            showError('email', 'err-email', false);
        }

        // Phone
        const phone = document.getElementById('phone');
        if (isVisible(phone) && (!phone || !phone.value.trim())) {
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

        // Staff Mode Customer Selection Check
        const staffHiddenId = document.getElementById('staff-selected-customer-id');
        const errStaffCust = document.getElementById('err-staff-customer');
        if (staffHiddenId) {
            if (!staffHiddenId.value) {
                if (errStaffCust) errStaffCust.classList.add('visible');
                valid = false;
            } else {
                if (errStaffCust) errStaffCust.classList.remove('visible');
            }
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

        // ── All valid: Submit to backend ──
        const submitBtn = document.getElementById('consult-submit-btn');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="material-symbols-outlined spin" style="animation: spin 1s linear infinite;">sync</span> Submitting...';
        submitBtn.disabled = true;

        const timeSlotSelect = document.getElementById('pref-time-slot');
        const timeVal = (contactMethodChosen && contactMethodChosen.value === 'In Person' && timeSlotSelect) ? timeSlotSelect.value : (document.getElementById('pref-time') ? document.getElementById('pref-time').value : '');

        const payload = {
            consult_type: consultType.value,
            contact_method: contactMethodChosen.value,
            message: document.getElementById('message').value,
            pref_date: document.getElementById('pref-date') ? document.getElementById('pref-date').value : '',
            pref_time: timeVal,
            on_behalf_customer_id: staffHiddenId ? staffHiddenId.value : ''
        };

        fetch('/consultation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;

            if (data.success) {
                form.reset();
                formCard.classList.add('submitted');
                
                // Update success message text if provided
                if (data.message && successMsg) {
                    const h3 = successMsg.querySelector('h3');
                    if (h3) h3.textContent = data.message;
                }

                // Scroll success card into view
                const top = formCard.getBoundingClientRect().top + window.scrollY - 100;
                window.scrollTo({ top, behavior: 'smooth' });
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(err => {
            console.error('Error submitting consultation:', err);
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            alert('An error occurred. Please try again.');
        });
    });

    // Staff Mode Customer Search Auto-Suggest
    const staffSearchInput = document.getElementById('staff-customer-search');
    const staffHiddenIdEl = document.getElementById('staff-selected-customer-id');
    const staffSuggestions = document.getElementById('staff-customer-suggestions');
    const staffPreview = document.getElementById('staff-customer-preview');
    const btnClearStaffCust = document.getElementById('btn-clear-staff-customer');

    if (staffSearchInput && staffSuggestions) {
        let timer = null;
        let allFetchedCustomers = [];
        let showAllCount = false;

        function renderStaffSuggestions(customers, query = '') {
            if (!customers || customers.length === 0) {
                staffSuggestions.innerHTML = '<div style="padding: 10px; font-size: 12px; color: #64748b; text-align: center;">No matching customers found</div>';
                staffSuggestions.classList.remove('hidden');
                staffSuggestions.style.display = 'block';
                return;
            }

            const limit = showAllCount ? customers.length : 5;
            const visible = customers.slice(0, limit);
            const remaining = customers.length - limit;

            let html = '';
            visible.forEach(c => {
                html += `
                    <div class="suggestion-item staff-cust-item" data-id="${c.id}" data-name="${c.name}" data-phone="${c.phone}" data-email="${c.email}" style="padding: 10px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: background 0.15s; border-bottom: 1px solid #e2e8f0; text-align: left; background: #ffffff;">
                        <div style="font-weight: 700; color: #0f172a;">${c.name}</div>
                        <div style="font-size: 11px; color: #475569;">Phone: ${c.phone || 'N/A'} • Email: ${c.email || 'N/A'}</div>
                    </div>
                `;
            });

            if (!showAllCount && remaining > 0) {
                html += `
                    <div id="btn-load-more-staff-cust" style="padding: 8px; font-size: 11px; font-weight: 700; color: #1e293b; text-align: center; cursor: pointer; background: #f1f5f9; border-radius: 6px; margin-top: 4px; border: 1px dashed #cbd5e1;">
                        Load more (${remaining} options)
                    </div>
                `;
            }

            staffSuggestions.innerHTML = html;
            staffSuggestions.classList.remove('hidden');
            staffSuggestions.style.display = 'block';

            const loadMoreBtn = staffSuggestions.querySelector('#btn-load-more-staff-cust');
            if (loadMoreBtn) {
                loadMoreBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    showAllCount = true;
                    renderStaffSuggestions(customers, query);
                });
            }

            staffSuggestions.querySelectorAll('.staff-cust-item').forEach(item => {
                item.addEventListener('mouseenter', () => item.style.background = '#f8fafc');
                item.addEventListener('mouseleave', () => item.style.background = '#ffffff');
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const id = item.dataset.id;
                    const name = item.dataset.name;
                    const phone = item.dataset.phone;

                    if (staffHiddenIdEl) staffHiddenIdEl.value = id;
                    if (staffPreview) {
                        staffPreview.querySelector('.preview-text').textContent = `Selected Customer: ${name} (${phone || 'No Phone'})`;
                        staffPreview.classList.remove('hidden');
                    }
                    staffSearchInput.classList.add('hidden');
                    staffSuggestions.classList.add('hidden');
                    staffSuggestions.style.display = 'none';
                    const err = document.getElementById('err-staff-customer');
                    if (err) err.classList.remove('visible');
                });
            });
        }

        function fetchAndShowCustomers(query = '') {
            fetch(`/api/consultation/search-customers?q=${encodeURIComponent(query)}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.customers) {
                        allFetchedCustomers = data.customers;
                        renderStaffSuggestions(allFetchedCustomers, query);
                    }
                })
                .catch(err => console.error(err));
        }

        // Show 5 initial suggestions on focus/click
        staffSearchInput.addEventListener('focus', () => {
            showAllCount = false;
            fetchAndShowCustomers(staffSearchInput.value.trim());
        });

        staffSearchInput.addEventListener('click', (e) => {
            e.stopPropagation();
            if (staffSuggestions.classList.contains('hidden')) {
                showAllCount = false;
                fetchAndShowCustomers(staffSearchInput.value.trim());
            }
        });

        // Filter while typing
        staffSearchInput.addEventListener('input', (e) => {
            const q = e.target.value.trim();
            showAllCount = false;
            clearTimeout(timer);
            timer = setTimeout(() => {
                fetchAndShowCustomers(q);
            }, 200);
        });

        if (btnClearStaffCust) {
            btnClearStaffCust.addEventListener('click', () => {
                if (staffHiddenIdEl) staffHiddenIdEl.value = '';
                if (staffSearchInput) {
                    staffSearchInput.value = '';
                    staffSearchInput.classList.remove('hidden');
                }
                if (staffPreview) staffPreview.classList.add('hidden');
                showAllCount = false;
            });
        }

        document.addEventListener('click', (e) => {
            if (staffSuggestions && !staffSearchInput.contains(e.target) && !staffSuggestions.contains(e.target)) {
                staffSuggestions.classList.add('hidden');
                staffSuggestions.style.display = 'none';
            }
        });
    }

});
