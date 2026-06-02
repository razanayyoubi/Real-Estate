/* -------------------------------------------------------------
   LEBESTATES ADMIN DASHBOARD CUSTOM JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // 1. COLLAPSIBLE SIDEBAR WITH BLURRED OVERLAY
    const sidebar = document.getElementById('sideNav');
    const hamburgerButton = document.getElementById('hamburger') || document.getElementById('hamburgerButton');
    const sidebarOverlay = document.getElementById('dashboardSidebarOverlay');
    const toggleButton = document.getElementById('toggleButton'); // Optional inner close button

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

    // SIMULATED KPI ANIMATIONS ON PAGE LOAD
    const chartBars = document.querySelectorAll('.chart-bar');
    chartBars.forEach(bar => {
        const originalHeight = bar.style.height || bar.parentElement.style.getPropertyValue('--bar-height') || '50%';
        bar.style.height = '0%';
        setTimeout(() => {
            bar.style.height = originalHeight;
        }, 150);
    });
});
