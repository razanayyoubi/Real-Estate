/**
 * LebEstates CRM - Agent Commissions JS Controller
 */

let isSyncing = false;

document.addEventListener('DOMContentLoaded', () => {
    // Initialization setup
    updateSyncTime();
});

/**
 * Updates the "Last Synced" text indicator to the current system time
 */
function updateSyncTime() {
    const syncStatusText = document.getElementById('syncStatusText');
    const syncDot = document.getElementById('syncDot');
    if (syncStatusText) {
        const now = new Date();
        const hrs = String(now.getHours()).padStart(2, '0');
        const mins = String(now.getMinutes()).padStart(2, '0');
        const secs = String(now.getSeconds()).padStart(2, '0');
        syncStatusText.textContent = `Last synced: ${hrs}:${mins}:${secs}`;
    }
    if (syncDot) {
        syncDot.classList.add('pulsing');
    }
}

/**
 * Helper to animate KPI number updates with a soft fade transition
 */
function updateElementTextAnimated(elementId, newText) {
    const el = document.getElementById(elementId);
    if (el && el.textContent.trim() !== String(newText).trim()) {
        el.style.transition = 'opacity 0.15s ease';
        el.style.opacity = '0';
        setTimeout(() => {
            el.textContent = newText;
            el.style.opacity = '1';
        }, 150);
    }
}

/**
 * Fetch commissions dashboard stats dynamically from the backend JSON endpoint
 */
function fetchCommissionsData() {
    if (isSyncing) return;
    isSyncing = true;

    const syncBtn = document.getElementById('manualSyncBtn');
    const syncDot = document.getElementById('syncDot');
    const syncStatusText = document.getElementById('syncStatusText');

    if (syncBtn) syncBtn.classList.add('spinning');
    if (syncDot) syncDot.classList.remove('pulsing');
    if (syncStatusText) syncStatusText.textContent = 'Syncing...';

    fetch('/control-panel/commissions/data')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
            return response.json();
        })
        .then(res => {
            if (res.success && res.data) {
                const data = res.data;
                
                // 1. Update KPI Values
                updateElementTextAnimated('kpi-total-volume', data.kpis.total_commission_volume);
                updateElementTextAnimated('kpi-ready-payout', data.kpis.ready_for_payout);
                updateElementTextAnimated('kpi-avg-rate', data.kpis.avg_commission_rate);
                updateElementTextAnimated('kpi-active-agents', data.kpis.active_agents);

                // 2. Re-render Top Performing Agents
                renderTopPerformers(data.top_agents);

                // 3. Re-render Recent Commissions Ledger
                renderLedgerTable(data.ledger);

                // 4. Re-render Agency Expenses
                renderExpensesTable(data.expenses);

                updateSyncTime();
            } else {
                if (syncStatusText) syncStatusText.textContent = 'Sync failed';
                console.error('Commissions sync data error:', res.error);
            }
        })
        .catch(err => {
            if (syncStatusText) syncStatusText.textContent = 'Connection lost';
            console.error('Polling commissions failed:', err);
        })
        .finally(() => {
            isSyncing = false;
            if (syncBtn) syncBtn.classList.remove('spinning');
        });
}

/**
 * Re-renders the Top Performers section dynamically
 */
function renderTopPerformers(agents) {
    const container = document.getElementById('performers-container');
    if (!container) return;

    if (!agents || agents.length === 0) {
        container.innerHTML = `
            <div class="no-data-card" style="grid-column: span 3;">
                <span class="material-symbols-outlined">emoji_events</span>
                <p>No agent commission data recorded for closed deals yet.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = agents.map(agent => {
        const fillPercent = agent.rank === 1 ? '100%' : agent.rank === 2 ? '75%' : '50%';
        return `
            <div class="performer-card rank-${agent.rank}">
                <div class="performer-rank-badge">#${agent.rank}</div>
                <div class="performer-avatar-wrapper">
                    <img src="${agent.avatar_url}" alt="${agent.name}" class="performer-avatar">
                </div>
                <div class="performer-info">
                    <h5 class="performer-name">${agent.name}</h5>
                    <p class="performer-role">${agent.position}</p>
                </div>
                <div class="performer-stats-grid">
                    <div class="perf-stat-item">
                        <span class="stat-label">Deals Closed</span>
                        <span class="stat-val">${agent.deal_count}</span>
                    </div>
                    <div class="perf-stat-item">
                        <span class="stat-label">Agent Split</span>
                        <span class="stat-val highlight">${agent.agent_share}</span>
                    </div>
                </div>
                <div class="performer-progress-bar">
                    <div class="performer-progress-fill" style="width: ${fillPercent};"></div>
                </div>
                <div class="performer-footer">
                    <span class="stat-label">Total Commission:</span>
                    <span class="stat-val-sm">${agent.total_commission}</span>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Re-renders the recent commissions ledger rows
 */
function renderLedgerTable(ledgerItems) {
    const tbody = document.getElementById('ledger-table-body');
    if (!tbody) return;

    if (!ledgerItems || ledgerItems.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="no-records">No commissions transactions found.</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = ledgerItems.map(item => {
        const optPending = item.status === 'Escrow' ? 'selected' : '';
        const optProgress = item.status === 'Legal' ? 'selected' : '';
        const optCompleted = item.status === 'Closed' ? 'selected' : '';
        const optCancelled = item.status === 'Cancelled' ? 'selected' : '';
        const selectClass = item.status === 'Closed' ? 'completed' : item.status === 'Escrow' ? 'pending' : item.status === 'Legal' ? 'inprogress' : 'cancelled';
        const typeText = item.type === 'Sell' ? 'Sale' : 'Rental';

        return `
            <tr class="ledger-row" 
                data-search="${item.id.toLowerCase()} ${item.property_title.toLowerCase()} ${item.agent_name.toLowerCase()} ${item.client_name.toLowerCase()}"
                data-type="${item.type}"
                data-status="${item.status}">
                <td class="id-cell">${item.id}</td>
                <td class="property-cell" title="${item.property_title}">
                    <div class="agent-cell">
                        <span class="prop-text" style="font-weight: 600; color: var(--primary);">${item.property_title}</span>
                        <span style="font-size: 11px; color: var(--on-surface-variant); font-weight: 500;">${typeText}</span>
                    </div>
                </td>
                <td>
                    <div class="agent-cell">
                        <span class="agent-name">${item.agent_name}</span>
                        <span class="agent-title">${item.agent_position}</span>
                    </div>
                </td>
                <td>${item.client_name}</td>
                <td class="text-right">
                    <div class="agent-cell" style="align-items: flex-end;">
                        <span style="font-weight: 700; color: var(--primary);">${item.final_price_formatted}</span>
                        <span style="font-size: 11px; color: var(--on-surface-variant);">Comm: ${item.commission_amount_formatted}</span>
                    </div>
                </td>
                <td class="text-right highlight font-weight-700">${item.agent_share_formatted}</td>
                <td class="text-center">
                    <select class="payment-select-dropdown status-${selectClass}" onchange="updateCommissionTransactionStatus(${item.raw_id}, this)">
                        <option value="Pending" ${optPending}>Pending</option>
                        <option value="In progress" ${optProgress}>In progress</option>
                        <option value="Completed" ${optCompleted}>Completed</option>
                        <option value="Cancelled" ${optCancelled}>Cancelled</option>
                    </select>
                </td>
                <td class="date-cell">${item.date}</td>
            </tr>
        `;
    }).join('');

    // Apply any active filters
    filterLedger();
}

/**
 * Re-renders the agency expenses table rows
 */
function renderExpensesTable(expenses) {
    const tbody = document.getElementById('expense-table-body');
    if (!tbody) return;

    if (!expenses || expenses.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="no-records">No operations expenses recorded.</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = expenses.map(exp => {
        const catClass = exp.category.toLowerCase().replace(/\s+/g, '-');
        return `
            <tr class="expense-row" data-search="${exp.id.toLowerCase()} ${exp.item.toLowerCase()} ${exp.category.toLowerCase()}">
                <td class="id-cell">${exp.id}</td>
                <td class="item-cell font-weight-600">${exp.item}</td>
                <td>
                    <span class="category-tag ${catClass}">${exp.category}</span>
                </td>
                <td class="text-right error-color font-weight-700">${exp.amount_formatted}</td>
                <td class="text-center">
                    <span class="status-badge ${exp.status.toLowerCase()}">${exp.status}</span>
                </td>
                <td class="date-cell">${exp.date}</td>
            </tr>
        `;
    }).join('');

    // Apply any active filters
    filterExpenses();
}

/**
 * Interactive filter for the commissions ledger table
 */
function filterLedger() {
    const searchVal = (document.getElementById('ledger-search-input')?.value || '').toLowerCase().trim();
    const typeVal = document.getElementById('ledger-type-filter')?.value || 'All';
    const statusVal = document.getElementById('ledger-status-filter')?.value || 'All';

    const rows = document.querySelectorAll('#ledger-table-body .ledger-row');
    let visibleCount = 0;

    rows.forEach(row => {
        const rowSearch = row.getAttribute('data-search') || '';
        const rowType = row.getAttribute('data-type') || '';
        const rowStatus = row.getAttribute('data-status') || '';

        const matchesSearch = searchVal === '' || rowSearch.includes(searchVal);
        const matchesType = typeVal === 'All' || rowType === typeVal;
        const matchesStatus = statusVal === 'All' || rowStatus === statusVal;

        if (matchesSearch && matchesType && matchesStatus) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Handle no matching records state
    const tableBody = document.getElementById('ledger-table-body');
    const existingNoRecordsRow = document.getElementById('ledger-no-records-row');
    
    if (visibleCount === 0 && rows.length > 0) {
        if (!existingNoRecordsRow) {
            const noRecordsRow = document.createElement('tr');
            noRecordsRow.id = 'ledger-no-records-row';
            noRecordsRow.innerHTML = `
                <td colspan="8" class="no-records">No matching ledger items found.</td>
            `;
            tableBody.appendChild(noRecordsRow);
        }
    } else if (existingNoRecordsRow) {
        existingNoRecordsRow.remove();
    }
}

/**
 * Interactive filter for the operations ledger table
 */
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
                <td colspan="6" class="no-records">No matching operations items found.</td>
            `;
            tableBody.appendChild(noRecordsRow);
        }
    } else if (existingNoRecordsRow) {
        existingNoRecordsRow.remove();
    }
}

/**
 * Resets search filters and selection parameters on the Commissions Ledger
 */
function resetLedgerFilters() {
    const searchInput = document.getElementById('ledger-search-input');
    const typeFilter = document.getElementById('ledger-type-filter');
    const statusFilter = document.getElementById('ledger-status-filter');
    
    if (searchInput) searchInput.value = '';
    if (typeFilter) typeFilter.value = 'All';
    if (statusFilter) statusFilter.value = 'All';
    
    filterLedger();
}

/**
 * AJAX update for transaction payment status on the commissions ledger
 */
function updateCommissionTransactionStatus(transId, selectElement) {
    const originalClass = selectElement.className;
    const newStatus = selectElement.value;

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
            alert(data.error);
            fetchCommissionsData();
        } else {
            const simplifiedStatus = newStatus.replace(/\s+/g, '').toLowerCase();
            selectElement.className = `payment-select-dropdown status-${simplifiedStatus}`;
            
            // Trigger a complete refresh to recalculate KPIs, Top Performers list and table data
            fetchCommissionsData();
        }
    })
    .catch(err => {
        console.error('Failed to update status:', err);
        fetchCommissionsData();
    });
}
