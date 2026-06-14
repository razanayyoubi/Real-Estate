/* ==========================================================================
   LEBESTATES ADMIN - TRANSACTIONS PAGE JAVASCRIPT
   ========================================================================== */

let currentPage = 1;
const rowsPerPage = 10;
let filteredRows = [];

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial Pagination & Filter Setup
    resetFilters();
    animateCardsOnLoad();

    // 2. Setup radio card selectors selection styles
    const typeRadios = document.querySelectorAll('input[name="transactionTypeDisplay"]');
    typeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            document.querySelectorAll('.radio-card-label').forEach(label => {
                label.classList.remove('selected');
            });
            const selectedLabel = radio.closest('.radio-card-label');
            if (selectedLabel) selectedLabel.classList.add('selected');
        });
    });
    // Trigger initial style check
    const checkedRadio = document.querySelector('input[name="transactionTypeDisplay"]:checked');
    if (checkedRadio) {
        const selectedLabel = checkedRadio.closest('.radio-card-label');
        if (selectedLabel) selectedLabel.classList.add('selected');
    }

    // 3. Setup Close modal on Escape Key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal-overlay:not(.hidden)');
            if (openModal) toggleModal(openModal.id);
        }
    });
});

/* ===== MODAL TOGGLE & LAYOUT CONTROLS ===== */
function toggleModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

function handleOverlayClick(event, modalId) {
    if (event.target.id === modalId) {
        toggleModal(modalId);
    }
}

/* ===== NEW TRANSACTION FORM HELPERS ===== */
function handlePropertyChange(selectElement) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const priceInput = document.getElementById('new-price-input');
    const radioWrapper = document.getElementById('new-type-radio-wrapper');
    const hiddenTypeInput = document.getElementById('new-type-hidden');

    if (!selectedOption || selectElement.value === "") {
        priceInput.value = "";
        priceInput.readOnly = false;
        if (radioWrapper) radioWrapper.classList.remove('locked');
        updateCommissionRatePreview();
        updateCommissionPreview();
        return;
    }

    // Auto-populate price and make read-only
    const price = selectedOption.getAttribute('data-price');
    priceInput.value = price;
    priceInput.readOnly = true;

    // Auto-select type and lock
    const type = selectedOption.getAttribute('data-type'); // Sell or Rent
    const typeVal = type === 'Rent' ? 'Rent' : 'Sell';
    
    if (hiddenTypeInput) {
        hiddenTypeInput.value = typeVal;
    }

    const targetRadio = document.querySelector(`input[name="transactionTypeDisplay"][value="${typeVal}"]`);
    if (targetRadio) {
        targetRadio.checked = true;
        // Trigger change style updates
        document.querySelectorAll('.radio-card-label').forEach(l => l.classList.remove('selected'));
        const lbl = targetRadio.closest('.radio-card-label');
        if (lbl) lbl.classList.add('selected');
    }

    if (radioWrapper) {
        radioWrapper.classList.add('locked');
    }

    updateCommissionRatePreview();
    updateCommissionPreview();
}

function handleTypeDisplayChange(radio) {
    const hiddenTypeInput = document.getElementById('new-type-hidden');
    if (hiddenTypeInput) {
        hiddenTypeInput.value = radio.value;
    }
    
    // Trigger change style updates
    document.querySelectorAll('.radio-card-label').forEach(label => {
        label.classList.remove('selected');
    });
    const selectedLabel = radio.closest('.radio-card-label');
    if (selectedLabel) selectedLabel.classList.add('selected');
    
    updateCommissionRatePreview();
    updateCommissionPreview();
}

function updateCommissionRatePreview() {
    const propSelect = document.getElementById('new-prop-select');
    const rateLabel = document.getElementById('preview-rate-label');
    const rightContainer = document.getElementById('preview-right-container');
    if (!rateLabel) return;

    if (!propSelect || propSelect.value === "") {
        rateLabel.textContent = "5";
        if (rightContainer) {
            rightContainer.style.display = 'none';
        }
        return;
    }

    const selectedOption = propSelect.options[propSelect.selectedIndex];
    const type = selectedOption.getAttribute('data-type'); // Sell or Rent

    if (type === 'Rent') {
        rateLabel.textContent = "100";
        if (rightContainer) {
            rightContainer.style.display = 'block';
            rightContainer.innerHTML = `
                <p class="preview-tag-bold text-white" style="font-size: 14px; margin-top: 10px;">1 month commission</p>
            `;
        }
    } else {
        rateLabel.textContent = "5";
        if (rightContainer) {
            rightContainer.style.display = 'block';
            rightContainer.innerHTML = `
                <p class="preview-tag text-muted" style="margin-bottom: 2px;">2.5% from owner</p>
                <p class="preview-tag-bold text-white" style="font-size: 14px; margin-top: 2px;">2.5% from buyer</p>
            `;
        }
    }
}

function updateCommissionPreview() {
    const priceInput = document.getElementById('new-price-input').value;
    const hiddenTypeInput = document.getElementById('new-type-hidden');
    if (!hiddenTypeInput) return;
    const typeVal = hiddenTypeInput.value;
    const commVal = document.getElementById('preview-commission-val');
    if (!commVal) return;

    if (!priceInput || isNaN(priceInput) || parseFloat(priceInput) <= 0) {
        commVal.textContent = "Waiting for price...";
        return;
    }

    const price = parseFloat(priceInput);
    let commission = 0;

    if (typeVal === 'Sell') {
        commission = price * 0.05; // 5%
    } else {
        commission = price; // 1 Month rent (100%)
    }

    commVal.textContent = `$${commission.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/* ===== LIVE FILTER ENGINE ===== */
function filterLedger() {
    const searchQuery = document.getElementById('search-ledger').value.toLowerCase().trim();
    const typeFilter = document.getElementById('filter-type').value;
    const paymentFilter = document.getElementById('filter-payment-status').value;
    const dateFilter = document.getElementById('filter-date').value;

    const allRows = Array.from(document.querySelectorAll('.trans-row-main'));
    filteredRows = [];

    allRows.forEach(row => {
        const rowType = row.getAttribute('data-type');
        const rowStatus = row.getAttribute('data-status');
        const rowDate = row.getAttribute('data-date'); // YYYY-MM-DD
        const searchText = row.getAttribute('data-search-text');

        const matchesSearch = !searchQuery || searchText.includes(searchQuery);
        const matchesType = (typeFilter === 'All') || (rowType === typeFilter);
        const matchesPayment = (paymentFilter === 'All') || (rowStatus === paymentFilter);
        
        let matchesDate = true;
        if (dateFilter && rowDate) {
            matchesDate = (rowDate === dateFilter);
        }

        if (matchesSearch && matchesType && matchesPayment && matchesDate) {
            filteredRows.push(row);
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });

    const clientEmptyRow = document.getElementById('client-empty-state-row');
    if (filteredRows.length === 0) {
        clientEmptyRow.style.display = '';
    } else {
        clientEmptyRow.style.display = 'none';
    }

    // Reset pagination to first page on filter change
    currentPage = 1;
    updatePagination();
}

function resetFilters() {
    document.getElementById('search-ledger').value = "";
    document.getElementById('filter-type').value = "All";
    document.getElementById('filter-payment-status').value = "All";
    document.getElementById('filter-date').value = "";
    filterLedger();
}

/* ===== CLIENT-SIDE PAGINATION ===== */
function updatePagination() {
    const totalEntries = filteredRows.length;
    const totalPages = Math.ceil(totalEntries / rowsPerPage);

    // Hide all filtered rows first
    filteredRows.forEach(row => {
        row.style.display = 'none';
    });

    // Calculate boundary indices
    const startIdx = (currentPage - 1) * rowsPerPage;
    const endIdx = Math.min(startIdx + rowsPerPage, totalEntries);

    // Show rows in page range
    for (let i = startIdx; i < endIdx; i++) {
        if (filteredRows[i]) {
            filteredRows[i].style.display = '';
        }
    }

    // Update info text
    const infoText = document.getElementById('pagination-info');
    if (totalEntries === 0) {
        infoText.textContent = "Showing 0 to 0 of 0 entries";
    } else {
        infoText.textContent = `Showing ${startIdx + 1} to ${endIdx} of ${totalEntries} entries`;
    }

    // Render Buttons
    const buttonsContainer = document.getElementById('pagination-buttons');
    buttonsContainer.innerHTML = "";

    if (totalPages <= 1) return;

    // Previous Button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'btn-page';
    prevBtn.textContent = 'Previous';
    prevBtn.disabled = (currentPage === 1);
    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            updatePagination();
        }
    };
    buttonsContainer.appendChild(prevBtn);

    // Page number buttons
    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `btn-page ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => {
            currentPage = i;
            updatePagination();
        };
        buttonsContainer.appendChild(pageBtn);
    }

    // Next Button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'btn-page';
    nextBtn.textContent = 'Next';
    nextBtn.disabled = (currentPage === totalPages);
    nextBtn.onclick = () => {
        if (currentPage < totalPages) {
            currentPage++;
            updatePagination();
        }
    };
    buttonsContainer.appendChild(nextBtn);
}

/* ===== AJAX API CALLS ===== */

// 1. Update status select dropdown change
function updateTransactionStatus(transId, selectElement) {
    const row = document.getElementById(`row-main-${transId}`);
    const originalStatus = row.getAttribute('data-status');
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
            selectElement.value = originalStatus;
            showToast('Error', data.error, 'error');
        } else {
            // Success: update classes & attributes
            row.setAttribute('data-status', newStatus);
            selectElement.className = `payment-select-dropdown status-${newStatus.replace(/\s+/g, '').toLowerCase()}`;
            showToast('Success', data.message, 'success');

            // Dynamic KPI animations
            if (data.stats) {
                animateValueUpdate('val-total-transactions', data.stats.total_transactions);
                animateValueUpdate('val-sales-transactions', data.stats.sales_transactions);
                animateValueUpdate('val-rental-transactions', data.stats.rental_transactions);
                animateValueUpdate('val-paid-transactions', data.stats.paid_transactions);
            }
        }
    })
    .catch(err => {
        selectElement.value = originalStatus;
        showToast('Error', 'Failed to update transaction status. Check connection.', 'error');
        console.error(err);
    });
}

// 2. Fetch transaction details modal contents
function loadTransactionDetails(transId) {
    fetch(`/control-panel/transactions/${transId}/details`)
    .then(res => res.json())
    .then(data => {
        if (data.error || !data.success) {
            showToast('Error', data.error || 'Failed to load details.', 'error');
        } else {
            const details = data.details;
            
            // Populate Modal Content
            document.getElementById('details-ref-id').textContent = `Ref: TRX-${details.transactionID}`;
            document.getElementById('details-prop-title').textContent = details.propertyTitle;
            document.getElementById('details-banner-img').style.backgroundImage = `url('${details.imageURL}')`;
            
            // Involved Parties
            document.getElementById('details-buyer-name').textContent = details.buyerName;
            document.getElementById('details-buyer-role').textContent = `${details.buyerRole} / Client`;
            document.getElementById('details-agent-name').textContent = details.agentName;
            document.getElementById('details-agent-role').textContent = details.agentPosition;
            document.getElementById('details-owner-name').textContent = details.ownerName;
            document.getElementById('details-owner-role').textContent = `Owner (${details.ownerEmail})`;

            // Financial Summary
            document.getElementById('details-prop-value').textContent = `$${details.finalPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            document.getElementById('details-comm-rate').textContent = `${details.commissionRate.toFixed(2)}%`;
            document.getElementById('details-comm-total').textContent = `$${details.commissionAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

            // Payment Progress Card
            document.getElementById('details-progress-text').textContent = details.progressText;
            document.getElementById('details-progress-percent').textContent = `${details.progressPercent}%`;
            document.getElementById('details-progress-bar').style.width = `${details.progressPercent}%`;

            // Payment Type and Method Details
            document.getElementById('details-payment-type').textContent = details.paymentType;
            document.getElementById('details-payment-method').textContent = details.paymentMethod;
            
            let note = `Transaction initialized on ${details.transactionDate}.`;
            if (details.paymentStatus === 'Completed') {
                note = `Transaction fully closed and paid in full. Record audited on ${details.transactionDate}.`;
                document.getElementById('details-progress-bar').style.backgroundColor = '#2e7d32';
                document.getElementById('details-progress-text').style.color = '#2e7d32';
            } else if (details.paymentStatus === 'Pending') {
                note = `Transaction value remains held in escrow pending legal deed clearances. Initialized ${details.transactionDate}.`;
                document.getElementById('details-progress-bar').style.backgroundColor = '#e65100';
                document.getElementById('details-progress-text').style.color = '#e65100';
            } else if (details.paymentStatus === 'In progress') {
                note = `Record has active holds undergoing audit or legislative checks. Initialized ${details.transactionDate}.`;
                document.getElementById('details-progress-bar').style.backgroundColor = '#0d47a1';
                document.getElementById('details-progress-text').style.color = '#0d47a1';
            } else if (details.paymentStatus === 'Cancelled') {
                note = `This transaction has been cancelled. Funds returned or holds dissolved. Date: ${details.transactionDate}.`;
                document.getElementById('details-progress-bar').style.backgroundColor = '#c62828';
                document.getElementById('details-progress-text').style.color = '#c62828';
            }
            document.getElementById('details-progress-note').textContent = note;

            // Store ID on edit button for quick navigation
            document.getElementById('details-modal').setAttribute('data-loaded-id', details.transactionID);

            // Open Modal
            toggleModal('details-modal');
        }
    })
    .catch(err => {
        showToast('Error', 'Failed to retrieve transaction details.', 'error');
        console.error(err);
    });
}

function editTransactionDetails() {
    const transId = document.getElementById('details-modal').getAttribute('data-loaded-id');
    if (transId) {
        openEditTransactionModal(transId);
    }
}

function openEditTransactionModal(transId) {
    // Hide details modal if open
    const detailsModal = document.getElementById('details-modal');
    if (detailsModal && !detailsModal.classList.contains('hidden')) {
        toggleModal('details-modal');
    }

    fetch(`/control-panel/transactions/${transId}/details`)
    .then(res => res.json())
    .then(data => {
        if (data.error || !data.success) {
            showToast('Error', data.error || 'Failed to load details.', 'error');
        } else {
            const details = data.details;
            
            // Set form action dynamically
            document.getElementById('edit-transaction-form').action = `/control-panel/transactions/${details.transactionID}/edit`;

            // Populate form fields
            document.getElementById('edit-prop-title').value = details.propertyTitle;
            document.getElementById('edit-type-display').value = details.transactionType === 'Sell' ? 'Sale' : 'Rental';
            document.getElementById('edit-price-input').value = details.finalPrice;
            
            // Select dropdowns
            document.getElementById('edit-customer-select').value = details.customerID;
            document.getElementById('edit-employee-select').value = details.employeeID;
            document.getElementById('edit-payment-type').value = details.paymentType;
            document.getElementById('edit-payment-method').value = details.paymentMethod;
            document.getElementById('edit-payment-status').value = details.paymentStatus;

            // Commission preview info
            const commVal = document.getElementById('edit-commission-val');
            if (commVal) {
                commVal.textContent = `$${details.commissionAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            }

            const rightContainer = document.getElementById('edit-right-container');
            if (rightContainer) {
                if (details.transactionType === 'Rent') {
                    rightContainer.innerHTML = `
                        <p class="preview-tag-bold text-white" style="font-size: 14px; margin-top: 10px;">1 month commission</p>
                    `;
                } else {
                    rightContainer.innerHTML = `
                        <p class="preview-tag text-muted" style="margin-bottom: 2px;">2.5% from owner</p>
                        <p class="preview-tag-bold text-white" style="font-size: 14px; margin-top: 2px;">2.5% from buyer</p>
                    `;
                }
            }

            // Open Modal
            toggleModal('edit-transaction-modal');
        }
    })
    .catch(err => {
        showToast('Error', 'Failed to retrieve transaction details.', 'error');
        console.error(err);
    });
}

/* ===== UTILITIES & ANIMS ===== */
function animateValueUpdate(elemId, newValue) {
    const elem = document.getElementById(elemId);
    if (!elem) return;

    elem.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
    elem.style.opacity = '0';
    elem.style.transform = 'scale(0.95)';

    setTimeout(() => {
        elem.textContent = typeof newValue === 'number' ? newValue.toLocaleString('en-US') : newValue;
        elem.style.opacity = '1';
        elem.style.transform = 'scale(1)';
    }, 150);
}

function showToast(title, message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastText = document.getElementById('toastText');
    const toastInner = document.getElementById('toastInner');
    const toastIcon = document.getElementById('toastIcon');

    if (!toast) return;

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
    }, 4000);
}

function animateCardsOnLoad() {
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(12px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.25, 0.8, 0.25, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 80);
    });
}
