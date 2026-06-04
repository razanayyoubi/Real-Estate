/* -------------------------------------------------------------
   LEBESTATES ADMIN CONTROL PANEL CUSTOM JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // 1. COLLAPSIBLE SIDEBAR WITH BLURRED OVERLAY
    const sidebar = document.getElementById('sideNav');
    const hamburgerButton = document.getElementById('hamburger') || document.getElementById('hamburgerButton');
    const sidebarOverlay = document.getElementById('dashboardSidebarOverlay');
    const toggleButton = document.getElementById('toggleButton'); // Inner toggle close button

    function openSidebar() {
        if (sidebar) sidebar.classList.add('sidebar--open');
        if (sidebarOverlay) sidebarOverlay.classList.add('active');
        document.body.style.overflow = 'hidden'; // lock page scroll when sidebar is open
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('sidebar--open');
        if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        document.body.style.overflow = ''; // unlock scroll
    }

    if (hamburgerButton && hamburgerButton.id !== 'hamburger') {
        hamburgerButton.addEventListener('click', (e) => {
            e.stopPropagation();
            if (sidebar && sidebar.classList.contains('sidebar--open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (toggleButton) {
        toggleButton.addEventListener('click', (e) => {
            e.stopPropagation();
            closeSidebar();
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Dismiss sidebar when clicking outside of it
    document.addEventListener('click', (e) => {
        if (sidebar && sidebar.classList.contains('sidebar--open')) {
            const clickedInsideSidebar = sidebar.contains(e.target);
            const clickedHamburger = hamburgerButton && hamburgerButton.contains(e.target);
            if (!clickedInsideSidebar && !clickedHamburger) {
                closeSidebar();
            }
        }
    });

    // 2. MODULE CARD CLICK REDIRECTION
    document.querySelectorAll('.module-card[data-href]').forEach(card => {
        card.addEventListener('click', () => {
            const url = card.getAttribute('data-href');
            if (url) {
                window.location.href = url;
            }
        });
    });

});

/**
 * Global Hierarchical Group Accordion Toggle Function
 * Exposed on `window` to support declarative inline HTML `onclick` callbacks safely.
 */
window.toggleGroup = function (id) {
    const groupElement = document.getElementById(id);
    if (!groupElement) return;

    if (groupElement.classList.contains('sidebar__group')) {
        groupElement.classList.toggle('sidebar__group--expanded');
    } else if (groupElement.classList.contains('sidebar__subgroup')) {
        groupElement.classList.toggle('sidebar__subgroup--expanded');
    }
};
