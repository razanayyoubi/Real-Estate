/* -------------------------------------------------------------
   LEBESTATES CUSTOMER DASHBOARD JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // 1. TABS & VIEWS CONTROLLER
    const viewSections = document.querySelectorAll('.customer-view-section');

    function switchView(viewName) {
        if (!viewName) return;

        // Hide all sections first
        viewSections.forEach(section => {
            section.classList.remove('customer-view-section--active');
        });

        // Show target section
        const targetSection = document.getElementById(`view-${viewName}`);
        if (targetSection) {
            targetSection.classList.add('customer-view-section--active');
        }

        // Update URL hash safely without jump
        if (window.location.hash !== `#${viewName}`) {
            history.pushState(null, null, `#${viewName}`);
        }
    }

    // Check initial hash on load and on hash change
    const validViews = ['dashboard', 'wishlist', 'tours', 'inquiries', 'ledger'];
    function checkHash() {
        const hash = window.location.hash.substring(1);
        if (hash && validViews.includes(hash)) {
            switchView(hash);
        } else {
            switchView('dashboard');
        }
    }

    window.addEventListener('hashchange', checkHash);
    checkHash();

    // 2. DYNAMIC WISHLIST TOGGLE (FAVORITE REMOVAL AJAX)
    const removeWishlistBtns = document.querySelectorAll('.wishlist-card-btn-remove');
    removeWishlistBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const propertyId = btn.getAttribute('data-id');
            if (!propertyId) return;

            const card = btn.closest('.wishlist-card');
            
            // AJAX request to toggle favorite (remove)
            fetch('/properties/favorite/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ property_id: parseInt(propertyId) })
            })
            .then(res => {
                if (res.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                return res.json();
            })
            .then(data => {
                if (data && data.success && data.action === 'removed') {
                    if (card) {
                        card.style.transform = 'scale(0.9)';
                        card.style.opacity = '0';
                        setTimeout(() => {
                            card.remove();
                            // Check if empty
                            const remainingCards = document.querySelectorAll('.wishlist-card');
                            if (remainingCards.length === 0) {
                                const grid = document.getElementById('wishlist-active-grid');
                                const emptyView = document.getElementById('wishlist-empty-view');
                                if (grid) grid.style.display = 'none';
                                if (emptyView) emptyView.style.display = 'flex';
                            }
                            
                            // Dynamically update favorites KPI count
                            const favCountEl = document.getElementById('kpi-fav-count');
                            if (favCountEl) {
                                const currentCount = parseInt(favCountEl.textContent) || 0;
                                if (currentCount > 0) {
                                    favCountEl.textContent = (currentCount - 1).toString().padStart(2, '0');
                                }
                            }
                        }, 300);
                    }
                } else if (data && data.error) {
                    alert('Error: ' + data.error);
                }
            })
            .catch(err => {
                console.error('Error toggling favorite:', err);
            });
        });
    });

    // 3. MICRO-INTERACTIONS
    // KPI metrics cards clicking takes user to respective tab
    const metricCards = document.querySelectorAll('.bento-card--stat[data-target-view]');
    metricCards.forEach(card => {
        card.addEventListener('click', () => {
            const target = card.getAttribute('data-target-view');
            switchView(target);
        });
    });
});
