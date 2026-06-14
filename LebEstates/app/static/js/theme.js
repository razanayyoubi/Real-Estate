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

    const handleToggle = (e) => {
        e.stopPropagation();
        const sideNav = document.getElementById('sideNav');
        if (!sideNav) {
            // Toggle the mobile navigation drawer for customer/guest pages
            const navMenu = document.getElementById('nav-menu');
            if (navMenu && navMenu.classList.contains('active')) {
                closeSidebar();
            } else {
                openSidebar();
            }
            return;
        }

        const isDesktop = window.innerWidth > 1024;
        const isAdmin = !!document.querySelector('.admin-layout-wrapper');

        if (isDesktop && isAdmin) {
            document.body.classList.toggle('sidebar-collapsed');
        } else {
            // Mobile/Tablet sidebar toggle drawer behavior
            sideNav.classList.toggle('sidebar--open');
            const overlay = document.getElementById('dashboardSidebarOverlay') || document.getElementById('sidebar-overlay');
            if (overlay) overlay.classList.toggle('active');
        }
    };

    if (hamburger) {
        hamburger.addEventListener('click', handleToggle);
    }

    // Sidebar Close button
    if (sidebarClose) {
        sidebarClose.addEventListener('click', (e) => {
            e.stopPropagation();
            closeSidebar();
        });
    }

    // Toggle button closes the sidebar if it exists
    const toggleButton = document.getElementById('toggleButton');
    if (toggleButton) {
        toggleButton.addEventListener('click', handleToggle);
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

    function setupSearchAutocomplete(inputId, suggestionsId) {
        const inputEl = document.getElementById(inputId);
        const suggestionsEl = document.getElementById(suggestionsId);
        if (inputEl && suggestionsEl) {
            inputEl.addEventListener('input', () => {
                const query = inputEl.value.toLowerCase().trim();
                suggestionsEl.innerHTML = ''; // clear suggestions

                if (query.length === 0) {
                    suggestionsEl.style.display = 'none';
                    return;
                }

                // Check role: admin/employee sees admin pages, others don't
                const isAdmin = !!document.querySelector('.admin-layout-wrapper');
                let filteredPages = searchablePages;
                if (!isAdmin) {
                    filteredPages = searchablePages.filter(page => 
                        !page.url.startsWith('/dashboard') && !page.url.startsWith('/control-panel')
                    );
                }

                const matches = filteredPages.filter(page =>
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
                    suggestionsEl.appendChild(emptyItem);
                } else {
                    matches.forEach(match => {
                        const suggItem = document.createElement('a');
                        suggItem.href = match.url;
                        suggItem.className = 'search-suggestion-item';
                        suggItem.innerHTML = `
                            <span class="material-symbols-outlined">${match.icon}</span>
                            <span>${match.name}</span>
                        `;
                        suggestionsEl.appendChild(suggItem);
                    });
                }

                suggestionsEl.style.display = 'flex';
            });

            // Redirect on Enter
            inputEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const query = inputEl.value.trim();
                    if (query.length > 0) {
                        window.location.href = `/properties?q=${encodeURIComponent(query)}`;
                    }
                }
            });

            // Hide suggestions when clicking outside
            document.addEventListener('click', (e) => {
                if (!inputEl.contains(e.target) && !suggestionsEl.contains(e.target)) {
                    suggestionsEl.style.display = 'none';
                }
            });
        }
    }

    setupSearchAutocomplete('searchInput', 'searchSuggestions');
    setupSearchAutocomplete('searchInputMobile', 'searchSuggestionsMobile');

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
