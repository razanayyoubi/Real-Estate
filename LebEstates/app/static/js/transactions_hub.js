/* ==========================================================================
   LEBESTATES TRANSACTIONS PORTAL HUB MODULE INTERACTIVITY (PURE JS)
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    const controlCards = document.querySelectorAll('.control-card');
    const toastContainer = document.getElementById('toast');
    const toastText = document.getElementById('toastText');
    let toastTimeout = null;

    // Toast utility helper
    const showToast = (message) => {
        if (!toastContainer || !toastText) return;

        // Reset previous timeout if active
        if (toastTimeout) {
            clearTimeout(toastTimeout);
        }

        toastText.textContent = message;
        toastContainer.classList.add('show');

        toastTimeout = setTimeout(() => {
            toastContainer.classList.remove('show');
        }, 3000);
    };

    // Click handler for control cards
    controlCards.forEach(card => {
        card.addEventListener('click', (e) => {
            const action = card.dataset.action;
            const message = card.dataset.message;

            if (action === 'ledger') {
                // Navigate to the transaction list ledger table
                window.location.href = '/control-panel/transactions/ledger';
            } else if (action === 'revenue-dashboard') {
                // Navigate to the revenue dashboard
                window.location.href = '/control-panel/transactions/revenue-dashboard';
            } else if (action === 'commission-settings') {
                // Navigate to the commission settings page
                window.location.href = '/control-panel/commission-settings';
            } else if (action === 'payment-tracking') {
                // Navigate to the payment tracking page
                window.location.href = '/control-panel/transactions/payment-tracking';
            } else if (action === 'commissions') {
                // Navigate to the agent commissions page
                window.location.href = '/control-panel/commissions';
            } else if (action === 'salaries') {
                // Navigate to the treasury salaries page
                window.location.href = '/control-panel/salaries';
            } else if (action === 'toast' && message) {
                // Show construction toast alert
                showToast(message);
            }
        });
    });
});
