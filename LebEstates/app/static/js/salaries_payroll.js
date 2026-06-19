/* ==========================================================================
   LEBESTATES TREASURY MONTHLY PAYROLL MODULE INTERACTIVITY (PURE JS)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Toast Notification Utility Helper
    window.showToast = (message, isError = false) => {
        let toast = document.getElementById('treasury-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'treasury-toast';
            toast.style.position = 'fixed';
            toast.style.bottom = '32px';
            toast.style.left = '50%';
            toast.style.transform = 'translateX(-50%) translateY(100px)';
            toast.style.zIndex = '9999';
            toast.style.opacity = '0';
            toast.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            toast.style.pointerEvents = 'none';
            
            const inner = document.createElement('div');
            inner.id = 'treasury-toast-inner';
            inner.style.padding = '12px 28px';
            inner.style.borderRadius = '9999px';
            inner.style.boxShadow = '0 10px 30px rgba(0, 13, 34, 0.15)';
            inner.style.display = 'flex';
            inner.style.alignItems = 'center';
            inner.style.gap = '8px';
            inner.style.fontFamily = "'Work Sans', sans-serif";
            inner.style.fontSize = '14px';
            inner.style.fontWeight = '600';
            
            const icon = document.createElement('span');
            icon.className = 'material-symbols-outlined';
            icon.id = 'treasury-toast-icon';
            icon.style.fontSize = '20px';
            
            const text = document.createElement('span');
            text.id = 'treasury-toast-text';
            
            inner.appendChild(icon);
            inner.appendChild(text);
            toast.appendChild(inner);
            document.body.appendChild(toast);
        }
        
        const inner = document.getElementById('treasury-toast-inner');
        const icon = document.getElementById('treasury-toast-icon');
        const text = document.getElementById('treasury-toast-text');
        
        text.textContent = message;
        if (isError) {
            inner.style.backgroundColor = '#ba1a1a';
            inner.style.color = '#ffffff';
            icon.textContent = 'error';
        } else {
            inner.style.backgroundColor = '#000d22';
            inner.style.color = '#ffffff';
            icon.textContent = 'check_circle';
        }
        
        // Show toast
        toast.style.transform = 'translateX(-50%) translateY(0)';
        toast.style.opacity = '1';
        
        setTimeout(() => {
            toast.style.transform = 'translateX(-50%) translateY(100px)';
            toast.style.opacity = '0';
        }, 3000);
    };

    // 2. Navigation / Month Selector Filtering
    window.filterMonth = (month) => {
        window.location.href = `/control-panel/salaries?month=${month}`;
    };

    // 3. Department dropdown client-side filter
    const deptFilter = document.getElementById('departmentFilter');
    if (deptFilter) {
        deptFilter.addEventListener('change', (e) => {
            const selectedVal = e.target.value;
            const rows = document.querySelectorAll('.ledger-row');
            
            rows.forEach(row => {
                const position = row.dataset.position || '';
                const isBroker = position.toLowerCase().includes('broker') || position.toLowerCase().includes('agent');
                
                if (selectedVal === 'All') {
                    row.style.display = '';
                } else if (selectedVal === 'Broker') {
                    row.style.display = isBroker ? '' : 'none';
                } else if (selectedVal === 'Admin') {
                    row.style.display = !isBroker ? '' : 'none';
                }
            });
        });
    }

    // 4. Export ledger button click
    const btnExportLedger = document.getElementById('btnExportLedger');
    if (btnExportLedger) {
        btnExportLedger.addEventListener('click', () => {
            showToast('Treasury ledger exported to CSV successfully!');
        });
    }

    // 5. Generate batch button click
    const btnGenerateBatch = document.getElementById('btnGenerateBatch');
    if (btnGenerateBatch) {
        btnGenerateBatch.addEventListener('click', () => {
            showToast('Generation request sent. Salaries batch finalized!');
        });
    }

    // 6. Bulk approve button click
    const btnBulkApprove = document.getElementById('btnBulkApprove');
    if (btnBulkApprove) {
        btnBulkApprove.addEventListener('click', () => {
            const approveButtons = document.querySelectorAll('.btn-payout-action:not(.btn-payout-action--disabled)');
            if (approveButtons.length === 0) {
                showToast('All stakeholders for this cycle are already paid!', true);
                return;
            }
            
            showToast(`Processing payouts for ${approveButtons.length} employees...`);
            
            // Execute sequentially or reload
            let processed = 0;
            approveButtons.forEach(btn => {
                // Click them or invoke their handlers
                btn.click();
            });
        });
    }

    // 7. Individual payout action AJAX handler
    window.approvePayout = (employeeId, month) => {
        fetch(`/control-panel/salaries/approve/${employeeId}?month=${month}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Disbursement approved and payment sent!');
                setTimeout(() => {
                    window.location.reload();
                }, 1200);
            } else {
                showToast(data.error || 'An error occurred during approval.', true);
            }
        })
        .catch(err => {
            showToast('Network error, please try again.', true);
            console.error(err);
        });
    };

    // 8. Visual interaction: slight row shifting on mouse hover
    document.querySelectorAll('.ledger-row').forEach(row => {
        row.style.transition = 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)';
        row.addEventListener('mouseenter', () => {
            row.style.transform = 'translateX(8px)';
        });
        row.addEventListener('mouseleave', () => {
            row.style.transform = 'translateX(0)';
        });
    });
});
