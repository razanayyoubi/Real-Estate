/* -------------------------------------------------------------
   LEBESTATES ADMIN DASHBOARD CUSTOM JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const sidebar = document.getElementById('sideNav');
    const mainContent = document.getElementById('mainContent');
    const toggleButton = document.getElementById('toggleButton');
    const toggleIcon = document.getElementById('toggleIcon');
    
    // Select brand text container to hide text but keep the icon visible when collapsed
    const brandText = document.querySelector('.sidebar__brand-text');
    const navLabels = document.querySelectorAll('.sidebar__nav-label');
    const ctaContainer = document.querySelector('.sidebar__cta-container');
    const ctaLabel = document.querySelector('.sidebar__cta-label');

    let isCollapsed = false;

    // Sidebar Toggling logic
    function toggleSidebar() {
        isCollapsed = !isCollapsed;

        if (isCollapsed) {
            // Collapse sidebar
            sidebar.classList.add('sidebar--collapsed');
            mainContent.classList.add('main-content--collapsed');
            
            // Hide navigation labels & brand text
            navLabels.forEach(label => label.classList.add('hidden'));
            if (brandText) brandText.classList.add('hidden');
            if (ctaLabel) ctaLabel.classList.add('hidden');
            if (ctaContainer) ctaContainer.classList.add('collapsed-cta');
            
            // Set menu icons
            if (toggleIcon) toggleIcon.innerText = 'menu';
        } else {
            // Expand sidebar
            sidebar.classList.remove('sidebar--collapsed');
            mainContent.classList.remove('main-content--collapsed');
            
            // Show navigation labels & brand text with slight delay for visual smoothness
            setTimeout(() => {
                navLabels.forEach(label => label.classList.remove('hidden'));
                if (brandText) brandText.classList.remove('hidden');
                if (ctaLabel) ctaLabel.classList.remove('hidden');
            }, 100);
            
            if (ctaContainer) ctaContainer.classList.remove('collapsed-cta');
            if (toggleIcon) toggleIcon.innerText = 'menu_open';
        }
    }

    // Attach Toggle Button listener
    if (toggleButton) {
        toggleButton.addEventListener('click', toggleSidebar);
    }

    // Interactive Chart Toggle Simulation (Volume vs Value)
    const toggleButtons = document.querySelectorAll('.toggle-btn');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            toggleButtons.forEach(b => b.classList.remove('toggle-btn--active'));
            e.currentTarget.classList.add('toggle-btn--active');
            
            // Simulate data reload animation
            const chartBars = document.querySelectorAll('.chart-bar');
            chartBars.forEach(bar => {
                const originalHeight = bar.style.height || bar.parentElement.style.getPropertyValue('--bar-height') || '50%';
                bar.style.height = '0%';
                setTimeout(() => {
                    bar.style.height = originalHeight;
                }, 100);
            });
        });
    });

    // Auto-adjust layout on smaller screens initially
    function handleResize() {
        if (window.innerWidth <= 1024 && !isCollapsed) {
            isCollapsed = false;
            toggleSidebar(); // Force collapse on tablet and smaller
        }
    }

    window.addEventListener('resize', handleResize);
    
    // Initial check
    handleResize();
});
