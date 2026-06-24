document.addEventListener('DOMContentLoaded', () => {
    console.log('LebEstates Admin UI Initialized - Visits Management');

    // 1. Dynamic Table Search and Filters
    function applyFilters() {
        const searchInput = document.getElementById('search-visits');
        if (!searchInput) return; // guard against element not loaded
        
        const searchQuery = searchInput.value.toLowerCase().trim();
        const statusFilter = document.getElementById('filter-status').value;
        const consultantFilter = document.getElementById('filter-consultant').value;
        const timeFilter = document.getElementById('filter-time').value;

        const rows = document.querySelectorAll('.visits-table tbody tr');
        let visibleCount = 0;

        rows.forEach(row => {
            if (row.id === 'no-matching-row') return;

            // Extract values
            const propNameEl = row.querySelector('.property-name');
            const propIdEl = row.querySelector('.property-id');
            const custNameEl = row.querySelector('.customer-name');
            const custEmailEl = row.querySelector('.customer-email');
            const visitDateEl = row.querySelector('.visit-date');
            
            const propertyName = propNameEl ? propNameEl.textContent.toLowerCase() : '';
            const propertyId = propIdEl ? propIdEl.textContent.toLowerCase() : '';
            const customerName = custNameEl ? custNameEl.textContent.toLowerCase() : '';
            const customerEmail = custEmailEl ? custEmailEl.textContent.toLowerCase() : '';
            
            const consultantSelect = row.querySelector('.consultant-dropdown');
            const consultantId = consultantSelect ? consultantSelect.value : '';
            const selectedOption = consultantSelect ? consultantSelect.options[consultantSelect.selectedIndex] : null;
            const consultantName = selectedOption ? (selectedOption.dataset.name || selectedOption.text).toLowerCase() : '';

            const statusSelect = row.querySelector('.status-dropdown');
            const status = statusSelect ? statusSelect.value : '';

            const visitDateText = visitDateEl ? visitDateEl.textContent.trim() : '';

            // Match query
            const matchesSearch = 
                propertyName.includes(searchQuery) ||
                propertyId.includes(searchQuery) ||
                customerName.includes(searchQuery) ||
                customerEmail.includes(searchQuery) ||
                consultantName.includes(searchQuery) ||
                status.toLowerCase().includes(searchQuery);

            // Match Status
            const matchesStatus = (statusFilter === 'All' || status === statusFilter);

            // Match Consultant
            const matchesConsultant = (consultantFilter === 'All' || consultantId === consultantFilter);

            // Match Time range
            let matchesTime = true;
            if (timeFilter !== 'All') {
                const visitDateObj = new Date(visitDateText);
                const today = new Date();
                today.setHours(0,0,0,0);

                if (timeFilter === 'Today') {
                    matchesTime = visitDateObj.toDateString() === today.toDateString();
                } else if (timeFilter === 'ThisWeek') {
                    const oneWeekAgo = new Date(today);
                    oneWeekAgo.setDate(today.getDate() - 7);
                    const oneWeekAhead = new Date(today);
                    oneWeekAhead.setDate(today.getDate() + 7);
                    matchesTime = visitDateObj >= oneWeekAgo && visitDateObj <= oneWeekAhead;
                } else if (timeFilter === 'ThisMonth') {
                    matchesTime = visitDateObj.getMonth() === today.getMonth() && visitDateObj.getFullYear() === today.getFullYear();
                }
            }

            if (matchesSearch && matchesStatus && matchesConsultant && matchesTime) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Toggle "No matches" row
        let noMatchRow = document.getElementById('no-matching-row');
        if (visibleCount === 0) {
            if (!noMatchRow) {
                noMatchRow = document.createElement('tr');
                noMatchRow.id = 'no-matching-row';
                noMatchRow.innerHTML = `
                    <td colspan="6" class="text-center" style="padding: 40px; color: var(--on-surface-variant); text-align: center;">
                        <span class="material-symbols-outlined" style="font-size: 48px; margin-bottom: 8px; display: block;">search_off</span>
                        No visits match your search criteria.
                    </td>
                `;
                document.querySelector('.visits-table tbody').appendChild(noMatchRow);
            } else {
                noMatchRow.style.display = '';
            }
        } else {
            if (noMatchRow) {
                noMatchRow.style.display = 'none';
            }
        }

        // Update showing text
        const pagText = document.querySelector('.pagination-text');
        if (pagText) {
            const totalRowsCount = rows.length - (document.getElementById('no-matching-row') ? 1 : 0);
            pagText.innerHTML = `Showing <span class="text-primary font-bold">${visibleCount}</span> of <span class="text-primary font-bold">${totalRowsCount}</span> visits`;
        }
    }

    // Bind filters
    const searchInp = document.getElementById('search-visits');
    const statusFlt = document.getElementById('filter-status');
    const consultantFlt = document.getElementById('filter-consultant');
    const timeFlt = document.getElementById('filter-time');

    if (searchInp) searchInp.addEventListener('input', applyFilters);
    if (statusFlt) statusFlt.addEventListener('change', applyFilters);
    if (consultantFlt) consultantFlt.addEventListener('change', applyFilters);
    if (timeFlt) timeFlt.addEventListener('change', applyFilters);

    // 2. Status Dropdown Inline Updates
    document.querySelectorAll('.status-dropdown').forEach(dropdown => {
        // For overdue visits the current value is 'Overdue'; store the real DB status
        dropdown.dataset.originalStatus = dropdown.dataset.actualStatus || dropdown.value;
        
        dropdown.addEventListener('change', (e) => {
            const id = dropdown.dataset.id;
            const newStatus = dropdown.value;
            const oldDisplayStatus = dropdown.dataset.originalStatus;

            // If user selects 'Overdue' (display-only option), revert without calling API
            if (newStatus === 'Overdue') {
                dropdown.value = 'Overdue';
                return;
            }

            // The actual status to restore on cancel/error is what's in DB
            const oldStatus = dropdown.dataset.actualStatus || oldDisplayStatus;
            
            if (!confirm(`Are you sure you want to change the status of visit #${id} to ${newStatus}?`)) {
                // Restore previous display
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
                    // Remove the 'Overdue' option if it was there (no longer overdue after update)
                    const overdueOpt = dropdown.querySelector('option[value="Overdue"]');
                    if (overdueOpt) overdueOpt.remove();
                    // Reload to update stats cards and note entries
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

    // 3. Consultant Dropdown Inline Updates
    document.querySelectorAll('.consultant-dropdown').forEach(dropdown => {
        dropdown.dataset.originalConsultant = dropdown.value;
        
        dropdown.addEventListener('change', (e) => {
            const id = dropdown.dataset.id;
            const newConsultantId = dropdown.value;
            const oldConsultantId = dropdown.dataset.originalConsultant;
            
            const selectedOption = dropdown.options[dropdown.selectedIndex];
            const fullName = selectedOption.dataset.name || selectedOption.text;
            
            if (!confirm(`Are you sure you want to assign ${fullName} to visit #${id}?`)) {
                dropdown.value = oldConsultantId;
                return;
            }

            fetch(`/control-panel/visits/${id}/update_consultant`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ employee_id: newConsultantId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    dropdown.dataset.originalConsultant = newConsultantId;
                    
                    // Update initials avatar dynamically
                    const avatarDiv = document.getElementById(`avatar-${id}`);
                    if (avatarDiv) {
                        const names = fullName.trim().split(' ');
                        const initials = names.length > 1 ? (names[0][0] + names[1][0]) : names[0][0];
                        avatarDiv.textContent = initials.toUpperCase();
                    }
                } else {
                    alert(data.error || 'Failed to assign consultant.');
                    dropdown.value = oldConsultantId;
                }
            })
            .catch(err => {
                console.error(err);
                alert('Network error occurred.');
                dropdown.value = oldConsultantId;
            });
        });
    });

    // 4. Export PDF Button Event
    const exportBtn = document.querySelector('.btn-export');
    if (exportBtn) {
        exportBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.print();
        });
    }

    // 5. Details Modal Interaction
    const modal = document.getElementById('visit-details-modal');
    const closeBtnTop = document.getElementById('btn-close-visit-modal');
    const closeBtnBottom = document.getElementById('btn-close-visit-bottom');

    function closeModal() {
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    if (closeBtnTop) closeBtnTop.addEventListener('click', closeModal);
    if (closeBtnBottom) closeBtnBottom.addEventListener('click', closeModal);
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    document.querySelectorAll('.view-details-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Read data attributes
            const propName = btn.dataset.propName;
            const propId = btn.dataset.propId;
            const custName = btn.dataset.custName;
            const custEmail = btn.dataset.custEmail;
            const visitDate = btn.dataset.visitDate;
            const visitTime = btn.dataset.visitTime;
            const consultant = btn.dataset.consultant;
            const status = btn.dataset.status;
            const notes = btn.dataset.notes;

            // Populate elements
            document.getElementById('modal-prop-name').textContent = propName;
            document.getElementById('modal-prop-id').textContent = propId;
            document.getElementById('modal-cust-name').textContent = custName;
            document.getElementById('modal-cust-email').textContent = custEmail;
            document.getElementById('modal-visit-date').textContent = visitDate;
            document.getElementById('modal-visit-time').textContent = visitTime;
            document.getElementById('modal-consultant-name').textContent = consultant;
            document.getElementById('modal-visit-notes').textContent = notes;

            // Update badge classes
            const badge = document.getElementById('modal-status-badge');
            if (badge) {
                badge.className = `status-badge status-${status.toLowerCase()}`;
                badge.textContent = status;
            }

            // Show modal
            if (modal) {
                modal.classList.remove('hidden');
            }
        });
    });
});

