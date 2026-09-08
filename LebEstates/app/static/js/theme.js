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
        { name: "User / Customer Management", url: "/customers/", icon: "groups" },
        { name: "Employee Directory", url: "/employees/", icon: "badge" },
        { name: "Access & Roles Management", url: "/roles/", icon: "security" },
        { name: "Property Inventory / Listings", url: "/control-panel/properties", icon: "apartment" },
        { name: "Public Property Browse", url: "/properties", icon: "search" },
        { name: "System Audit Logs", url: "/control-panel/audit-logs/", icon: "settings_suggest" },
        { name: "Blacklist Registry", url: "/blacklist/", icon: "block" },
        { name: "Visits Management", url: "/control-panel/visits", icon: "calendar_month" },
        { name: "Transactions Hub", url: "/control-panel/transactions", icon: "payments" },
        { name: "Sales / Transaction Ledger", url: "/control-panel/transactions/ledger", icon: "menu_book" },
        { name: "Revenue Dashboard", url: "/control-panel/transactions/revenue-dashboard", icon: "monitoring" },
        { name: "Payment Tracking", url: "/control-panel/transactions/payment-tracking", icon: "account_balance_wallet" },
        { name: "Agent Commissions", url: "/control-panel/commissions", icon: "percent" },
        { name: "Commission Settings", url: "/control-panel/commission-settings", icon: "settings" },
        { name: "Monthly Payroll / Salaries", url: "/control-panel/salaries", icon: "monetization_on" },
        { name: "Consultation Hub", url: "/consultation", icon: "chat_bubble" },
        { name: "Homepage", url: "/", icon: "home" },
        { name: "About LebEstates", url: "/about", icon: "info" },
        { name: "Contact Us", url: "/contact", icon: "contact_support" },
        { name: "My Favorites", url: "/favorites", icon: "favorite" }
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
                const roleEl = document.querySelector('.header__profile-role');
                const role = roleEl ? roleEl.textContent.trim().toLowerCase() : '';
                const isAdmin = ['admin', 'employee', 'accountant'].includes(role);
                
                let filteredPages = searchablePages;
                if (!isAdmin) {
                    filteredPages = searchablePages.filter(page => 
                        !page.url.startsWith('/dashboard') && 
                        !page.url.startsWith('/control-panel') &&
                        !page.url.startsWith('/customers') &&
                        !page.url.startsWith('/employees') &&
                        !page.url.startsWith('/roles') &&
                        !page.url.startsWith('/blacklist')
                    );
                }

                const matches = filteredPages.filter(page =>
                    page.name.toLowerCase().includes(query)
                );

                if (matches.length > 0) {
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

                // Fetch dynamic suggestions from backend
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (inputEl.value.toLowerCase().trim() === query) {
                            const existingUrls = new Set(matches.map(m => m.url));
                            const uniqueDynamic = data.filter(item => !existingUrls.has(item.url));
                            
                            uniqueDynamic.forEach(match => {
                                const suggItem = document.createElement('a');
                                suggItem.href = match.url;
                                suggItem.className = 'search-suggestion-item';
                                suggItem.innerHTML = `
                                    <span class="material-symbols-outlined">${match.icon}</span>
                                    <span>${match.name}</span>
                                `;
                                suggestionsEl.appendChild(suggItem);
                            });

                            if (matches.length === 0 && uniqueDynamic.length === 0) {
                                suggestionsEl.innerHTML = '';
                                const emptyItem = document.createElement('div');
                                emptyItem.className = 'search-suggestion-item';
                                emptyItem.style.cursor = 'default';
                                emptyItem.innerHTML = `
                                    <span class="material-symbols-outlined">search_off</span>
                                    <span>No results found</span>
                                `;
                                suggestionsEl.appendChild(emptyItem);
                            }
                        }
                    })
                    .catch(err => console.error('Error fetching dynamic search results:', err));

                suggestionsEl.style.display = 'flex';
            });

            // Redirect on Enter
            inputEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const firstSuggestion = suggestionsEl.querySelector('.search-suggestion-item:not([style*="cursor: default"])');
                    if (firstSuggestion && firstSuggestion.href) {
                        window.location.href = firstSuggestion.href;
                    } else {
                        const query = inputEl.value.trim();
                        if (query.length > 0) {
                            const roleEl = document.querySelector('.header__profile-role');
                            const role = roleEl ? roleEl.textContent.trim().toLowerCase() : '';
                            const isAdmin = ['admin', 'employee', 'accountant'].includes(role);
                            if (isAdmin) {
                                window.location.href = `/control-panel/properties?q=${encodeURIComponent(query)}`;
                            } else {
                                window.location.href = `/properties?q=${encodeURIComponent(query)}`;
                            }
                        }
                    }
                }
            });

            // Click search icon functionality
            const searchIcon = inputEl.parentElement.querySelector('.header__search-icon');
            if (searchIcon) {
                searchIcon.style.cursor = 'pointer';
                searchIcon.addEventListener('click', () => {
                    const firstSuggestion = suggestionsEl.querySelector('.search-suggestion-item:not([style*="cursor: default"])');
                    if (firstSuggestion && firstSuggestion.href) {
                        window.location.href = firstSuggestion.href;
                    } else {
                        const query = inputEl.value.trim();
                        if (query.length > 0) {
                            const roleEl = document.querySelector('.header__profile-role');
                            const role = roleEl ? roleEl.textContent.trim().toLowerCase() : '';
                            const isAdmin = ['admin', 'employee', 'accountant'].includes(role);
                            if (isAdmin) {
                                window.location.href = `/control-panel/properties?q=${encodeURIComponent(query)}`;
                            } else {
                                window.location.href = `/properties?q=${encodeURIComponent(query)}`;
                            }
                        }
                    }
                });
            }

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
       SIDEBAR "POST NEW PROPERTY" CTA REDIRECT
       ───────────────────────────────────────────────────────── */
    const postPropertyBtn = document.getElementById('sidebarPostPropertyBtn');
    if (postPropertyBtn) {
        postPropertyBtn.addEventListener('click', () => {
            window.location.href = '/sell-rent';
        });
    }

    /* ─────────────────────────────────────────────────────────
       NOTIFICATION BADGE & DROPDOWN MANAGEMENT
    ───────────────────────────────────────────────────────── */
    const bellBtn = document.getElementById('notificationBellBtn');
    const dropdown = document.getElementById('notificationDropdown');
    const badge = document.getElementById('notificationBadge');
    const list = document.getElementById('notificationList');
    const markAllBtn = document.getElementById('markAllReadBtn');

    if (bellBtn) {
        // Fetch unread count to show badge
        function updateUnreadCount() {
            fetch('/api/notifications/unread-count')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const count = data.count;
                        if (count > 0) {
                            badge.textContent = count;
                            badge.classList.add('notification-badge--visible');
                        } else {
                            badge.classList.remove('notification-badge--visible');
                        }
                    }
                })
                .catch(err => console.error('Error fetching unread notification count:', err));
        }

        // Fetch and render notification list
        function loadNotifications() {
            fetch('/api/notifications')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const notifs = data.notifications;
                        list.innerHTML = '';
                        if (notifs.length === 0) {
                            list.innerHTML = `
                                <div class="notification-empty">
                                    <span class="material-symbols-outlined notification-empty__icon">notifications_off</span>
                                    <p class="notification-empty__text">No notifications yet.</p>
                                </div>
                            `;
                            return;
                        }

                        notifs.forEach(n => {
                            const item = document.createElement('div');
                            item.className = `notification-item ${n.isRead ? '' : 'unread'}`;

                            item.innerHTML = `
                                <div class="notification-item__message">
                                    ${n.message}
                                </div>
                                <div class="notification-item__date">
                                    ${n.createdAt}
                                </div>
                            `;

                            item.addEventListener('click', () => {
                                fetch(`/api/notifications/${n.notificationID}/read`, { method: 'POST' })
                                    .then(() => {
                                        updateUnreadCount();
                                        if (n.actionURL) {
                                            window.location.href = n.actionURL;
                                        } else {
                                            loadNotifications();
                                        }
                                    });
                            });

                            list.appendChild(item);
                        });
                    }
                })
                .catch(err => console.error('Error loading notifications:', err));
        }

        // Bell click toggle
        bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = !dropdown.classList.contains('notification-dropdown--open');
            dropdown.classList.toggle('notification-dropdown--open', isHidden);
            if (isHidden) {
                loadNotifications();
            }
        });

        // Close on clicking outside
        document.addEventListener('click', (e) => {
            if (dropdown.classList.contains('notification-dropdown--open') && !dropdown.contains(e.target) && e.target !== bellBtn) {
                dropdown.classList.remove('notification-dropdown--open');
            }
        });

        // Mark all read
        if (markAllBtn) {
            markAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fetch('/api/notifications/read-all', { method: 'POST' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            updateUnreadCount();
                            loadNotifications();
                        }
                    });
            });
        }

        // Initial load
        updateUnreadCount();

        // Poll for updates every 15s
        setInterval(updateUnreadCount, 15000);
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

/* ─────────────────────────────────────────────────────────
   GLOBAL UNIFIED TABLE PAGINATION HELPER
───────────────────────────────────────────────────────── */
window.initTablePagination = function(tableBodyOrId, rowSelector, infoId, buttonsId, perPage = 10) {
    const tableBody = typeof tableBodyOrId === 'string' ? document.getElementById(tableBodyOrId) : tableBodyOrId;
    const infoContainer = document.getElementById(infoId);
    const buttonsContainer = document.getElementById(buttonsId);
    if (!tableBody || !buttonsContainer) return function() {};

    let currentPage = 1;

    function renderPage() {
        const rows = Array.from(tableBody.querySelectorAll(rowSelector));
        const matchingRows = rows.filter(r => !r.classList.contains('filter-hidden'));
        
        const totalEntries = matchingRows.length;
        const totalPages = Math.max(1, Math.ceil(totalEntries / perPage));
        if (currentPage > totalPages) currentPage = totalPages;
        if (currentPage < 1) currentPage = 1;

        rows.forEach(r => {
            if (r.classList.contains('filter-hidden')) {
                r.style.display = 'none';
            }
        });

        const startIdx = (currentPage - 1) * perPage;
        const endIdx = startIdx + perPage;

        matchingRows.forEach((r, idx) => {
            if (idx >= startIdx && idx < endIdx) {
                r.style.display = '';
            } else {
                r.style.display = 'none';
            }
        });

        if (infoContainer) {
            if (totalEntries === 0) {
                infoContainer.textContent = "Showing 0 to 0 of 0 entries";
            } else {
                const start = startIdx + 1;
                const end = Math.min(endIdx, totalEntries);
                infoContainer.textContent = `Showing ${start} to ${end} of ${totalEntries} entries`;
            }
        }

        buttonsContainer.innerHTML = '';
        if (totalPages <= 1) return;

        const prevBtn = document.createElement('button');
        prevBtn.className = 'btn-page';
        prevBtn.textContent = 'Previous';
        prevBtn.disabled = (currentPage === 1);
        prevBtn.onclick = (e) => {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                renderPage();
            }
        };
        buttonsContainer.appendChild(prevBtn);

        for (let i = 1; i <= totalPages; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `btn-page ${i === currentPage ? 'active' : ''}`;
            pageBtn.textContent = i;
            pageBtn.onclick = (e) => {
                e.preventDefault();
                currentPage = i;
                renderPage();
            };
            buttonsContainer.appendChild(pageBtn);
        }

        const nextBtn = document.createElement('button');
        nextBtn.className = 'btn-page';
        nextBtn.textContent = 'Next';
        nextBtn.disabled = (currentPage === totalPages);
        nextBtn.onclick = (e) => {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                renderPage();
            }
        };
        buttonsContainer.appendChild(nextBtn);
    }

    renderPage();
    return renderPage;
};

