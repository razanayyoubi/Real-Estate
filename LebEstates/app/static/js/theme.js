/* -------------------------------------------------------------
   LEBESTATES PUBLIC MOBILE NAVIGATION
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    /* ─────────────────────────────────────────────────────────
       RESPONSIVE MOBILE LEFT SIDEBAR NAVIGATION
    ───────────────────────────────────────────────────────── */
    const hamburger = document.getElementById('hamburger');
    const sidebarClose = document.getElementById('sidebar-close');
    const navMenu = document.getElementById('nav-menu');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const navLinks = document.querySelectorAll('.nav-link');

    const openSidebar = () => {
        if (navMenu) navMenu.classList.add('active');
        if (sidebarOverlay) sidebarOverlay.classList.add('active');
        document.body.style.overflow = 'hidden'; // lock page scroll when sidebar is open
    };

    const closeSidebar = () => {
        if (navMenu) navMenu.classList.remove('active');
        if (sidebarOverlay) sidebarOverlay.classList.remove('active');
        document.body.style.overflow = ''; // unlock page scroll
    };

    // Toggle button opens the sidebar
    if (hamburger) {
        hamburger.addEventListener('click', (e) => {
            e.stopPropagation();
            openSidebar();
        });
    }

    // Sidebar Close button
    if (sidebarClose) {
        sidebarClose.addEventListener('click', (e) => {
            e.stopPropagation();
            closeSidebar();
        });
    }

    // Overlay click dismisses the sidebar
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            closeSidebar();
        });
    }

    // Dismiss sidebar when clicking outside of it
    document.addEventListener('click', (e) => {
        if (navMenu && navMenu.classList.contains('active')) {
            const clickedInsideSidebar = navMenu.contains(e.target);
            const clickedHamburger = hamburger && hamburger.contains(e.target);
            if (!clickedInsideSidebar && !clickedHamburger) {
                closeSidebar();
            }
        }
    });

    // Dismiss sidebar when a navigation link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            closeSidebar();
        });
    });
});
