document.addEventListener('DOMContentLoaded', () => {
    // Calculator state
    let calcType = 'sale'; // 'sale' or 'rent'

    // DOM Elements
    const elements = {
        form: document.getElementById('commission-form'),
        alertBox: document.getElementById('settings-alert-box'),
        
        // Settings form inputs
        inputRentRule: document.getElementById('input-rent-rule'),
        inputBuyerRate: document.getElementById('input-buyer-rate'),
        inputSellerRate: document.getElementById('input-seller-rate'),
        inputAgentShare: document.getElementById('input-agent-share'),
        
        // Buttons
        btnSave: document.getElementById('btn-save'),
        btnDiscard: document.getElementById('btn-discard'),
        btnReset: document.getElementById('btn-reset'),
        
        // Calculator elements
        optSale: document.getElementById('opt-sale'),
        optRent: document.getElementById('opt-rent'),
        slider: document.getElementById('slider'),
        inputPrice: document.getElementById('calc-price'),
        labelPrice: document.getElementById('calc-price-label'),
        
        // Calculator outputs
        resBuyer: document.getElementById('res-buyer'),
        resSeller: document.getElementById('res-seller'),
        resGross: document.getElementById('res-gross'),
        resAgentPerc: document.getElementById('res-agent-perc'),
        resAgentVal: document.getElementById('res-agent-val'),
        resNet: document.getElementById('res-net')
    };

    // Helper: format currency
    function formatCurrency(val) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0
        }).format(val);
    }

    // Helper: show alert banner
    function showAlert(message, type = 'success') {
        elements.alertBox.className = `alert-box alert-box--${type}`;
        elements.alertBox.textContent = message;
        elements.alertBox.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Helper: hide alert banner
    function hideAlert() {
        elements.alertBox.style.display = 'none';
        elements.alertBox.textContent = '';
    }

    // Toggle calculator modes (Sale vs Rent)
    function setCalcMode(mode) {
        calcType = mode;
        if (mode === 'sale') {
            elements.optSale.classList.add('active');
            elements.optRent.classList.remove('active');
            elements.slider.style.transform = 'translateX(0)';
            elements.labelPrice.textContent = 'Listed Property Price ($)';
            elements.inputPrice.value = 500000;
        } else {
            elements.optRent.classList.add('active');
            elements.optSale.classList.remove('active');
            elements.slider.style.transform = 'translateX(100%)';
            elements.labelPrice.textContent = 'Monthly Rent Price ($)';
            elements.inputPrice.value = 2500;
        }
        updateCalculation();
    }

    // Core Calculation Logic
    function updateCalculation() {
        const price = parseFloat(elements.inputPrice.value) || 0;
        const buyerRate = parseFloat(elements.inputBuyerRate.value) || 0;
        const sellerRate = parseFloat(elements.inputSellerRate.value) || 0;
        const agentShare = parseFloat(elements.inputAgentShare.value) || 0;
        const rentRule = elements.inputRentRule.value;
        
        let buyerComm = 0;
        let sellerComm = 0;

        if (calcType === 'sale') {
            buyerComm = price * (buyerRate / 100);
            sellerComm = price * (sellerRate / 100);
        } else {
            // "1 Month" rent. Split 50/50
            buyerComm = price;
            sellerComm = price * 0.5;
        }

        const gross = buyerComm + sellerComm;
        const agentPayout = gross * (agentShare / 100);
        const net = gross - agentPayout;

        // Render to UI
        elements.resBuyer.textContent = formatCurrency(buyerComm);
        elements.resSeller.textContent = formatCurrency(sellerComm);
        elements.resGross.textContent = formatCurrency(gross);
        elements.resAgentPerc.textContent = agentShare;
        elements.resAgentVal.textContent = '-' + formatCurrency(agentPayout);
        elements.resNet.textContent = formatCurrency(net);
    }

    // Toggle click listeners
    elements.optSale.addEventListener('click', () => setCalcMode('sale'));
    elements.optRent.addEventListener('click', () => setCalcMode('rent'));

    // Input change listeners
    [
        elements.inputPrice,
        elements.inputBuyerRate,
        elements.inputSellerRate,
        elements.inputAgentShare,
        elements.inputRentRule
    ].forEach(el => {
        el.addEventListener('input', updateCalculation);
        el.addEventListener('change', updateCalculation);
    });

    // Form submission (Save)
    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideAlert();

        const payload = {
            rent_rule: elements.inputRentRule.value,
            buyer_rate: parseFloat(elements.inputBuyerRate.value),
            seller_rate: parseFloat(elements.inputSellerRate.value),
            agent_split: parseInt(elements.inputAgentShare.value)
        };

        // UI Feedback loader
        const originalBtnText = elements.btnSave.innerHTML;
        elements.btnSave.disabled = true;
        elements.btnSave.innerHTML = `
            <svg class="animate-spin" style="width:18px; height:18px; color:#ffffff; animation: spin-anim 1s linear infinite; display:inline-block; vertical-align:middle;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle style="opacity:0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path style="opacity:0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span style="vertical-align:middle; margin-left: 6px;">Saving Settings...</span>
        `;

        try {
            const response = await fetch('/control-panel/commission-settings/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (response.ok) {
                showAlert(result.message || 'Settings saved successfully!', 'success');
            } else {
                showAlert(result.error || 'Failed to save settings.', 'error');
            }
        } catch (err) {
            console.error('Save settings error:', err);
            showAlert('Network error: Unable to contact the database server.', 'error');
        } finally {
            elements.btnSave.disabled = false;
            elements.btnSave.innerHTML = originalBtnText;
        }
    });

    // Discard Changes (Reload Page)
    elements.btnDiscard.addEventListener('click', () => {
        hideAlert();
        window.location.reload();
    });

    // Reset Settings to Defaults
    elements.btnReset.addEventListener('click', async () => {
        hideAlert();
        if (!confirm('Are you sure you want to restore the global default commission parameters? This will clear any database custom values.')) {
            return;
        }

        try {
            const response = await fetch('/control-panel/commission-settings/reset', {
                method: 'POST'
            });

            const result = await response.json();
            if (response.ok) {
                // Revert values in UI
                elements.inputRentRule.value = '1 Month';
                elements.inputBuyerRate.value = 2.5;
                elements.inputSellerRate.value = 2.5;
                elements.inputAgentShare.value = 30;
                
                updateCalculation();
                showAlert(result.message || 'Restored global default parameters successfully.', 'success');
            } else {
                showAlert(result.error || 'Failed to reset settings.', 'error');
            }
        } catch (err) {
            console.error('Reset settings error:', err);
            showAlert('Network error: Unable to contact the database server.', 'error');
        }
    });

    // Add spin keyframes style dynamically for AJAX saving spinner
    const styleSheet = document.createElement("style");
    styleSheet.textContent = `
        @keyframes spin-anim {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(styleSheet);

    // Run initial calculation
    updateCalculation();
});
