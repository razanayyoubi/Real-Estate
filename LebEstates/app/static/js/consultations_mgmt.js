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
                // Position fixed over table so card is 100% visible and not clipped
                const rect = trigger.getBoundingClientRect();
                menu.style.position = 'fixed';
                menu.style.zIndex = '999999';
                menu.style.width = '230px';

                const menuHeight = 220;
                let top = rect.top - menuHeight - 6;
                if (top < 10) {
                    top = rect.bottom + 6;
                }
                let left = rect.left;
                if (left + 230 > window.innerWidth - 16) {
                    left = window.innerWidth - 246;
                }

                menu.style.top = top + 'px';
                menu.style.left = left + 'px';

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

    function filterItems(container, filterText, showAll = false) {
        const text = filterText.toLowerCase();
        const allItems = Array.from(container.querySelectorAll('.dropdown-option-item'));
        
        let matching = allItems.filter(item => {
            const label = item.textContent.toLowerCase();
            return label.includes(text);
        });

        // Hide all options first
        allItems.forEach(item => item.style.display = 'none');

        // Limit visible items to 4 unless showAll is true
        const visibleItems = showAll ? matching : matching.slice(0, 4);
        visibleItems.forEach(item => item.style.display = 'block');

        // Manage "View More" button
        let viewMoreBtn = container.querySelector('.btn-view-more-options');
        if (!viewMoreBtn) {
            viewMoreBtn = document.createElement('div');
            viewMoreBtn.className = 'btn-view-more-options';
            viewMoreBtn.style.cssText = 'padding: 6px; font-size: 11px; font-weight: 700; color: var(--primary); text-align: center; cursor: pointer; background: var(--surface-container-low); border-radius: 4px; margin-top: 4px; border: 1px dashed var(--outline-variant);';
            container.appendChild(viewMoreBtn);
        }

        const remaining = matching.length - 4;
        if (!showAll && remaining > 0) {
            viewMoreBtn.style.display = 'block';
            viewMoreBtn.textContent = `View more (${remaining} options)`;
            viewMoreBtn.onclick = (e) => {
                e.stopPropagation();
                filterItems(container, filterText, true);
            };
        } else {
            viewMoreBtn.style.display = 'none';
        }
    }

    // Close searchable selects if clicking outside
    document.addEventListener('click', () => {
        document.querySelectorAll('.searchable-consultant-select .select-dropdown-menu').forEach(m => {
            m.classList.add('hidden');
        });
    });

    // Helper functions for modal open/close
    function openModalEl(el) {
        if (!el) return;
        el.classList.remove('hidden');
        el.classList.add('active');
        el.style.display = 'flex';
    }

    function closeModalEl(el) {
        if (!el) return;
        el.classList.remove('active');
        el.classList.add('hidden');
        el.style.display = 'none';
    }

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
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-schedule');
        if (btn) {
            const id = btn.getAttribute('data-id');
            const date = btn.getAttribute('data-date');
            const time = btn.getAttribute('data-time');

            document.getElementById('schedule-consultation-id').value = id;
            document.getElementById('scheduled-date-input').value = date || '';
            document.getElementById('scheduled-time-input').value = time ? time.substring(0, 5) : '';

            openModalEl(scheduleModal);
        }
    });

    const closeScheduleBtn = document.getElementById('close-schedule-modal');
    const cancelScheduleBtn = document.getElementById('cancel-schedule-modal');
    if (closeScheduleBtn) closeScheduleBtn.addEventListener('click', () => closeModalEl(scheduleModal));
    if (cancelScheduleBtn) cancelScheduleBtn.addEventListener('click', () => closeModalEl(scheduleModal));

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
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-notes');
        if (btn) {
            const id = btn.getAttribute('data-id');
            const message = btn.getAttribute('data-message');
            const notes = btn.getAttribute('data-notes');

            document.getElementById('notes-consultation-id').value = id;
            document.getElementById('notes-customer-msg').textContent = message || '(No initial message sent)';
            document.getElementById('notes-textarea').value = notes || '';

            openModalEl(notesModal);
        }
    });

    const closeNotesBtn = document.getElementById('close-notes-modal');
    const cancelNotesBtn = document.getElementById('cancel-notes-modal');
    if (closeNotesBtn) closeNotesBtn.addEventListener('click', () => closeModalEl(notesModal));
    if (cancelNotesBtn) cancelNotesBtn.addEventListener('click', () => closeModalEl(notesModal));

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

    // Open schedule modal (Add Consultation)
    const openConsScheduleBtn = document.getElementById('btn-open-schedule-consultation');
    if (openConsScheduleBtn) {
        openConsScheduleBtn.addEventListener('click', () => {
            if (consScheduleForm) consScheduleForm.reset();
            if (consScheduleId) consScheduleId.value = '';
            if (consScheduleTitle) consScheduleTitle.textContent = 'Schedule Consultation';
            
            // Clear previews
            clearPreview(consCustPreview, consCustSearch, consCustIdHidden, consCustSuggestions);
            clearPreview(consEmpPreview, consEmpSearch, consEmpIdHidden, consEmpSuggestions);

            // Defaults
            if (consAssignOptionLater) consAssignOptionLater.checked = true;
            if (consAssignLaterWarning) consAssignLaterWarning.style.display = 'flex';
            if (consDirectAssignField) consDirectAssignField.classList.add('hidden');
            if (consStatusGroupContainer) consStatusGroupContainer.classList.add('hidden');

            openModalEl(consScheduleModal);
        });
    }

    // Edit consultation button handler
    document.addEventListener('click', (e) => {
        const editBtn = e.target.closest('.edit-consultation-btn');
        if (editBtn) {
            const id = editBtn.getAttribute('data-id');
            const custId = editBtn.getAttribute('data-customer-id');
            const custName = editBtn.getAttribute('data-customer-name');
            const empId = editBtn.getAttribute('data-employee-id');
            const empName = editBtn.getAttribute('data-employee-name');
            const type = editBtn.getAttribute('data-consultation-type');
            const method = editBtn.getAttribute('data-preferred-method');
            const message = editBtn.getAttribute('data-message');
            const scheduledDate = editBtn.getAttribute('data-scheduled-date');
            const scheduledTime = editBtn.getAttribute('data-scheduled-time');
            const status = editBtn.getAttribute('data-status');
            const notes = editBtn.getAttribute('data-notes');

            if (consScheduleForm) consScheduleForm.reset();
            if (consScheduleId) consScheduleId.value = id;
            if (consScheduleTitle) consScheduleTitle.textContent = `Edit Consultation #${id}`;

            // Set Customer
            if (consCustIdHidden) consCustIdHidden.value = custId || '';
            if (consCustSearch) consCustSearch.value = custName || '';
            if (consCustPreview && custName) {
                const textEl = consCustPreview.querySelector('.text');
                if (textEl) textEl.textContent = custName;
                consCustPreview.classList.remove('hidden');
                if (consCustSearch) consCustSearch.classList.add('hidden');
            }

            // Set Employee
            if (empId && empId !== 'None' && empId !== 'Unassigned') {
                if (consAssignOptionNow) consAssignOptionNow.checked = true;
                if (consAssignLaterWarning) consAssignLaterWarning.style.display = 'none';
                if (consDirectAssignField) consDirectAssignField.classList.remove('hidden');
                if (consEmpIdHidden) consEmpIdHidden.value = empId;
                if (consEmpSearch) consEmpSearch.value = empName || '';
                if (consEmpPreview && empName) {
                    const textEl = consEmpPreview.querySelector('.text');
                    if (textEl) textEl.textContent = empName;
                    consEmpPreview.classList.remove('hidden');
                    if (consEmpSearch) consEmpSearch.classList.add('hidden');
                }
            } else {
                if (consAssignOptionLater) consAssignOptionLater.checked = true;
                if (consAssignLaterWarning) consAssignLaterWarning.style.display = 'flex';
                if (consDirectAssignField) consDirectAssignField.classList.add('hidden');
            }

            if (consTypeSelect) consTypeSelect.value = type || 'Other';
            if (consMethodSelect) consMethodSelect.value = method || 'Phone';
            if (consDateInput) consDateInput.value = scheduledDate || '';
            if (consTimeInput) consTimeInput.value = scheduledTime || '';
            if (consMessageInput) consMessageInput.value = message || '';
            if (consNotesInput) consNotesInput.value = notes || '';
            if (consStatusSelect) consStatusSelect.value = status || 'Pending';
            if (consStatusGroupContainer) consStatusGroupContainer.classList.remove('hidden');

            openModalEl(consScheduleModal);
        }
    });

    // Close modals
    const closeConsBtn = document.getElementById('btn-close-cons-modal');
    const cancelConsBtn = document.getElementById('btn-cancel-cons-modal');
    
    if (closeConsBtn) closeConsBtn.addEventListener('click', () => closeModalEl(consScheduleModal));
    if (cancelConsBtn) cancelConsBtn.addEventListener('click', () => closeModalEl(consScheduleModal));

    // Global Hover Popover Portal
    (function() {
        let portal = document.getElementById('globalPopoverPortal');
        if (!portal) {
            portal = document.createElement('div');
            portal.id = 'globalPopoverPortal';
            portal.className = 'global-popover-portal';
            document.body.appendChild(portal);
        }

        let hideTimeout = null;

        document.addEventListener('mouseover', function(e) {
            const triggerCell = e.target.closest('.popover-trigger-cell');
            if (!triggerCell) return;

            const template = triggerCell.querySelector('.popover-template');
            if (!template) return;

            clearTimeout(hideTimeout);

            portal.innerHTML = template.innerHTML;

            const rect = triggerCell.getBoundingClientRect();
            const portalWidth = 320;

            portal.style.display = 'block';
            portal.style.visibility = 'hidden';
            
            let left = rect.left;
            if (left + portalWidth > window.innerWidth - 16) {
                left = window.innerWidth - portalWidth - 16;
            }
            left = Math.max(16, left);

            const portalHeight = portal.offsetHeight || 220;

            let top = rect.top - portalHeight - 8;
            if (top < 12) {
                top = rect.bottom + 8;
            }

            portal.style.top = top + 'px';
            portal.style.left = left + 'px';
            portal.style.visibility = 'visible';
            portal.classList.add('active');
        });

        document.addEventListener('mouseout', function(e) {
            const triggerCell = e.target.closest('.popover-trigger-cell');
            if (triggerCell) {
                const related = e.relatedTarget;
                if (related && (triggerCell.contains(related) || portal.contains(related))) {
                    return;
                }
                hideTimeout = setTimeout(() => {
                    portal.classList.remove('active');
                }, 150);
            }
        });

        portal.addEventListener('mouseenter', function() {
            clearTimeout(hideTimeout);
        });

        portal.addEventListener('mouseleave', function() {
            hideTimeout = setTimeout(() => {
                portal.classList.remove('active');
            }, 150);
        });
    })();

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

    // Hide suggestions & menus when clicking or scrolling outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#schedule-cons-cust-search') && consCustSuggestions) consCustSuggestions.classList.add('hidden');
        if (!e.target.closest('#schedule-cons-emp-search') && consEmpSuggestions) consEmpSuggestions.classList.add('hidden');
    });

    window.addEventListener('scroll', () => {
        document.querySelectorAll('.searchable-consultant-select .select-dropdown-menu').forEach(m => m.classList.add('hidden'));
    }, true);
});
