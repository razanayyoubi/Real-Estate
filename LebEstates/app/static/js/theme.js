document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeToggleIcon = document.getElementById('theme-toggle-icon');

    // Function to set theme
    const setTheme = (theme) => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark-mode');
            if (themeToggleIcon) {
                themeToggleIcon.textContent = 'light_mode'; // Sun icon in dark mode
            }
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark-mode');
            if (themeToggleIcon) {
                themeToggleIcon.textContent = 'dark_mode'; // Moon icon in light mode
            }
            localStorage.setItem('theme', 'light');
        }
    };

    // Initialize based on localStorage or document class
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        // Fallback to check if dark-mode is already set via inline script
        const hasDarkMode = document.documentElement.classList.contains('dark-mode');
        setTheme(hasDarkMode ? 'dark' : 'light');
    }

    // Toggle button event listener
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.classList.contains('dark-mode') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Rich scale/rotate micro-interaction animation on click
            if (themeToggleIcon) {
                themeToggleIcon.style.transform = 'scale(0.3) rotate(90deg)';
                themeToggleIcon.style.opacity = '0';
            }
            
            setTimeout(() => {
                setTheme(newTheme);
                if (themeToggleIcon) {
                    themeToggleIcon.style.transform = 'scale(1) rotate(0deg)';
                    themeToggleIcon.style.opacity = '1';
                }
            }, 150);
        });
    }
});
