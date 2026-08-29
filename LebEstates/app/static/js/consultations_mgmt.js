/* -------------------------------------------------------------
   LEBESTATES CONSULTATIONS MANAGEMENT CLIENT CONTROLLER
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchInput = document.getElementById('filter-client-search');
    const tableBody = document.getElementById('consultations-tbody');
    const tableRows = tableBody ? tableBody.querySelectorAll('tr[id^="consultation-row-"]') : [];

    // Modals
    const scheduleModal = document.getElementById('modal-schedule');
    const notesModal = document.getElementById('modal-notes');

    // 1. FILTER & PAGINATION FUNCTIONALITY
    let currentPage = 1;
    const pageSize = 10;
    let matchingRows = [];

    function renderPagination() {
        const pagContainer = document.getElementById('consultations-pagination');
        if (!pagContainer) return;

        const totalItems = matchingRows.length;
        const totalPages = Math.ceil(totalItems / pageSize) || 1;
        if (currentPage > totalPages) currentPage = totalPages;

        const startIdx = (currentPage - 1) * pageSize;
        const endIdx = Math.min(startIdx + pageSize, totalItems);

        // Update row displays
        tableRows.forEach(row => row.style.display = 'none');
        matchingRows.slice(startIdx, endIdx).forEach(row => row.style.display = '');

        const emptyRow = document.getElementById('empty-row');
        if (emptyRow) {
            emptyRow.style.display = totalItems === 0 ? '' : 'none';
        }

        pagContainer.innerHTML = `
            <div style="font-size: 0.85rem; color: var(--outline);">
                Showing <strong>${totalItems > 0 ? startIdx + 1 : 0}</strong> - <strong>${endIdx}</strong> of <strong>${totalItems}</strong> records
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <button type="button" class="btn-prev-page" ${currentPage === 1 ? 'disabled' : ''} style="padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: var(--surface-container); color: var(--on-surface); cursor: pointer;">
                    Previous
                </button>
                <span style="font-size: 0.85rem; padding: 0 8px;">Page <strong>${currentPage}</strong> of <strong>${totalPages}</strong></span>
                <button type="button" class="btn-next-page" ${currentPage >= totalPages ? 'disabled' : ''} style="padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); background: var(--surface-container); color: var(--on-surface); cursor: pointer;">
                    Next
                </button>
            </div>
        `;

        const prevBtn = pagContainer.querySelector('.btn-prev-page');
        const nextBtn = pagContainer.querySelector('.btn-next-page');
        if (prevBtn) prevBtn.onclick = () => { if (currentPage > 1) { currentPage--; renderPagination(); } };
        if (nextBtn) nextBtn.onclick = () => { if (currentPage < totalPages) { currentPage++; renderPagination(); } };
    }

    function applyFilters() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

        matchingRows = [];

        tableRows.forEach(row => {
            const rowSearch = row.getAttribute('data-search') || '';
            const matchesSearch = !query || rowSearch.includes(query);

            if (matchesSearch) {
                matchingRows.push(row);
            }
        });

        currentPage = 1;
        renderPagination();
    }

    if (searchInput) searchInput.addEventListener('input', applyFilters);

    // Initial render
    applyFilters();

    // 2. SEARCHABLE CONSULTANT INLINE SELECT DROPDOWN IN TABLE
    document.querySelectorAll('.searchable-consultant-select').forEach(container => {
        const id = container.dataset.id;
        const trigger = container.querySelector('.select-trigger');
        const menu = container.querySelector('.select-dropdown-menu');
        const searchInputEl = container.querySelector('.dropdown-search-input');
        const optionsList = container.querySelector('.dropdown-options-list');

        // Toggle dropdown open/close
        trigger.addEventListener('click', async (e) => {
            e.stopPropagation();
            
            // Close all other open menus
            document.querySelectorAll('.searchable-consultant-select .select-dropdown-menu').forEach(m => {
                if (m !== menu) m.classList.add('hidden');
            });

            const isHidden = menu.classList.toggle('hidden');
            if (!isHidden) {
                searchInputEl.value = '';
                filterItems(optionsList, '');
                searchInputEl.focus();

                // Fetch Availability check for this row's scheduled date and time
                const date = container.dataset.date;
                const time = container.dataset.time;
                if (date && time) {
                    try {
                        trigger.style.opacity = '0.5';
                        const res = await fetch(`/control-panel/visits/api/employees/availability?date=${date}&time=${time}&exclude_consultation_id=${id}`);
                        const availList = await res.json();
                        trigger.style.opacity = '1';

                        // Map availability to UI options list items
                        optionsList.querySelectorAll('.dropdown-option-item').forEach(optionItem => {
                            const empId = optionItem.dataset.value;
                            if (empId && empId !== 'Unassigned') {
                                const status = availList.find(x => x.id == empId);
                                if (status && status.has_conflict) {
                                    optionItem.classList.add('conflicted');
                                    optionItem.style.color = '#c5221f';
                                    optionItem.style.background = '#fce8e6';
                                    optionItem.innerHTML = `${status.fullName} <span style="font-size:10px; font-weight:700; color:#c5221f; margin-left:6px;">[Conflict]</span>`;
                                } else {
                                    optionItem.classList.remove('conflicted');
                                    optionItem.style.color = '';
                                    optionItem.style.background = '';
                                    optionItem.textContent = optionItem.dataset.name || optionItem.textContent;
                                }
                            }
                        });
                    } catch (err) {
                        console.error(err);
                        trigger.style.opacity = '1';
                    }
                }
            }
        });

        // Filter list items based on search input
        searchInputEl.addEventListener('input', (e) => {
            filterItems(optionsList, e.target.value);
        });

        // Option clicked
        optionsList.addEventListener('click', (e) => {
            const item = e.target.closest('.dropdown-option-item');
            if (!item) return;
            e.stopPropagation();

            if (item.classList.contains('conflicted')) {
                alert("This consultant is unavailable due to a scheduled appointment at this time.");
                return;
            }

            const value = item.dataset.value;
            const name = item.dataset.name || 'Unassigned';

            if (!confirm(`Are you sure you want to assign ${name} to consultation #${id}?`)) {
                menu.classList.add('hidden');
                return;
            }

            fetch(`/control-panel/consultations/${id}/update_consultant`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ employee_id: value === 'Unassigned' ? null : parseInt(value) })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Update trigger label
                    container.querySelector('.selected-text').textContent = name;
                    
                    // Update Avatar Initials
                    const avatarDiv = document.getElementById(`avatar-${id}`);
                    if (avatarDiv) {
                        if (value === 'Unassigned') {
                            avatarDiv.textContent = '--';
                        } else {
                            const names = name.trim().split(' ');
                            const initials = names.length > 1 ? (names[0][0] + names[1][0]) : names[0][0];
                            avatarDiv.textContent = initials.toUpperCase();
                        }
                    }
                    
                    // Update data-consultant on row for search filtering
                    const row = document.getElementById(`consultation-row-${id}`);
                    if (row) row.setAttribute('data-consultant', value === 'Unassigned' ? 'Unassigned' : value);

                    menu.classList.add('hidden');
                } else {
                    alert(data.error || 'Failed to assign consultant.');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Network error occurred.');
            });
        });
    });

    function filterItems(container, filterText) {
        const text = filterText.toLowerCase();
        container.querySelectorAll('.dropdown-option-item').forEach(item => {
            const label = item.textContent.toLowerCase();
            if (label.includes(text)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    // Close searchable selects if clicking outside
    document.addEventListener('click', () => {
        document.querySelectorAll('.searchable-consultant-select .select-dropdown-menu').forEach(m => {
            m.classList.add('hidden');
        });
    });

    // 3. UPDATE STATUS (AJAX)
    const statusDropdowns = document.querySelectorAll('.status-badge');
    statusDropdowns.forEach(dropdown => {
        dropdown.addEventListener('change', async (e) => {
            const id = dropdown.getAttribute('data-id');
            const status = dropdown.value;

            const row = document.getElementById(`consultation-row-${id}`);
            if (row) {
                row.setAttribute('data-status', status);
            }

            dropdown.className = `status-badge status-${status.toLowerCase()}`;

            try {
                const response = await fetch(`/control-panel/consultations/${id}/update_status`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status })
                });
                const res = await response.json();
                if (!response.ok) {
                    alert(res.error || 'Failed to update status');
                } else {
                    setTimeout(() => window.location.reload(), 300);
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Failed to update status.');
            }
        });
    });

    // 4. MODAL CONTROLS: SCHEDULE
    const scheduleButtons = document.querySelectorAll('.btn-schedule');
    scheduleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const date = btn.getAttribute('data-date');
            const time = btn.getAttribute('data-time');

            document.getElementById('schedule-consultation-id').value = id;
            document.getElementById('scheduled-date-input').value = date || '';
            document.getElementById('scheduled-time-input').value = time ? time.substring(0, 5) : '';

            if (scheduleModal) scheduleModal.classList.add('active');
        });
    });

    function closeScheduleModal() {
        if (scheduleModal) scheduleModal.classList.remove('active');
    }

    const closeScheduleBtn = document.getElementById('close-schedule-modal');
    const cancelScheduleBtn = document.getElementById('cancel-schedule-modal');
    if (closeScheduleBtn) closeScheduleBtn.addEventListener('click', closeScheduleModal);
    if (cancelScheduleBtn) cancelScheduleBtn.addEventListener('click', closeScheduleModal);

    const formSchedule = document.getElementById('form-schedule');
    if (formSchedule) {
        formSchedule.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('schedule-consultation-id').value;
            const date = document.getElementById('scheduled-date-input').value;
            const time = document.getElementById('scheduled-time-input').value;

            try {
                const response = await fetch(`/control-panel/consultations/${id}/update_schedule`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scheduled_date: date, scheduled_time: time })
                });
                const res = await response.json();
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert(res.error || 'Failed to schedule');
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Failed to schedule appointment.');
            }
        });
    }

    // 5. MODAL CONTROLS: NOTES
    const notesButtons = document.querySelectorAll('.btn-notes');
    notesButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const message = btn.getAttribute('data-message');
            const notes = btn.getAttribute('data-notes');

            document.getElementById('notes-consultation-id').value = id;
            document.getElementById('notes-customer-msg').textContent = message || '(No initial message sent)';
            document.getElementById('notes-textarea').value = notes || '';

            if (notesModal) notesModal.classList.add('active');
        });
    });

    function closeNotesModal() {
        if (notesModal) notesModal.classList.remove('active');
    }

    const closeNotesBtn = document.getElementById('close-notes-modal');
    const cancelNotesBtn = document.getElementById('cancel-notes-modal');
    if (closeNotesBtn) closeNotesBtn.addEventListener('click', closeNotesModal);
    if (cancelNotesBtn) cancelNotesBtn.addEventListener('click', closeNotesModal);

    const formNotes = document.getElementById('form-notes');
    if (formNotes) {
        formNotes.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('notes-consultation-id').value;
            const notesText = document.getElementById('notes-textarea').value;

            try {
                const response = await fetch(`/control-panel/consultations/${id}/update_notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: notesText })
                });
                const res = await response.json();
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert(res.error || 'Failed to save notes');
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Failed to update notes.');
            }
        });
    }

    // 6. PDF REPORT PRINTING
    const btnExport = document.getElementById('btn-export-pdf');
    if (btnExport) {
        btnExport.addEventListener('click', () => {
            window.print();
        });
    }

    // 7. CONSULTATION SCHEDULING / EDITING MODAL CLIENT CONTROLLER
    const consScheduleModal = document.getElementById('consultation-schedule-modal');
    const consScheduleForm = document.getElementById('form-cons-schedule');
    const consScheduleTitle = document.getElementById('cons-schedule-title');
    const consScheduleId = document.getElementById('schedule-cons-id');

    // Radios
    const consAssignOptionLater = document.getElementById('cons-assign-option-later');
    const consAssignOptionNow = document.getElementById('cons-assign-option-now');
    const consAssignLaterWarning = document.getElementById('cons-assign-later-warning');
    const consDirectAssignField = document.getElementById('cons-direct-assign-field');

    // Fields
    const consCustSearch = document.getElementById('schedule-cons-cust-search');
    const consCustIdHidden = document.getElementById('schedule-cons-customer-id');
    const consCustSuggestions = document.getElementById('schedule-cons-cust-suggestions');
    const consCustPreview = document.getElementById('selected-cons-cust-preview');

    const consEmpSearch = document.getElementById('schedule-cons-emp-search');
    const consEmpIdHidden = document.getElementById('schedule-cons-employee-id');
    const consEmpSuggestions = document.getElementById('schedule-cons-emp-suggestions');
    const consEmpPreview = document.getElementById('selected-cons-emp-preview');

    const consDateInput = document.getElementById('schedule-cons-date');
    const consTimeInput = document.getElementById('schedule-cons-time');
    const consTypeSelect = document.getElementById('schedule-cons-type');
    const consMethodSelect = document.getElementById('schedule-cons-method');
    const consMessageInput = document.getElementById('schedule-cons-message');
    const consNotesInput = document.getElementById('schedule-cons-notes');
    const consStatusSelect = document.getElementById('schedule-cons-status');
    const consStatusGroupContainer = document.getElementById('cons-status-group-container');

    // Open schedule modal
    const openConsScheduleBtn = document.getElementById('btn-open-schedule-consultation');
    if (openConsScheduleBtn) {
        openConsScheduleBtn.addEventListener('click', () => {
            consScheduleForm.reset();
            consScheduleId.value = '';
            consScheduleTitle.textContent = 'Schedule Consultation';
            
            // Clear previews
            clearPreview(consCustPreview, consCustSearch, consCustIdHidden, consCustSuggestions);
            clearPreview(consEmpPreview, consEmpSearch, consEmpIdHidden, consEmpSuggestions);

            // Defaults
            consAssignOptionLater.checked = true;
            consAssignLaterWarning.style.display = 'flex';
            consDirectAssignField.classList.add('hidden');
            consStatusGroupContainer.classList.add('hidden');

            consScheduleModal.classList.remove('hidden');
        });
    }

    // Close modals
    const closeConsBtn = document.getElementById('btn-close-cons-modal');
    const cancelConsBtn = document.getElementById('btn-cancel-cons-modal');
    
    function hideConsScheduleModal() {
        if (consScheduleModal) consScheduleModal.classList.add('hidden');
    }
    if (closeConsBtn) closeConsBtn.addEventListener('click', hideConsScheduleModal);
    if (cancelConsBtn) cancelConsBtn.addEventListener('click', hideConsScheduleModal);

    // Radios toggling
    consAssignOptionLater.addEventListener('change', () => {
        consAssignLaterWarning.style.display = 'flex';
        consDirectAssignField.classList.add('hidden');
        clearPreview(consEmpPreview, consEmpSearch, consEmpIdHidden);
    });

    consAssignOptionNow.addEventListener('change', () => {
        consAssignLaterWarning.style.display = 'none';
        consDirectAssignField.classList.remove('hidden');
    });

    // Customer searchable autocompletion
    consCustSearch.addEventListener('input', debounce(async (e) => {
        const val = e.target.value.trim();
        if (val.length < 2) {
            consCustSuggestions.classList.add('hidden');
            return;
        }
        const res = await fetch(`/control-panel/visits/api/search-users?role=customer&q=${encodeURIComponent(val)}`);
        const items = await res.json();
        
        consCustSuggestions.innerHTML = '';
        if (items.length === 0) {
            consCustSuggestions.innerHTML = '<div class="suggestion-item">No customers found</div>';
        } else {
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.textContent = `${item.fullName} (${item.email}) - Phone: ${item.phone}`;
                div.addEventListener('click', () => {
                    consCustIdHidden.value = item.id;
                    consCustPreview.querySelector('.text').textContent = item.fullName;
                    consCustPreview.classList.remove('hidden');
                    consCustSearch.classList.add('hidden');
                    consCustSuggestions.innerHTML = '';
                    consCustSuggestions.classList.add('hidden');
                    consCustSuggestions.style.display = 'none';
                });
                consCustSuggestions.appendChild(div);
            });
        }
        consCustSuggestions.style.display = '';
        consCustSuggestions.classList.remove('hidden');
    }, 300));

    consCustPreview.querySelector('.btn-clear').addEventListener('click', () => {
        clearPreview(consCustPreview, consCustSearch, consCustIdHidden, consCustSuggestions);
    });

    // Employee searchable autocompletion with live availability checks
    consEmpSearch.addEventListener('input', debounce(async (e) => {
        const val = e.target.value.trim();
        const targetDate = consDateInput.value;
        const targetTime = consTimeInput.value;

        if (!targetDate || !targetTime) {
            consEmpSuggestions.innerHTML = '<div class="suggestion-item" style="color:#b78103;">Please fill in Scheduled Date & Time first to query consultant availability.</div>';
            consEmpSuggestions.classList.remove('hidden');
            return;
        }

        if (val.length < 1) {
            consEmpSuggestions.classList.add('hidden');
            return;
        }

        // Fetch users matching query
        const userRes = await fetch(`/control-panel/visits/api/search-users?role=employee&q=${encodeURIComponent(val)}`);
        const employees = await userRes.json();

        // Fetch availability status
        const consId = consScheduleId.value;
        const availRes = await fetch(`/control-panel/visits/api/employees/availability?date=${targetDate}&time=${targetTime}${consId ? '&exclude_consultation_id=' + consId : ''}`);
        const availability = await availRes.json();

        consEmpSuggestions.innerHTML = '';
        if (employees.length === 0) {
            consEmpSuggestions.innerHTML = '<div class="suggestion-item">No employees found</div>';
        } else {
            employees.forEach(emp => {
                const avail = availability.find(x => x.id === emp.id);
                const isConflicted = avail ? avail.has_conflict : false;

                const div = document.createElement('div');
                div.className = `suggestion-item ${isConflicted ? 'conflicted' : ''}`;
                
                if (isConflicted) {
                    div.innerHTML = `<span>${emp.fullName} (${emp.email})</span> <span class="conflict-badge">Conflict</span>`;
                    div.title = avail.conflict_reason || "Not available";
                } else {
                    div.textContent = `${emp.fullName} (${emp.email})`;
                    div.addEventListener('click', () => {
                        consEmpIdHidden.value = emp.id;
                        consEmpPreview.querySelector('.text').textContent = emp.fullName;
                        consEmpPreview.classList.remove('hidden');
                        consEmpSearch.classList.add('hidden');
                        consEmpSuggestions.innerHTML = '';
                        consEmpSuggestions.classList.add('hidden');
                        consEmpSuggestions.style.display = 'none';
                    });
                }
                consEmpSuggestions.appendChild(div);
            });
        }
        consEmpSuggestions.style.display = '';
        consEmpSuggestions.classList.remove('hidden');
    }, 300));

    consEmpPreview.querySelector('.btn-clear').addEventListener('click', () => {
        clearPreview(consEmpPreview, consEmpSearch, consEmpIdHidden, consEmpSuggestions);
    });

    // Form submit scheduling / updates
    consScheduleForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const consId = consScheduleId.value;
        const custId = consCustIdHidden.value;
        const dateVal = consDateInput.value || null;
        const timeVal = consTimeInput.value || null;
        const typeVal = consTypeSelect.value;
        const methodVal = consMethodSelect.value;
        const messageVal = consMessageInput.value;
        const notesVal = consNotesInput.value;
        
        let employeeIdVal = null;
        if (consAssignOptionNow.checked) {
            employeeIdVal = consEmpIdHidden.value;
            if (!employeeIdVal) {
                alert("Please select a consultant or check 'Assign Later'.");
                return;
            }
        }

        const payload = {
            customer_id: custId,
            assigned_employee_id: employeeIdVal,
            consultation_type: typeVal,
            preferred_method: methodVal,
            message: messageVal,
            scheduled_date: dateVal,
            scheduled_time: timeVal,
            notes: notesVal
        };

        if (consId) {
            payload.status = consStatusSelect.value;
        }

        const endpoint = consId ? `/control-panel/consultations/${consId}/edit` : `/control-panel/consultations/create`;
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                alert(data.message || "Consultation saved successfully");
                window.location.reload();
            } else {
                alert(data.error || "Failed to save consultation");
            }
        } catch (err) {
            console.error(err);
            alert("Network error. Failed to save consultation.");
        }
    });

    // Edit consultation buttons binding
    document.querySelectorAll('.edit-consultation-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const id = btn.dataset.id;
            const custId = btn.dataset.customerId;
            const custName = btn.dataset.customerName;
            const empId = btn.dataset.employeeId;
            const empName = btn.dataset.employeeName;
            const date = btn.dataset.scheduledDate;
            const time = btn.dataset.scheduledTime;
            const type = btn.dataset.consultationType;
            const method = btn.dataset.preferredMethod;
            const message = btn.dataset.message;
            const status = btn.dataset.status;
            const notes = btn.dataset.notes;

            // Prepare edit form
            consScheduleId.value = id;
            consScheduleTitle.textContent = `Edit Consultation #${id}`;

            // Customer Preview
            consCustIdHidden.value = custId;
            consCustPreview.querySelector('.text').textContent = custName;
            consCustPreview.classList.remove('hidden');
            consCustSearch.classList.add('hidden');

            // Date & Time
            consDateInput.value = date || '';
            consTimeInput.value = time ? time.substring(0, 5) : '';

            // Type & Method
            consTypeSelect.value = type;
            consMethodSelect.value = method;

            // Consultant Selection
            if (empId && empId !== 'None' && empId !== '') {
                consAssignOptionNow.checked = true;
                consAssignLaterWarning.style.display = 'none';
                consDirectAssignField.classList.remove('hidden');
                
                consEmpIdHidden.value = empId;
                consEmpPreview.querySelector('.text').textContent = empName;
                consEmpPreview.classList.remove('hidden');
                consEmpSearch.classList.add('hidden');
            } else {
                consAssignOptionLater.checked = true;
                consAssignLaterWarning.style.display = 'flex';
                consDirectAssignField.classList.add('hidden');
                clearPreview(consEmpPreview, consEmpSearch, consEmpIdHidden);
            }

            // Message & Notes
            consMessageInput.value = message || '';
            consNotesInput.value = notes || '';

            // Status Editing
            consStatusSelect.value = status;
            consStatusGroupContainer.classList.remove('hidden');

            consScheduleModal.classList.remove('hidden');
        });
    });

    // Helper functions
    function clearPreview(previewEl, searchEl, hiddenEl, suggestionsEl) {
        hiddenEl.value = '';
        searchEl.value = '';
        searchEl.classList.remove('hidden');
        previewEl.classList.add('hidden');
        if (suggestionsEl) {
            suggestionsEl.innerHTML = '';
            suggestionsEl.classList.add('hidden');
            suggestionsEl.style.display = 'none';
        }
    }

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#schedule-cons-cust-search')) consCustSuggestions.classList.add('hidden');
        if (!e.target.closest('#schedule-cons-emp-search')) consEmpSuggestions.classList.add('hidden');
    });
});
