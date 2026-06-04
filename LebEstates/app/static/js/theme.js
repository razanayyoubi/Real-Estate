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
            const sideNav = document.getElementById('sideNav');
            if (sideNav) {
                // If there's an admin aside sidebar on the page, toggle it!
                sideNav.classList.toggle('sidebar--open');
                const overlay = document.getElementById('dashboardSidebarOverlay') || document.getElementById('sidebar-overlay');
                if (overlay) overlay.classList.toggle('active');
            } else {
                // Otherwise, toggle the mobile navigation drawer
                openSidebar();
            }
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
            const sideNav = document.getElementById('sideNav');
            if (sideNav) {
                sideNav.classList.remove('sidebar--open');
                const overlay = document.getElementById('dashboardSidebarOverlay') || document.getElementById('sidebar-overlay');
                if (overlay) overlay.classList.remove('active');
            }
        });
    }

    // Dismiss sidebar when clicking outside of it
    document.addEventListener('click', (e) => {
        const sideNav = document.getElementById('sideNav');
        if (sideNav && sideNav.classList.contains('sidebar--open')) {
            const clickedInsideSidebar = sideNav.contains(e.target);
            const clickedHamburger = hamburger && hamburger.contains(e.target);
            if (!clickedInsideSidebar && !clickedHamburger) {
                sideNav.classList.remove('sidebar--open');
                const overlay = document.getElementById('dashboardSidebarOverlay') || document.getElementById('sidebar-overlay');
                if (overlay) overlay.classList.remove('active');
            }
        }
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

    /* ─────────────────────────────────────────────────────────
       CENTERED SEARCH BAR AUTOCOMPLETE SUGGESTIONS
    ───────────────────────────────────────────────────────── */
    const searchInput = document.getElementById('searchInput');
    const searchSuggestions = document.getElementById('searchSuggestions');

    const searchablePages = [
        { name: "Dashboard Overview", url: "/dashboard", icon: "dashboard" },
        { name: "Control Panel Center", url: "/control-panel", icon: "admin_panel_settings" },
        { name: "User / Customer Management", url: "/control-panel#people-mgmt", icon: "groups" },
        { name: "Employee Directory", url: "/control-panel#people-mgmt", icon: "badge" },
        { name: "Access & Roles Management", url: "/control-panel#people-mgmt", icon: "security" },
        { name: "Sales / Sell Ledger", url: "/control-panel#financial-mgmt", icon: "payments" },
        { name: "Property Listings", url: "/control-panel#property-mgmt", icon: "apartment" },
        { name: "System Audit Logs", url: "/control-panel#system-admin", icon: "settings_suggest" },
        { name: "Blacklist Registry", url: "/control-panel#system-admin", icon: "block" },
        { name: "Customer Support Tickets", url: "/control-panel#support-mgmt", icon: "support_agent" },
        { name: "Consultation Hub", url: "/consultation", icon: "chat_bubble" },
        { name: "Homepage", url: "/", icon: "home" },
        { name: "About LebEstates", url: "/about", icon: "info" }
    ];

    if (searchInput && searchSuggestions) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.toLowerCase().trim();
            searchSuggestions.innerHTML = ''; // clear suggestions

            if (query.length === 0) {
                searchSuggestions.style.display = 'none';
                return;
            }

            const matches = searchablePages.filter(page =>
                page.name.toLowerCase().includes(query)
            );

            if (matches.length === 0) {
                const emptyItem = document.createElement('div');
                emptyItem.className = 'search-suggestion-item';
                emptyItem.style.cursor = 'default';
                emptyItem.innerHTML = `
                    <span class="material-symbols-outlined">search_off</span>
                    <span>No results found</span>
                `;
                searchSuggestions.appendChild(emptyItem);
            } else {
                matches.forEach(match => {
                    const suggItem = document.createElement('a');
                    suggItem.href = match.url;
                    suggItem.className = 'search-suggestion-item';
                    suggItem.innerHTML = `
                        <span class="material-symbols-outlined">${match.icon}</span>
                        <span>${match.name}</span>
                    `;
                    searchSuggestions.appendChild(suggItem);
                });
            }

            searchSuggestions.style.display = 'flex';
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
                searchSuggestions.style.display = 'none';
            }
        });
    }

    /* ─────────────────────────────────────────────────────────
       USER PROFILE DROPDOWN MENU
    ───────────────────────────────────────────────────────── */
    const profileToggle = document.getElementById('profileDropdownToggle');
    const profileDropdown = document.getElementById('profileDropdown');

    if (profileToggle && profileDropdown) {
        profileToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            profileDropdown.classList.toggle('profile-dropdown--open');
        });

        document.addEventListener('click', (e) => {
            if (!profileToggle.contains(e.target)) {
                profileDropdown.classList.remove('profile-dropdown--open');
            }
        });
    }
});
