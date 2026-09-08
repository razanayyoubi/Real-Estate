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

    // Attach client search listener
    const clientSearchInput = document.getElementById('filter-client-search');
    if (clientSearchInput) {
        clientSearchInput.addEventListener('input', () => {
            filterLedger();
        });
    }

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

    // 4. Auto-open modal if query string dictates
    if (window.location.search.includes('open_new=true')) {
        toggleModal('new-transaction-modal');
    }

    // 5. Initialize Report Customer Tags UI
    updateReportCustomerTagsUI();

    // 6. Outside click handler to close dropdowns
    document.addEventListener('click', (e) => {
        const propWrapper = document.getElementById('new-property-autocomplete-wrapper');
        if (propWrapper && !propWrapper.contains(e.target)) {
            const box = document.getElementById('new-property-suggestions-box');
            if (box) { box.classList.add('hidden'); box.style.display = 'none'; }
        }
        const clientWrapper = document.getElementById('new-client-autocomplete-wrapper');
        if (clientWrapper && !clientWrapper.contains(e.target)) {
            const box = document.getElementById('new-client-suggestions-box');
            if (box) { box.classList.add('hidden'); box.style.display = 'none'; }
        }
        const reportCustWrapper = document.getElementById('report-customer-autocomplete-wrapper');
        if (reportCustWrapper && !reportCustWrapper.contains(e.target)) {
            const box = document.getElementById('report-customer-suggestions-box');
            if (box) { box.classList.add('hidden'); box.style.display = 'none'; }
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

/* ===== LIVE FILTER & PAGINATION ENGINE ===== */
function filterLedger() {
    const searchInput = document.getElementById('filter-client-search') || document.getElementById('search-ledger');
    const searchQuery = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    const typeSelect = document.querySelector('select[name="type"]') || document.getElementById('filter-type');
    const typeFilter = typeSelect ? typeSelect.value : 'All';
    
    const statusSelect = document.querySelector('select[name="status"]') || document.getElementById('filter-payment-status');
    const paymentFilter = statusSelect ? statusSelect.value : 'All';

    const allRows = Array.from(document.querySelectorAll('.trans-row-main'));
    filteredRows = [];

    allRows.forEach(row => {
        const rowType = row.getAttribute('data-type');
        const rowStatus = row.getAttribute('data-status');
        const searchText = (row.getAttribute('data-search-text') || '').toLowerCase();

        const matchesSearch = !searchQuery || searchText.includes(searchQuery);
        const matchesType = (typeFilter === 'All') || (rowType === typeFilter);
        const matchesPayment = (paymentFilter === 'All') || (rowStatus === paymentFilter);

        if (matchesSearch && matchesType && matchesPayment) {
            filteredRows.push(row);
        } else {
            row.style.display = 'none';
        }
    });

    const clientEmptyRow = document.getElementById('client-empty-state-row');
    if (clientEmptyRow) {
        if (filteredRows.length === 0 && allRows.length > 0) {
            clientEmptyRow.style.display = '';
        } else {
            clientEmptyRow.style.display = 'none';
        }
    }

    currentPage = 1;
    updatePagination();
}

function resetFilters() {
    const clientInput = document.getElementById('filter-client-search');
    if (clientInput) clientInput.value = "";
    const serverInput = document.getElementById('filter-server-search');
    if (serverInput) serverInput.value = "";
    
    filterLedger();
}

/* ===== CLIENT & AJAX PAGINATION ===== */
function updatePagination() {
    const totalEntries = filteredRows.length;
    const totalPages = Math.max(1, Math.ceil(totalEntries / rowsPerPage));

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
    if (infoText) {
        if (totalEntries === 0) {
            infoText.textContent = "Showing 0 to 0 of 0 entries";
        } else {
            infoText.textContent = `Showing ${startIdx + 1} to ${endIdx} of ${totalEntries} entries`;
        }
    }

    // Render Buttons
    const buttonsContainer = document.getElementById('pagination-buttons');
    if (!buttonsContainer) return;
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

// Function to fetch and reload ledger data via AJAX offset
function loadTransactionsPageAjax(page = 1) {
    const q = (document.getElementById('filter-server-search')?.value || '').trim();
    const typeSelect = document.querySelector('select[name="type"]');
    const type = typeSelect ? typeSelect.value : 'All';
    const statusSelect = document.querySelector('select[name="status"]');
    const status = statusSelect ? statusSelect.value : 'All';

    const params = new URLSearchParams({
        page: page,
        per_page: rowsPerPage,
        server_q: q,
        type: type,
        status: status
    });

    fetch(`/control-panel/transactions/ledger/data?${params.toString()}`)
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            renderTransactionsTbody(data.transactions);
            currentPage = page;
            renderAjaxPaginationButtons(data.total_count, page, rowsPerPage);
            if (data.stats) {
                animateValueUpdate('val-total-transactions', data.stats.total_transactions);
                animateValueUpdate('val-sales-transactions', data.stats.sales_transactions);
                animateValueUpdate('val-rental-transactions', data.stats.rental_transactions);
                animateValueUpdate('val-paid-transactions', data.stats.paid_transactions);
            }
        }
    })
    .catch(err => console.error('Error fetching transactions via AJAX:', err));
}

function renderTransactionsTbody(transactions) {
    const tbody = document.getElementById('ledger-table-body');
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `
            <tr class="no-records-row">
                <td colspan="7" class="no-records-cell">
                    <span class="material-symbols-outlined">info</span>
                    <p>No transaction records found.</p>
                </td>
            </tr>
        `;
        filteredRows = [];
        return;
    }

    let html = '';
    transactions.forEach(t => {
        const isSell = t.transactionType === 'Sell';
        const typeLabel = isSell ? 'Sale' : 'Rent';
        const badgeClass = isSell ? 'badge-sold' : 'badge-rented';
        const badgeText = isSell ? 'Sold' : 'Rented';
        const statusClass = `status-${t.statusDisplay.replace(/\s+/g, '').toLowerCase()}`;

        html += `
            <tr class="trans-row-main" id="row-main-${t.transactionID}"
                data-id="${t.transactionID}"
                data-type="${t.transactionType}"
                data-status="${t.statusDisplay}"
                data-date="${t.date}"
                data-search-text="trx-${t.transactionID} ${t.property.title.toLowerCase()} ${t.property.location.toLowerCase()} ${t.customer.name.toLowerCase()} ${t.employee.name.toLowerCase()}">
                
                <td class="td-id" data-label="ID">TRX-${t.transactionID}</td>
                
                <td class="td-property" data-label="Property">
                    <div class="property-cell-wrapper">
                        <div class="property-image-box">
                            <img src="${t.property.image}" alt="Property Thumbnail" loading="lazy">
                        </div>
                        <div class="property-info-box">
                            <p class="property-title-text">${t.property.title}</p>
                            <p class="property-meta-text">${typeLabel} • ${t.property.location}</p>
                        </div>
                    </div>
                </td>

                <td class="td-stakeholders" data-label="Stakeholders">
                    <div class="stakeholders-cell-box">
                        <span class="client-name-text">${t.customer.name}</span>
                        <span class="agent-name-text">Agent: ${t.employee.name}</span>
                    </div>
                </td>

                <td class="td-value text-right" data-label="Value">
                    <div class="value-cell-box">
                        <span class="value-price-text">$${t.finalPrice.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}${isSell ? '' : ' /mo'}</span>
                        <span class="value-comm-text">Comm: $${t.commissionAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                    </div>
                </td>

                <td class="td-status text-center" data-label="Status">
                    <span class="badge ${badgeClass}">${badgeText}</span>
                </td>

                <td class="td-payment text-center" data-label="Payment">
                    <select class="payment-select-dropdown ${statusClass}" onchange="updateTransactionStatus(${t.transactionID}, this)">
                        <option value="Pending" ${t.paymentStatus === 'Escrow' ? 'selected' : ''}>Pending</option>
                        <option value="In progress" ${t.paymentStatus === 'Legal' ? 'selected' : ''}>In progress</option>
                        <option value="Completed" ${t.paymentStatus === 'Closed' ? 'selected' : ''}>Completed</option>
                        <option value="Cancelled" ${t.paymentStatus === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                    </select>
                </td>

                <td class="td-actions text-center" data-label="Actions">
                    <div class="actions-cell-wrapper">
                        <button class="btn btn-icon btn-view" onclick="loadTransactionDetails(${t.transactionID})" title="View Details">
                            <span class="material-symbols-outlined">visibility</span>
                        </button>
                        <button class="btn btn-icon btn-edit" title="Edit Transaction" onclick="openEditTransactionModal(${t.transactionID})">
                            <span class="material-symbols-outlined">edit</span>
                        </button>
                        <button class="btn btn-icon btn-print" onclick="window.open('/control-panel/transactions/${t.transactionID}/receipt', '_blank')" title="Print PDF Receipt">
                            <span class="material-symbols-outlined">receipt_long</span>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
    filteredRows = Array.from(document.querySelectorAll('.trans-row-main'));
}

function renderAjaxPaginationButtons(totalEntries, page, perPage) {
    const totalPages = Math.max(1, Math.ceil(totalEntries / perPage));
    const infoText = document.getElementById('pagination-info');
    if (infoText) {
        const startIdx = (page - 1) * perPage + 1;
        const endIdx = Math.min(page * perPage, totalEntries);
        infoText.textContent = totalEntries > 0 ? `Showing ${startIdx} to ${endIdx} of ${totalEntries} entries` : "Showing 0 to 0 of 0 entries";
    }

    const buttonsContainer = document.getElementById('pagination-buttons');
    if (!buttonsContainer) return;
    buttonsContainer.innerHTML = '';

    if (totalPages <= 1) return;

    const prevBtn = document.createElement('button');
    prevBtn.className = 'btn-page';
    prevBtn.textContent = 'Previous';
    prevBtn.disabled = (page === 1);
    prevBtn.onclick = () => loadTransactionsPageAjax(page - 1);
    buttonsContainer.appendChild(prevBtn);

    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `btn-page ${i === page ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => loadTransactionsPageAjax(i);
        buttonsContainer.appendChild(pageBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'btn-page';
    nextBtn.textContent = 'Next';
    nextBtn.disabled = (page === totalPages);
    nextBtn.onclick = () => loadTransactionsPageAjax(page + 1);
    buttonsContainer.appendChild(nextBtn);
}

function printCurrentDetailsReceipt() {
    const transId = document.getElementById('details-modal')?.getAttribute('data-loaded-id');
    if (transId) {
        window.open(`/control-panel/transactions/${transId}/receipt`, '_blank');
    } else {
        window.print();
    }
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

function filterExpenses() {
    const searchVal = (document.getElementById('expense-search-input')?.value || '').toLowerCase().trim();
    const rows = document.querySelectorAll('#expense-table-body .expense-row');
    let visibleCount = 0;

    rows.forEach(row => {
        const rowSearch = row.getAttribute('data-search') || '';
        if (searchVal === '' || rowSearch.includes(searchVal)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    const tableBody = document.getElementById('expense-table-body');
    const existingNoRecordsRow = document.getElementById('expense-no-records-row');

    if (visibleCount === 0 && rows.length > 0) {
        if (!existingNoRecordsRow) {
            const noRecordsRow = document.createElement('tr');
            noRecordsRow.id = 'expense-no-records-row';
            noRecordsRow.innerHTML = `
                <td colspan="6" class="no-records-cell" style="text-align: center; padding: 40px; color: var(--on-surface-variant);">No matching operations items found.</td>
            `;
            tableBody.appendChild(noRecordsRow);
        }
    } else if (existingNoRecordsRow) {
        existingNoRecordsRow.remove();
    }
}

/* ===== AUTOCOMPLETE SEARCH & SUGGESTIONS ===== */

// 1. PROPERTY AUTOCOMPLETE
let propertyDisplayLimit = 5;

function handlePropertySearchFocus() {
    renderPropertySuggestions(document.getElementById('new-property-search-input')?.value || '', propertyDisplayLimit);
}

function handlePropertySearchInput(query) {
    propertyDisplayLimit = 5;
    renderPropertySuggestions(query, propertyDisplayLimit);
}

function renderPropertySuggestions(query = '', limit = 5) {
    const box = document.getElementById('new-property-suggestions-box');
    if (!box) return;
    box.style.display = 'block';
    box.classList.remove('hidden');

    if (!window.allProperties) window.allProperties = [];

    const q = query.toLowerCase().trim();
    const filtered = window.allProperties.filter(p => {
        const idStr = String(p.id).toLowerCase();
        const titleStr = (p.title || '').toLowerCase();
        const locStr = (p.location || '').toLowerCase();
        return !q || idStr.includes(q) || titleStr.includes(q) || locStr.includes(q);
    });

    renderPropertyBoxHTML(box, filtered, q, limit);

    // Live AJAX query fetch
    if (q.length >= 1) {
        fetch(`/control-panel/transactions/api/search-properties?q=${encodeURIComponent(q)}`)
            .then(res => res.json())
            .then(data => {
                if (data.success && data.properties) {
                    let updated = false;
                    data.properties.forEach(p => {
                        if (!window.allProperties.some(item => item.id === p.id)) {
                            window.allProperties.push(p);
                            updated = true;
                        }
                    });
                    if (updated) {
                        const newFiltered = window.allProperties.filter(p => {
                            const idStr = String(p.id).toLowerCase();
                            const titleStr = (p.title || '').toLowerCase();
                            const locStr = (p.location || '').toLowerCase();
                            return !q || idStr.includes(q) || titleStr.includes(q) || locStr.includes(q);
                        });
                        renderPropertyBoxHTML(box, newFiltered, q, limit);
                    }
                }
            })
            .catch(err => console.debug('Property AJAX search error:', err));
    }
}

function renderPropertyBoxHTML(box, filtered, q, limit) {
    if (filtered.length === 0) {
        box.innerHTML = '<div style="padding: 12px; color: var(--on-surface-variant, #a0a0a0); font-size: 13px; text-align: center;">No matching properties found</div>';
        return;
    }

    const itemsToShow = filtered.slice(0, limit);
    let html = itemsToShow.map(p => `
        <div class="autocomplete-item" onclick="selectProperty(${p.id})" style="padding: 10px 14px; border-bottom: 1px solid var(--outline-variant, rgba(255,255,255,0.1)); cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background 0.15s ease;">
            <div>
                <span style="font-weight: 700; color: var(--on-surface, #ffffff); font-size: 13px;">[P-${p.id}] ${escapeHtml(p.title)}</span>
                <p style="font-size: 11px; color: var(--on-surface-variant, #a0a0a0); margin: 2px 0 0 0;">${escapeHtml(p.location)} • ${p.listingType}</p>
            </div>
            <span style="font-weight: 700; color: var(--primary, #c5a059); font-size: 13px;">$${Number(p.price).toLocaleString('en-US')}</span>
        </div>
    `).join('');

    if (filtered.length > limit) {
        html += `
            <div style="padding: 8px; text-align: center; background: var(--surface-container-high, #2a2a2a); border-top: 1px solid var(--outline-variant, rgba(255,255,255,0.1));">
                <button type="button" onclick="loadMoreProperties(event, '${escapeHtml(q)}')" style="background: var(--primary, #c5a059); color: #fff; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                    Load More (${filtered.length - limit} remaining)
                </button>
            </div>
        `;
    }

    box.innerHTML = html;
}

function loadMoreProperties(event, query) {
    if (event) event.stopPropagation();
    propertyDisplayLimit += 10;
    renderPropertySuggestions(query, propertyDisplayLimit);
}

function selectProperty(id) {
    const prop = window.allProperties.find(p => p.id === id);
    if (!prop) return;

    document.getElementById('new-property-id-hidden').value = prop.id;
    
    const searchInput = document.getElementById('new-property-search-input');
    if (searchInput) searchInput.classList.add('hidden');

    const box = document.getElementById('new-property-suggestions-box');
    if (box) {
        box.classList.add('hidden');
        box.style.display = 'none';
    }

    const card = document.getElementById('new-property-selected-card');
    document.getElementById('new-prop-selected-title').textContent = `[P-${prop.id}] ${prop.title}`;
    document.getElementById('new-prop-selected-meta').textContent = `$${Number(prop.price).toLocaleString('en-US')} • ${prop.listingType} • ${prop.location}`;
    if (card) {
        card.classList.remove('hidden');
        card.style.display = 'flex';
    }

    // Auto-fill price & type
    const priceInput = document.getElementById('new-price-input');
    if (priceInput) {
        priceInput.value = prop.price;
        priceInput.readOnly = true;
    }

    const typeVal = prop.listingType === 'Rent' ? 'Rent' : 'Sell';
    const hiddenTypeInput = document.getElementById('new-type-hidden');
    if (hiddenTypeInput) hiddenTypeInput.value = typeVal;

    const targetRadio = document.querySelector(`input[name="transactionTypeDisplay"][value="${typeVal}"]`);
    if (targetRadio) {
        targetRadio.checked = true;
        document.querySelectorAll('.radio-card-label').forEach(l => l.classList.remove('selected'));
        const lbl = targetRadio.closest('.radio-card-label');
        if (lbl) lbl.classList.add('selected');
    }

    const radioWrapper = document.getElementById('new-type-radio-wrapper');
    if (radioWrapper) radioWrapper.classList.add('locked');

    updateCommissionRatePreview();
    updateCommissionPreview();
}

function clearSelectedProperty() {
    document.getElementById('new-property-id-hidden').value = '';
    const input = document.getElementById('new-property-search-input');
    if (input) {
        input.value = '';
        input.classList.remove('hidden');
        input.style.display = '';
    }

    const card = document.getElementById('new-property-selected-card');
    if (card) {
        card.classList.add('hidden');
        card.style.display = 'none';
    }

    const priceInput = document.getElementById('new-price-input');
    if (priceInput) {
        priceInput.value = '';
        priceInput.readOnly = false;
    }

    const radioWrapper = document.getElementById('new-type-radio-wrapper');
    if (radioWrapper) radioWrapper.classList.remove('locked');

    updateCommissionRatePreview();
    updateCommissionPreview();
    handlePropertySearchFocus();
}

// 2. CLIENT AUTOCOMPLETE (FOR NEW TRANSACTION)
let clientDisplayLimit = 5;

function handleClientSearchFocus() {
    clientDisplayLimit = 5;
    renderClientSuggestions(document.getElementById('new-client-search-input')?.value || '', clientDisplayLimit);
}

function handleClientSearchInput(query) {
    clientDisplayLimit = 5;
    renderClientSuggestions(query, clientDisplayLimit);
}

function renderClientSuggestions(query = '', limit = 5) {
    const box = document.getElementById('new-client-suggestions-box');
    if (!box) return;
    box.style.display = 'block';
    box.classList.remove('hidden');

    if (!window.allCustomers) window.allCustomers = [];

    const q = query.toLowerCase().trim();
    const filtered = window.allCustomers.filter(c => {
        const idStr = String(c.id).toLowerCase();
        const nameStr = (c.name || '').toLowerCase();
        const emailStr = (c.email || '').toLowerCase();
        const phoneStr = (c.phone || '').toLowerCase();
        const unameStr = (c.username || '').toLowerCase();
        return !q || idStr.includes(q) || nameStr.includes(q) || emailStr.includes(q) || phoneStr.includes(q) || unameStr.includes(q);
    });

    renderClientBoxHTML(box, filtered, q, limit);

    // Live AJAX query fetch
    if (q.length >= 1) {
        fetch(`/control-panel/transactions/api/search-customers?q=${encodeURIComponent(q)}`)
            .then(res => res.json())
            .then(data => {
                if (data.success && data.customers) {
                    let updated = false;
                    data.customers.forEach(c => {
                        if (!window.allCustomers.some(item => item.id === c.id)) {
                            window.allCustomers.push(c);
                            updated = true;
                        }
                    });
                    if (updated) {
                        const newFiltered = window.allCustomers.filter(c => {
                            const idStr = String(c.id).toLowerCase();
                            const nameStr = (c.name || '').toLowerCase();
                            const emailStr = (c.email || '').toLowerCase();
                            const phoneStr = (c.phone || '').toLowerCase();
                            const unameStr = (c.username || '').toLowerCase();
                            return !q || idStr.includes(q) || nameStr.includes(q) || emailStr.includes(q) || phoneStr.includes(q) || unameStr.includes(q);
                        });
                        renderClientBoxHTML(box, newFiltered, q, limit);
                    }
                }
            })
            .catch(err => console.debug('Customer AJAX search error:', err));
    }
}

function renderClientBoxHTML(box, filtered, q = '', limit = 5) {
    if (filtered.length === 0) {
        box.innerHTML = '<div style="padding: 12px; color: var(--on-surface-variant, #a0a0a0); font-size: 13px; text-align: center;">No matching clients found</div>';
        return;
    }

    const itemsToShow = filtered.slice(0, limit);
    let html = itemsToShow.map(c => `
        <div class="autocomplete-item" onclick="selectClient(${c.id})" style="padding: 10px 14px; border-bottom: 1px solid var(--outline-variant, rgba(255,255,255,0.1)); cursor: pointer; transition: background 0.15s ease;">
            <div style="font-weight: 700; color: var(--on-surface, #ffffff); font-size: 13px;">${escapeHtml(c.name)} <span style="font-weight: 400; color: var(--on-surface-variant, #a0a0a0); font-size: 11px;">(ID: ${c.id})</span></div>
            <div style="font-size: 11px; color: var(--on-surface-variant, #a0a0a0); margin-top: 2px;">${escapeHtml(c.email || 'No email')} ${c.phone ? '• ' + escapeHtml(c.phone) : ''}</div>
        </div>
    `).join('');

    if (filtered.length > limit) {
        html += `
            <div style="padding: 8px; text-align: center; background: var(--surface-container-high, #2a2a2a); border-top: 1px solid var(--outline-variant, rgba(255,255,255,0.1));">
                <button type="button" onclick="loadMoreClients(event, '${escapeHtml(q)}')" style="background: var(--primary, #c5a059); color: #fff; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                    Load More (${filtered.length - limit} remaining)
                </button>
            </div>
        `;
    }

    box.innerHTML = html;
}

function loadMoreClients(event, query) {
    if (event) event.stopPropagation();
    clientDisplayLimit += 5;
    renderClientSuggestions(query, clientDisplayLimit);
}

function selectClient(id) {
    const client = window.allCustomers.find(c => c.id === id);
    if (!client) return;

    document.getElementById('new-client-id-hidden').value = client.id;
    
    const searchInput = document.getElementById('new-client-search-input');
    if (searchInput) searchInput.classList.add('hidden');

    const box = document.getElementById('new-client-suggestions-box');
    if (box) {
        box.classList.add('hidden');
        box.style.display = 'none';
    }

    const card = document.getElementById('new-client-selected-card');
    document.getElementById('new-client-selected-name').textContent = `${client.name} (ID: ${client.id})`;
    document.getElementById('new-client-selected-email').textContent = `${client.email || 'No email'} ${client.phone ? '• ' + client.phone : ''}`;
    if (card) {
        card.classList.remove('hidden');
        card.style.display = 'flex';
    }
}

function clearSelectedClient() {
    document.getElementById('new-client-id-hidden').value = '';
    const input = document.getElementById('new-client-search-input');
    if (input) {
        input.value = '';
        input.classList.remove('hidden');
        input.style.display = '';
    }

    const card = document.getElementById('new-client-selected-card');
    if (card) {
        card.classList.add('hidden');
        card.style.display = 'none';
    }

    handleClientSearchFocus();
}

// 3. REPORT CUSTOMER MULTI-SELECT AUTOCOMPLETE
let selectedReportCustomerIds = [];
let reportCustomerDisplayLimit = 5;

function handleReportCustomerSearchFocus() {
    reportCustomerDisplayLimit = 5;
    renderReportCustomerSuggestions(document.getElementById('report-customer-search-input')?.value || '', reportCustomerDisplayLimit);
}

function handleReportCustomerSearchInput(query) {
    reportCustomerDisplayLimit = 5;
    renderReportCustomerSuggestions(query, reportCustomerDisplayLimit);
}

function renderReportCustomerSuggestions(query = '', limit = 5) {
    const box = document.getElementById('report-customer-suggestions-box');
    if (!box) return;
    box.style.display = 'block';
    box.classList.remove('hidden');

    if (!window.allCustomers) window.allCustomers = [];

    const q = query.toLowerCase().trim();
    const filtered = window.allCustomers.filter(c => {
        if (selectedReportCustomerIds.includes(c.id)) return false;
        const idStr = String(c.id).toLowerCase();
        const nameStr = (c.name || '').toLowerCase();
        const emailStr = (c.email || '').toLowerCase();
        const phoneStr = (c.phone || '').toLowerCase();
        const unameStr = (c.username || '').toLowerCase();
        return !q || idStr.includes(q) || nameStr.includes(q) || emailStr.includes(q) || phoneStr.includes(q) || unameStr.includes(q);
    });

    renderReportCustomerBoxHTML(box, filtered, q, limit);

    // Live AJAX query fetch
    if (q.length >= 1) {
        fetch(`/control-panel/transactions/api/search-customers?q=${encodeURIComponent(q)}`)
            .then(res => res.json())
            .then(data => {
                if (data.success && data.customers) {
                    let updated = false;
                    data.customers.forEach(c => {
                        if (!window.allCustomers.some(item => item.id === c.id)) {
                            window.allCustomers.push(c);
                            updated = true;
                        }
                    });
                    if (updated) {
                        const newFiltered = window.allCustomers.filter(c => {
                            if (selectedReportCustomerIds.includes(c.id)) return false;
                            const idStr = String(c.id).toLowerCase();
                            const nameStr = (c.name || '').toLowerCase();
                            const emailStr = (c.email || '').toLowerCase();
                            const phoneStr = (c.phone || '').toLowerCase();
                            const unameStr = (c.username || '').toLowerCase();
                            return !q || idStr.includes(q) || nameStr.includes(q) || emailStr.includes(q) || phoneStr.includes(q) || unameStr.includes(q);
                        });
                        renderReportCustomerBoxHTML(box, newFiltered, q, limit);
                    }
                }
            })
            .catch(err => console.debug('Report Customer AJAX search error:', err));
    }
}

function renderReportCustomerBoxHTML(box, filtered, q = '', limit = 5) {
    if (filtered.length === 0) {
        box.innerHTML = '<div style="padding: 12px; color: var(--on-surface-variant, #a0a0a0); font-size: 13px; text-align: center;">No matching clients found</div>';
        return;
    }

    const itemsToShow = filtered.slice(0, limit);
    let html = itemsToShow.map(c => `
        <div class="autocomplete-item" onclick="addReportCustomerTag(${c.id})" style="padding: 10px 14px; border-bottom: 1px solid var(--outline-variant, rgba(255,255,255,0.1)); cursor: pointer; transition: background 0.15s ease;">
            <div style="font-weight: 700; color: var(--on-surface, #ffffff); font-size: 13px;">${escapeHtml(c.name)} <span style="font-weight: 400; color: var(--on-surface-variant, #a0a0a0); font-size: 11px;">(ID: ${c.id})</span></div>
            <div style="font-size: 11px; color: var(--on-surface-variant, #a0a0a0); margin-top: 2px;">User: ${escapeHtml(c.username || 'N/A')} • ${escapeHtml(c.email || 'No email')} ${c.phone ? '• ' + escapeHtml(c.phone) : ''}</div>
        </div>
    `).join('');

    if (filtered.length > limit) {
        html += `
            <div style="padding: 8px; text-align: center; background: var(--surface-container-high, #2a2a2a); border-top: 1px solid var(--outline-variant, rgba(255,255,255,0.1));">
                <button type="button" onclick="loadMoreReportCustomers(event, '${escapeHtml(q)}')" style="background: var(--primary, #c5a059); color: #fff; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                    Load More (${filtered.length - limit} remaining)
                </button>
            </div>
        `;
    }

    box.innerHTML = html;
}

function loadMoreReportCustomers(event, query) {
    if (event) event.stopPropagation();
    reportCustomerDisplayLimit += 5;
    renderReportCustomerSuggestions(query, reportCustomerDisplayLimit);
}

function addReportCustomerTag(id) {
    if (!selectedReportCustomerIds.includes(id)) {
        selectedReportCustomerIds.push(id);
        updateReportCustomerTagsUI();
    }
    const input = document.getElementById('report-customer-search-input');
    if (input) input.value = '';
    const box = document.getElementById('report-customer-suggestions-box');
    if (box) {
        box.classList.add('hidden');
        box.style.display = 'none';
    }
}

function removeReportCustomerTag(id) {
    selectedReportCustomerIds = selectedReportCustomerIds.filter(cId => cId !== id);
    updateReportCustomerTagsUI();
}

function updateReportCustomerTagsUI() {
    const container = document.getElementById('report-customer-tags-container');
    const hiddenInput = document.getElementById('report-customer-ids-hidden');
    if (!container || !hiddenInput) return;

    if (selectedReportCustomerIds.length === 0) {
        container.innerHTML = '<span style="font-size: 12px; color: var(--on-surface-variant, #888); font-style: italic;">All clients included (No filter selected)</span>';
        hiddenInput.value = 'All';
        return;
    }

    hiddenInput.value = selectedReportCustomerIds.join(',');

    let html = selectedReportCustomerIds.map(id => {
        const c = window.allCustomers.find(item => item.id === id);
        const name = c ? c.name : `Client #${id}`;
        return `
            <span style="display: inline-flex; align-items: center; gap: 6px; background: var(--primary, #c5a059); color: #fff; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-weight: 600;">
                <span>${escapeHtml(name)}</span>
                <button type="button" onclick="removeReportCustomerTag(${id})" style="background: transparent; border: none; color: #fff; cursor: pointer; font-weight: 700; font-size: 14px; line-height: 1; padding: 0 2px;">&times;</button>
            </span>
        `;
    }).join('');

    container.innerHTML = html;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
