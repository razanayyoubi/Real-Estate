document.addEventListener('DOMContentLoaded', () => {
    // Micro-interaction for the search bar focus states
    const searchInputs = document.querySelectorAll('input, select');
    searchInputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.style.transform = 'scale(1.02)';
            input.parentElement.style.transition = 'all 0.3s ease';
        });
        input.addEventListener('blur', () => {
            input.parentElement.style.transform = 'scale(1)';
        });
    });

    // Atmospheric parallax-like scroll effect for the hero
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const heroBg = document.querySelector('.hero-bg-slideshow');
        if (heroBg) {
            heroBg.style.transform = `translateY(${scrolled * 0.4}px)`;
        }
    });

    // Search button redirect logic
    const searchBtn = document.getElementById('search-submit-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const propType = document.getElementById('search-property-type').value;
            const listingType = document.getElementById('search-listing-type').value;
            const location = document.getElementById('search-location').value.trim();
            const priceRange = document.getElementById('search-price-range').value;

            let queryParams = [];

            if (propType !== 'All') {
                queryParams.push(`property_types=${encodeURIComponent(propType)}`);
            }
            if (listingType !== 'All') {
                queryParams.push(`listing_type=${encodeURIComponent(listingType)}`);
            }
            if (location) {
                queryParams.push(`q=${encodeURIComponent(location)}`); // Use q parameter to match browse route search query
            }
            if (priceRange !== 'All') {
                const parts = priceRange.split('-');
                if (parts[0]) queryParams.push(`price_min=${parts[0]}`);
                if (parts[1] && parts[1] !== 'max') queryParams.push(`price_max=${parts[1]}`);
            }

            const url = '/properties' + (queryParams.length > 0 ? '?' + queryParams.join('&') : '');
            window.location.href = url;
        });
    }
});
