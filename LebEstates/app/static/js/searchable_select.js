/**
 * LebEstates - Searchable Select Component
 * Converts standard <select> elements into searchable dropdowns.
 */
document.addEventListener('DOMContentLoaded', () => {
    initSearchableSelects();
});

function initSearchableSelects() {
    document.querySelectorAll('select.searchable-select').forEach(select => {
        if (select.dataset.searchableInitialized) return;
        select.dataset.searchableInitialized = 'true';

        // Wrap select element
        const wrapper = document.createElement('div');
        wrapper.className = 'searchable-select-wrapper';
        wrapper.style.position = 'relative';
        wrapper.style.width = '100%';

        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
        select.style.display = 'none';

        // Create search input UI
        const input = document.createElement('input');
        input.type = 'text';
        input.className = select.className.replace('searchable-select', '') + ' searchable-input';
        input.placeholder = select.getAttribute('data-placeholder') || 'Search & select...';
        input.style.width = '100%';
        input.style.cursor = 'pointer';

        // Set initial selected text
        const selectedOpt = select.options[select.selectedIndex];
        if (selectedOpt && selectedOpt.value) {
            input.value = selectedOpt.text;
        }

        // Create dropdown list
        const dropdown = document.createElement('div');
        dropdown.className = 'searchable-select-dropdown';
        dropdown.style.display = 'none';
        dropdown.style.position = 'absolute';
        dropdown.style.top = '100%';
        dropdown.style.left = '0';
        dropdown.style.right = '0';
        dropdown.style.maxHeight = '220px';
        dropdown.style.overflowY = 'auto';
        dropdown.style.zIndex = '999999';
        dropdown.style.background = 'var(--surface-container-lowest, #ffffff)';
        dropdown.style.border = '1px solid var(--outline-variant, #c5c6cf)';
        dropdown.style.borderRadius = '8px';
        dropdown.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';

        wrapper.appendChild(input);
        wrapper.appendChild(dropdown);

        function populateDropdown(filterText = '') {
            dropdown.innerHTML = '';
            const q = filterText.toLowerCase();
            let count = 0;

            Array.from(select.options).forEach(opt => {
                if (opt.value === '' && opt.text.startsWith('--')) return;
                const text = opt.text;
                if (!q || text.toLowerCase().includes(q)) {
                    count++;
                    const item = document.createElement('div');
                    item.className = 'searchable-option-item';
                    item.textContent = text;
                    item.style.padding = '10px 14px';
                    item.style.cursor = 'pointer';
                    item.style.fontSize = '14px';
                    item.style.color = 'var(--on-surface)';
                    if (opt.selected) {
                        item.style.background = 'var(--surface-container-high, #dee9fc)';
                        item.style.fontWeight = '700';
                    }

                    item.addEventListener('mouseenter', () => {
                        item.style.background = 'var(--surface-container-high, #dee9fc)';
                    });
                    item.addEventListener('mouseleave', () => {
                        if (!opt.selected) item.style.background = 'transparent';
                    });

                    item.addEventListener('click', () => {
                        select.value = opt.value;
                        input.value = text;
                        dropdown.style.display = 'none';
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                    });

                    dropdown.appendChild(item);
                }
            });

            if (count === 0) {
                const noResult = document.createElement('div');
                noResult.textContent = 'No matching options found';
                noResult.style.padding = '10px 14px';
                noResult.style.color = 'var(--on-surface-variant)';
                noResult.style.fontSize = '13px';
                dropdown.appendChild(noResult);
            }
        }

        input.addEventListener('focus', () => {
            populateDropdown('');
            dropdown.style.display = 'block';
        });

        input.addEventListener('input', (e) => {
            populateDropdown(e.target.value);
            dropdown.style.display = 'block';
        });

        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                dropdown.style.display = 'none';
                const curOpt = select.options[select.selectedIndex];
                if (curOpt) input.value = curOpt.text;
            }
        });
    });
}
