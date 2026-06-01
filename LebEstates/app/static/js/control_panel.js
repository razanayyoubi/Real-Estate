/* -------------------------------------------------------------
   LEBESTATES ADMIN CONTROL PANEL CUSTOM JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // 1. COLLAPSIBLE SIDEBAR WITH BLURRED OVERLAY
    const sidebar = document.getElementById('sideNav');
    const hamburgerButton = document.getElementById('hamburgerButton');
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

    if (hamburgerButton) {
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

    // 2. CENTERED SEARCH BAR AUTOCOMPLETE SUGGESTIONS
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

    // 3. PROFILE DROPDOWN MENU
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

/**
 * Global Hierarchical Group Accordion Toggle Function
 * Exposed on `window` to support declarative inline HTML `onclick` callbacks safely.
 */
window.toggleGroup = function(id) {
    const groupElement = document.getElementById(id);
    if (!groupElement) return;

    if (groupElement.classList.contains('sidebar__group')) {
        groupElement.classList.toggle('sidebar__group--expanded');
    } else if (groupElement.classList.contains('sidebar__subgroup')) {
        groupElement.classList.toggle('sidebar__subgroup--expanded');
    }
};
