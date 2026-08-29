/* -------------------------------------------------------------
   LEBESTATES VISITS MANAGEMENT CLIENT CONTROLLER
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    console.log('LebEstates Admin UI Initialized - Visits Management');

    // 1. Dynamic Table Search, Filters & 10-Record Pagination
    let currentPage = 1;
    const pageSize = 10;
    let matchingRows = [];

    function renderPagination() {
        const pagFooter = document.querySelector('.pagination-footer');
        const rows = document.querySelectorAll('.visits-table tbody tr');
        
        const totalItems = matchingRows.length;
        const totalPages = Math.ceil(totalItems / pageSize) || 1;
        if (currentPage > totalPages) currentPage = totalPages;

        const startIdx = (currentPage - 1) * pageSize;
        const endIdx = Math.min(startIdx + pageSize, totalItems);

        rows.forEach(row => {
            if (row.id !== 'no-matching-row') row.style.display = 'none';
        });
        matchingRows.slice(startIdx, endIdx).forEach(row => row.style.display = '');

        let noMatchRow = document.getElementById('no-matching-row');
        if (totalItems === 0) {
            if (!noMatchRow) {
                noMatchRow = document.createElement('tr');
                noMatchRow.id = 'no-matching-row';
                noMatchRow.innerHTML = `
                    <td colspan="7" class="text-center" style="padding: 40px; color: var(--on-surface-variant); text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; margin-bottom: 8px; display: block;">search_off</span>
                        No visits match your search criteria.
                    </td>
                `;
                document.querySelector('.visits-table tbody').appendChild(noMatchRow);
            } else {
                noMatchRow.style.display = '';
            }
        } else {
            if (noMatchRow) noMatchRow.style.display = 'none';
        }

        if (pagFooter) {
            pagFooter.innerHTML = `
                <p class="pagination-text">Showing <span class="text-primary font-bold">${totalItems > 0 ? startIdx + 1 : 0}-${endIdx}</span> of <span class="text-primary font-bold">${totalItems}</span> visits</p>
                <div class="pagination-controls" style="display: flex; gap: 8px; align-items: center;">
                    <button class="page-btn btn-prev-page" ${currentPage === 1 ? 'disabled' : ''} style="padding: 6px 12px; cursor: pointer;">
                        <span class="material-symbols-outlined">chevron_left</span>
                    </button>
                    <span style="font-size: 0.85rem;">Page <strong>${currentPage}</strong> of <strong>${totalPages}</strong></span>
                    <button class="page-btn btn-next-page" ${currentPage >= totalPages ? 'disabled' : ''} style="padding: 6px 12px; cursor: pointer;">
                        <span class="material-symbols-outlined">chevron_right</span>
                    </button>
                </div>
            `;

            const prevBtn = pagFooter.querySelector('.btn-prev-page');
            const nextBtn = pagFooter.querySelector('.btn-next-page');
            if (prevBtn) prevBtn.onclick = () => { if (currentPage > 1) { currentPage--; renderPagination(); } };
            if (nextBtn) nextBtn.onclick = () => { if (currentPage < totalPages) { currentPage++; renderPagination(); } };
        }
    }

    function applyFilters() {
        const clientSearchInput = document.getElementById('filter-client-search');
        if (!clientSearchInput) return;
        
        const searchQuery = clientSearchInput.value.toLowerCase().trim();

        const rows = document.querySelectorAll('.visits-table tbody tr');
        matchingRows = [];

        rows.forEach(row => {
            if (row.id === 'no-matching-row') return;

            const propNameEl = row.querySelector('.property-name');
            const propIdEl = row.querySelector('.property-id');
            const custNameEl = row.querySelector('.customer-name');
            const custEmailEl = row.querySelector('.customer-email');
            const visitDateEl = row.querySelector('.visit-date');
            
            const propertyName = propNameEl ? propNameEl.textContent.toLowerCase() : '';
            const propertyId = propIdEl ? propIdEl.textContent.toLowerCase() : '';
            const customerName = custNameEl ? custNameEl.textContent.toLowerCase() : '';
            const customerEmail = custEmailEl ? custEmailEl.textContent.toLowerCase() : '';
            
            const consultantTrigger = row.querySelector('.select-trigger .selected-text');
            const consultantName = consultantTrigger ? consultantTrigger.textContent.toLowerCase() : '';

            const statusSelect = row.querySelector('.status-dropdown');
            const status = statusSelect ? statusSelect.value : '';

            const matchesSearch = 
                propertyName.includes(searchQuery) ||
                propertyId.includes(searchQuery) ||
                customerName.includes(searchQuery) ||
                customerEmail.includes(searchQuery) ||
                consultantName.includes(searchQuery) ||
                status.toLowerCase().includes(searchQuery);

            if (matchesSearch) {
                matchingRows.push(row);
            }
        });

        currentPage = 1;
        renderPagination();
    }

    // Bind filters
    const clientSearchInp = document.getElementById('filter-client-search');
    if (clientSearchInp) {
        clientSearchInp.addEventListener('input', applyFilters);
    }
    // Initial pagination setup
    applyFilters();

    // 2. Status Dropdown Inline Updates
    document.querySelectorAll('.status-dropdown').forEach(dropdown => {
        dropdown.dataset.originalStatus = dropdown.dataset.actualStatus || dropdown.value;
        
        dropdown.addEventListener('change', (e) => {
            const id = dropdown.dataset.id;
            const newStatus = dropdown.value;
            const oldDisplayStatus = dropdown.dataset.originalStatus;

            if (newStatus === 'Overdue') {
                dropdown.value = 'Overdue';
                return;
            }

            const oldStatus = dropdown.dataset.actualStatus || oldDisplayStatus;
            
            if (!confirm(`Are you sure you want to change the status of visit #${id} to ${newStatus}?`)) {
                if (dropdown.querySelector('option[value="Overdue"]') && oldStatus === 'Scheduled') {
                    dropdown.value = 'Overdue';
                } else {
                    dropdown.value = oldStatus;
                }
                return;
            }

            fetch(`/control-panel/visits/${id}/update_status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    dropdown.className = `status-dropdown status-${newStatus.toLowerCase()}`;
                    dropdown.dataset.originalStatus = newStatus;
                    dropdown.dataset.actualStatus = newStatus;
                    const overdueOpt = dropdown.querySelector('option[value="Overdue"]');
                    if (overdueOpt) overdueOpt.remove();
                    location.reload();
                } else {
                    alert(data.error || 'Failed to update status.');
                    if (dropdown.querySelector('option[value="Overdue"]') && (dropdown.dataset.actualStatus === 'Scheduled')) {
                        dropdown.value = 'Overdue';
                    } else {
                        dropdown.value = oldStatus;
                    }
                }
            })
            .catch(err => {
                console.error(err);
                alert('Network error occurred.');
                if (dropdown.querySelector('option[value="Overdue"]') && (dropdown.dataset.actualStatus === 'Scheduled')) {
                    dropdown.value = 'Overdue';
                } else {
                    dropdown.value = oldStatus;
                }
            });
        });
    });

    // 3. Searchable Consultant Inline Select Dropdown in Table
    document.querySelectorAll('.searchable-consultant-select').forEach(container => {
        const id = container.dataset.id;
        const trigger = container.querySelector('.select-trigger');
        const menu = container.querySelector('.select-dropdown-menu');
        const searchInput = container.querySelector('.dropdown-search-input');
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
                searchInput.value = '';
                filterItems(optionsList, '');
                searchInput.focus();

                // Fetch Availability check for this row's scheduled date and time
                const date = container.dataset.date;
                const time = container.dataset.time;
                if (date && time) {
                    try {
                        trigger.style.opacity = '0.5';
                        const res = await fetch(`/control-panel/visits/api/employees/availability?date=${date}&time=${time}&exclude_visit_id=${id}`);
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
        searchInput.addEventListener('input', (e) => {
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

            if (!confirm(`Are you sure you want to assign ${name} to visit #${id}?`)) {
                menu.classList.add('hidden');
                return;
            }

            fetch(`/control-panel/visits/${id}/update_consultant`, {
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

    // 4. Details Modal Interaction
    const detailsModal = document.getElementById('visit-details-modal');
    const closeBtnTop = document.getElementById('btn-close-visit-modal');
    const closeBtnBottom = document.getElementById('btn-close-visit-bottom');

    function closeDetailsModal() {
        if (detailsModal) detailsModal.classList.add('hidden');
    }

    if (closeBtnTop) closeBtnTop.addEventListener('click', closeDetailsModal);
    if (closeBtnBottom) closeBtnBottom.addEventListener('click', closeDetailsModal);
    if (detailsModal) {
        detailsModal.addEventListener('click', (e) => {
            if (e.target === detailsModal) closeDetailsModal();
        });
    }

    document.querySelectorAll('.view-details-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            
            const propName = btn.dataset.propName;
            const propId = btn.dataset.propId;
            const custName = btn.dataset.custName;
            const custEmail = btn.dataset.custEmail;
            const visitDate = btn.dataset.visitDate;
            const visitTime = btn.dataset.visitTime;
            const consultant = btn.dataset.consultant;
            const status = btn.dataset.status;
            const notes = btn.dataset.notes;

            document.getElementById('modal-prop-name').textContent = propName;
            document.getElementById('modal-prop-id').textContent = propId;
            document.getElementById('modal-cust-name').textContent = custName;
            document.getElementById('modal-cust-email').textContent = custEmail;
            document.getElementById('modal-visit-date').textContent = visitDate;
            document.getElementById('modal-visit-time').textContent = visitTime;
            document.getElementById('modal-consultant-name').textContent = consultant;
            document.getElementById('modal-visit-notes').textContent = notes;

            const badge = document.getElementById('modal-status-badge');
            if (badge) {
                badge.className = `status-badge status-${status.toLowerCase()}`;
                badge.textContent = status;
            }

            if (detailsModal) detailsModal.classList.remove('hidden');
        });
    });

    // 5. VISIT SCHEDULING / EDITING MODAL CLIENT CONTROLLER
    const scheduleModal = document.getElementById('visit-schedule-modal');
    const scheduleForm = document.getElementById('form-visit-schedule');
    const scheduleTitle = document.getElementById('visit-schedule-title');
    const scheduleVisitId = document.getElementById('schedule-visit-id');

    // Radios
    const assignOptionLater = document.getElementById('assign-option-later');
    const assignOptionNow = document.getElementById('assign-option-now');
    const assignLaterWarning = document.getElementById('assign-later-warning');
    const directAssignField = document.getElementById('direct-assign-field');

    // Fields
    const propSearch = document.getElementById('schedule-prop-search');
    const propIdHidden = document.getElementById('schedule-property-id');
    const propSuggestions = document.getElementById('schedule-prop-suggestions');
    const propPreview = document.getElementById('selected-prop-preview');

    const custSearch = document.getElementById('schedule-cust-search');
    const custIdHidden = document.getElementById('schedule-customer-id');
    const custSuggestions = document.getElementById('schedule-cust-suggestions');
    const custPreview = document.getElementById('selected-cust-preview');

    const empSearch = document.getElementById('schedule-emp-search');
    const empIdHidden = document.getElementById('schedule-employee-id');
    const empSuggestions = document.getElementById('schedule-emp-suggestions');
    const empPreview = document.getElementById('selected-emp-preview');

    const visitDateInput = document.getElementById('schedule-visit-date');
    const visitTimeInput = document.getElementById('schedule-visit-time');
    const notesInput = document.getElementById('schedule-notes');
    const statusSelectInput = document.getElementById('schedule-status');
    const statusGroupContainer = document.getElementById('status-group-container');

    // Open schedule modal
    const openScheduleBtn = document.getElementById('btn-open-schedule-visit');
    if (openScheduleBtn) {
        openScheduleBtn.addEventListener('click', () => {
            scheduleForm.reset();
            scheduleVisitId.value = '';
            scheduleTitle.textContent = 'Schedule New Visit';
            
            // Clear previews
            clearPreview(propPreview, propSearch, propIdHidden, propSuggestions);
            clearPreview(custPreview, custSearch, custIdHidden, custSuggestions);
            clearPreview(empPreview, empSearch, empIdHidden, empSuggestions);

            // Defaults
            assignOptionLater.checked = true;
            assignLaterWarning.style.display = 'flex';
            directAssignField.classList.add('hidden');
            statusGroupContainer.classList.add('hidden');

            scheduleModal.classList.remove('hidden');
        });
    }

    // Close modals
    const closeScheduleBtn = document.getElementById('btn-close-schedule-modal');
    const cancelScheduleBtn = document.getElementById('btn-cancel-schedule-modal');
    
    function hideScheduleModal() {
        if (scheduleModal) scheduleModal.classList.add('hidden');
    }
    if (closeScheduleBtn) closeScheduleBtn.addEventListener('click', hideScheduleModal);
    if (cancelScheduleBtn) cancelScheduleBtn.addEventListener('click', hideScheduleModal);

    // Radios toggling
    assignOptionLater.addEventListener('change', () => {
        assignLaterWarning.style.display = 'flex';
        directAssignField.classList.add('hidden');
        clearPreview(empPreview, empSearch, empIdHidden);
    });

    assignOptionNow.addEventListener('change', () => {
        assignLaterWarning.style.display = 'none';
        directAssignField.classList.remove('hidden');
    });

    // Property searchable autocompletion
    propSearch.addEventListener('input', debounce(async (e) => {
        const val = e.target.value.trim();
        if (val.length < 2) {
            propSuggestions.classList.add('hidden');
            return;
        }
        const res = await fetch(`/control-panel/visits/api/search-properties?q=${encodeURIComponent(val)}`);
        const items = await res.json();
        
        propSuggestions.innerHTML = '';
        if (items.length === 0) {
            propSuggestions.innerHTML = '<div class="suggestion-item">No properties found</div>';
        } else {
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.textContent = `${item.title} (${item.location}) - $${item.price.toLocaleString()}`;
                div.addEventListener('click', () => {
                    propIdHidden.value = item.id;
                    propPreview.querySelector('.text').textContent = item.title;
                    propPreview.classList.remove('hidden');
                    propSearch.classList.add('hidden');
                    propSuggestions.innerHTML = '';
                    propSuggestions.classList.add('hidden');
                    propSuggestions.style.display = 'none';
                });
                propSuggestions.appendChild(div);
            });
        }
        propSuggestions.style.display = '';
        propSuggestions.classList.remove('hidden');
    }, 300));

    propPreview.querySelector('.btn-clear').addEventListener('click', () => {
        clearPreview(propPreview, propSearch, propIdHidden, propSuggestions);
    });

    // Customer searchable autocompletion
    custSearch.addEventListener('input', debounce(async (e) => {
        const val = e.target.value.trim();
        if (val.length < 2) {
            custSuggestions.classList.add('hidden');
            return;
        }
        const res = await fetch(`/control-panel/visits/api/search-users?role=customer&q=${encodeURIComponent(val)}`);
        const items = await res.json();
        
        custSuggestions.innerHTML = '';
        if (items.length === 0) {
            custSuggestions.innerHTML = '<div class="suggestion-item">No customers found</div>';
        } else {
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.textContent = `${item.fullName} (${item.email}) - Phone: ${item.phone}`;
                div.addEventListener('click', () => {
                    custIdHidden.value = item.id;
                    custPreview.querySelector('.text').textContent = item.fullName;
                    custPreview.classList.remove('hidden');
                    custSearch.classList.add('hidden');
                    custSuggestions.innerHTML = '';
                    custSuggestions.classList.add('hidden');
                    custSuggestions.style.display = 'none';
                });
                custSuggestions.appendChild(div);
            });
        }
        custSuggestions.style.display = '';
        custSuggestions.classList.remove('hidden');
    }, 300));

    custPreview.querySelector('.btn-clear').addEventListener('click', () => {
        clearPreview(custPreview, custSearch, custIdHidden, custSuggestions);
    });

    // Employee searchable autocompletion with live availability checks
    empSearch.addEventListener('input', debounce(async (e) => {
        const val = e.target.value.trim();
        const targetDate = visitDateInput.value;
        const targetTime = visitTimeInput.value;

        if (!targetDate || !targetTime) {
            empSuggestions.innerHTML = '<div class="suggestion-item" style="color:#b78103;">Please fill in Visit Date & Time first to query consultant availability.</div>';
            empSuggestions.classList.remove('hidden');
            return;
        }

        if (val.length < 1) {
            empSuggestions.classList.add('hidden');
            return;
        }

        // Fetch users matching query
        const userRes = await fetch(`/control-panel/visits/api/search-users?role=employee&q=${encodeURIComponent(val)}`);
        const employees = await userRes.json();

        // Fetch availability status
        const visitId = scheduleVisitId.value;
        const availRes = await fetch(`/control-panel/visits/api/employees/availability?date=${targetDate}&time=${targetTime}${visitId ? '&exclude_visit_id=' + visitId : ''}`);
        const availability = await availRes.json();

        empSuggestions.innerHTML = '';
        if (employees.length === 0) {
            empSuggestions.innerHTML = '<div class="suggestion-item">No employees found</div>';
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
                        empIdHidden.value = emp.id;
                        empPreview.querySelector('.text').textContent = emp.fullName;
                        empPreview.classList.remove('hidden');
                        empSearch.classList.add('hidden');
                        empSuggestions.innerHTML = '';
                        empSuggestions.classList.add('hidden');
                        empSuggestions.style.display = 'none';
                    });
                }
                empSuggestions.appendChild(div);
            });
        }
        empSuggestions.style.display = '';
        empSuggestions.classList.remove('hidden');
    }, 300));

    empPreview.querySelector('.btn-clear').addEventListener('click', () => {
        clearPreview(empPreview, empSearch, empIdHidden, empSuggestions);
    });

    // Form submit scheduling / updates
    scheduleForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const visitId = scheduleVisitId.value;
        const propId = propIdHidden.value;
        const custId = custIdHidden.value;
        const dateVal = visitDateInput.value;
        const timeVal = visitTimeInput.value;
        const notesVal = notesInput.value;
        
        let employeeIdVal = null;
        if (assignOptionNow.checked) {
            employeeIdVal = empIdHidden.value;
            if (!employeeIdVal) {
                alert("Please select a consultant or check 'Assign Later'.");
                return;
            }
        }

        const payload = {
            property_id: propId,
            customer_id: custId,
            employee_id: employeeIdVal,
            visit_date: dateVal,
            visit_time: timeVal,
            notes: notesVal
        };

        if (visitId) {
            payload.status = statusSelectInput.value;
        }

        const endpoint = visitId ? `/control-panel/visits/${visitId}/edit` : `/control-panel/visits/create`;
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                alert(data.message || "Visit saved successfully");
                window.location.reload();
            } else {
                alert(data.error || "Failed to save visit");
            }
        } catch (err) {
            console.error(err);
            alert("Network error. Failed to save visit.");
        }
    });

    // Edit visit buttons binding
    document.querySelectorAll('.edit-visit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const id = btn.dataset.id;
            const propId = btn.dataset.propertyId;
            const propTitle = btn.dataset.propertyTitle;
            const custId = btn.dataset.customerId;
            const custName = btn.dataset.customerName;
            const empId = btn.dataset.employeeId;
            const empName = btn.dataset.employeeName;
            const date = btn.dataset.visitDate;
            const time = btn.dataset.visitTime;
            const status = btn.dataset.status;
            const notes = btn.dataset.notes;

            // Prepare edit form
            scheduleVisitId.value = id;
            scheduleTitle.textContent = `Edit Visit #${id}`;

            // Property Preview
            propIdHidden.value = propId;
            propPreview.querySelector('.text').textContent = propTitle;
            propPreview.classList.remove('hidden');
            propSearch.classList.add('hidden');

            // Customer Preview
            custIdHidden.value = custId;
            custPreview.querySelector('.text').textContent = custName;
            custPreview.classList.remove('hidden');
            custSearch.classList.add('hidden');

            // Date & Time
            visitDateInput.value = date;
            visitTimeInput.value = time;

            // Consultant Selection
            if (empId && empId !== 'None' && empId !== '') {
                assignOptionNow.checked = true;
                assignLaterWarning.style.display = 'none';
                directAssignField.classList.remove('hidden');
                
                empIdHidden.value = empId;
                empPreview.querySelector('.text').textContent = empName;
                empPreview.classList.remove('hidden');
                empSearch.classList.add('hidden');
            } else {
                assignOptionLater.checked = true;
                assignLaterWarning.style.display = 'flex';
                directAssignField.classList.add('hidden');
                clearPreview(empPreview, empSearch, empIdHidden);
            }

            // Status Editing
            statusSelectInput.value = status;
            statusGroupContainer.classList.remove('hidden');

            // Notes
            notesInput.value = notes;

            scheduleModal.classList.remove('hidden');
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
        if (!e.target.closest('#schedule-prop-search')) propSuggestions.classList.add('hidden');
        if (!e.target.closest('#schedule-cust-search')) custSuggestions.classList.add('hidden');
        if (!e.target.closest('#schedule-emp-search')) empSuggestions.classList.add('hidden');
    });
});
