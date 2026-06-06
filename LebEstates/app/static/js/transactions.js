/* ==========================================================================
   LEBESTATES TRANSACTIONS LEDGER CUSTOM JAVASCRIPT
   ========================================================================== */

// 1. Live Filter and Calendar Date-Range Isolation
function filterLedger() {
    const searchQuery = document.getElementById('search-ledger').value.toLowerCase().trim();
    const startDateVal = document.getElementById('date-start').value;
    const endDateVal = document.getElementById('date-end').value;
    const typeFilter = document.getElementById('filter-type').value;
    const statusFilter = document.getElementById('filter-status').value;

    const rows = document.querySelectorAll('.trans-row-main');
    let visibleCount = 0;

    rows.forEach(row => {
        // Read dataset variables pre-compiled by Jinja
        const rowType = row.getAttribute('data-type');
        const rowStatus = row.getAttribute('data-status');
        const rowDateStr = row.getAttribute('data-date'); // YYYY-MM-DD
        const searchText = row.getAttribute('data-search-text');

        // A. Search Query Match
        const matchesSearch = !searchQuery || searchText.includes(searchQuery);

        // B. Type Select Match
        const matchesType = (typeFilter === 'All') || (rowType === typeFilter);

        // C. Status Select Match
        const matchesStatus = (statusFilter === 'All') || (rowStatus === statusFilter);

        // D. Calendar Date Range Match
        let matchesDate = true;
        if (rowDateStr) {
            const rowDate = new Date(rowDateStr);
            // Reset hours to avoid timezone boundary issues
            rowDate.setHours(0,0,0,0);

            if (startDateVal) {
                const startDate = new Date(startDateVal);
                startDate.setHours(0,0,0,0);
                if (rowDate < startDate) {
                    matchesDate = false;
                }
            }

            if (endDateVal) {
                const endDate = new Date(endDateVal);
                endDate.setHours(0,0,0,0);
                if (rowDate > endDate) {
                    matchesDate = false;
                }
            }
        }

        // Hide or Show Row based on condition aggregation
        if (matchesSearch && matchesType && matchesStatus && matchesDate) {
            row.style.display = 'table-row';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Handle Empty Search Placeholder Row
    const clientEmptyRow = document.getElementById('client-empty-state-row');
    if (visibleCount === 0) {
        clientEmptyRow.style.display = 'table-row';
    } else {
        clientEmptyRow.style.display = 'none';
    }
}

// 2. Status Transition AJAX Update Trigger
function updateTransactionStatus(transId, selectElement) {
    const originalStatus = selectElement.closest('tr').getAttribute('data-status');
    const newStatus = selectElement.value;

    if (originalStatus === newStatus) return;

    fetch(`/control-panel/transactions/${transId}/update-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            // Revert dropdown state
            selectElement.value = originalStatus;
            showToast('Error', data.error, 'error');
        } else {
            // Apply new status styles and update dataset row attributes
            const row = selectElement.closest('tr');
            row.setAttribute('data-status', newStatus);

            // Rebuild class map for dropdown colors
            selectElement.className = `status-select-dropdown status-${newStatus.toLowerCase()}`;

            // Show Toast Notification
            showToast('Success', data.message, 'success');

            // Dynamically refresh KPI cards values from API metrics payload without reload
            if (data.stats) {
                animateValueUpdate('val-gross-volume', data.stats.gross_volume);
                animateValueUpdate('val-commissions', data.stats.total_commission);
                animateValueUpdate('val-escrows', data.stats.pending_escrows);
                animateValueUpdate('val-deals', data.stats.total_deals);
            }
        }
    })
    .catch(err => {
        selectElement.value = originalStatus;
        showToast('Error', 'An error occurred while updating status. Please try again.', 'error');
        console.error(err);
    });
}

// 3. Elegant Value Transition Animation Callback
function animateValueUpdate(elemId, newValue) {
    const elem = document.getElementById(elemId);
    if (!elem) return;

    // Soft fade-out / fade-in transition
    elem.style.transition = 'opacity 0.2s ease, transform 0.2s ease';
    elem.style.opacity = '0';
    elem.style.transform = 'scale(0.95)';

    setTimeout(() => {
        elem.textContent = newValue;
        elem.style.opacity = '1';
        elem.style.transform = 'scale(1)';
    }, 200);
}

// 4. Custom Toast Notification System
function showToast(title, message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastText = document.getElementById('toastText');
    const toastInner = document.getElementById('toastInner');
    const toastIcon = document.getElementById('toastIcon');

    if (!toast || !toastText || !toastInner || !toastIcon) return;

    toastText.textContent = `${title}: ${message}`;

    if (type === 'error') {
        toastInner.className = 'toast-inner error';
        toastIcon.textContent = 'error';
    } else {
        toastInner.className = 'toast-inner';
        toastIcon.textContent = 'check_circle';
    }

    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3500);
}

// 5. Bento Card Staggered Entrance Animations on Load
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(15px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 90);
    });
});
