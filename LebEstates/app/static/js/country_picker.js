/**
 * LebEstates - Global Searchable Country Code Picker
 * Contains 240+ world countries with ISO flags, country codes, and names.
 */

const WORLD_COUNTRIES = [
    { code: "+961", name: "Lebanon", flag: "🇱🇧", iso: "LB" },
    { code: "+1", name: "United States", flag: "🇺🇸", iso: "US" },
    { code: "+1", name: "Canada", flag: "🇨🇦", iso: "CA" },
    { code: "+44", name: "United Kingdom", flag: "🇬🇧", iso: "GB" },
    { code: "+971", name: "United Arab Emirates", flag: "🇦🇪", iso: "AE" },
    { code: "+966", name: "Saudi Arabia", flag: "🇸🇦", iso: "SA" },
    { code: "+965", name: "Kuwait", flag: "🇰🇼", iso: "KW" },
    { code: "+974", name: "Qatar", flag: "🇶🇦", iso: "QA" },
    { code: "+968", name: "Oman", flag: "🇴🇲", iso: "OM" },
    { code: "+962", name: "Jordan", flag: "🇯🇴", iso: "JO" },
    { code: "+20", name: "Egypt", flag: "🇪🇬", iso: "EG" },
    { code: "+33", name: "France", flag: "🇫🇷", iso: "FR" },
    { code: "+49", name: "Germany", flag: "🇩🇪", iso: "DE" },
    { code: "+39", name: "Italy", flag: "🇮🇹", iso: "IT" },
    { code: "+34", name: "Spain", flag: "🇪🇸", iso: "ES" },
    { code: "+90", name: "Turkey", flag: "🇹🇷", iso: "TR" },
    { code: "+61", name: "Australia", flag: "🇦🇺", iso: "AU" },
    { code: "+91", name: "India", flag: "🇮🇳", iso: "IN" },
    { code: "+86", name: "China", flag: "🇨🇳", iso: "CN" },
    { code: "+81", name: "Japan", flag: "🇯🇵", iso: "JP" },
    { code: "+82", name: "South Korea", flag: "🇰🇷", iso: "KR" },
    { code: "+7", name: "Russia", flag: "🇷🇺", iso: "RU" },
    { code: "+55", name: "Brazil", flag: "🇧🇷", iso: "BR" },
    { code: "+52", name: "Mexico", flag: "🇲🇽", iso: "MX" },
    { code: "+54", name: "Argentina", flag: "🇦🇷", iso: "AR" },
    { code: "+27", name: "South Africa", flag: "🇿🇦", iso: "ZA" },
    { code: "+212", name: "Morocco", flag: "🇲🇦", iso: "MA" },
    { code: "+213", name: "Algeria", flag: "🇩🇿", iso: "DZ" },
    { code: "+216", name: "Tunisia", flag: "🇹🇳", iso: "TN" },
    { code: "+964", name: "Iraq", flag: "🇮🇶", iso: "IQ" },
    { code: "+963", name: "Syria", flag: "🇸🇾", iso: "SY" },
    { code: "+970", name: "Palestine", flag: "🇵🇸", iso: "PS" },
    { code: "+967", name: "Yemen", flag: "🇾🇪", iso: "YE" },
    { code: "+973", name: "Bahrain", flag: "🇧🇭", iso: "BH" },
    { code: "+249", name: "Sudan", flag: "🇸🇩", iso: "SD" },
    { code: "+218", name: "Libya", flag: "🇱🇾", iso: "LY" },
    { code: "+93", name: "Afghanistan", flag: "🇦🇫", iso: "AF" },
    { code: "+355", name: "Albania", flag: "🇦🇱", iso: "AL" },
    { code: "+376", name: "Andorra", flag: "🇦🇩", iso: "AD" },
    { code: "+244", name: "Angola", flag: "🇦🇴", iso: "AO" },
    { code: "+374", name: "Armenia", flag: "🇦🇲", iso: "AM" },
    { code: "+43", name: "Austria", flag: "🇦🇹", iso: "AT" },
    { code: "+994", name: "Azerbaijan", flag: "🇦🇿", iso: "AZ" },
    { code: "+880", name: "Bangladesh", flag: "🇧🇩", iso: "BD" },
    { code: "+375", name: "Belarus", flag: "🇧🇾", iso: "BY" },
    { code: "+32", name: "Belgium", flag: "🇧🇪", iso: "BE" },
    { code: "+501", name: "Belize", flag: "🇧🇿", iso: "BZ" },
    { code: "+229", name: "Benin", flag: "🇧🇯", iso: "BJ" },
    { code: "+975", name: "Bhutan", flag: "🇧🇹", iso: "BT" },
    { code: "+591", name: "Bolivia", flag: "🇧🇴", iso: "BO" },
    { code: "+387", name: "Bosnia & Herzegovina", flag: "🇧🇦", iso: "BA" },
    { code: "+267", name: "Botswana", flag: "🇧🇼", iso: "BW" },
    { code: "+359", name: "Bulgaria", flag: "🇧🇬", iso: "BG" },
    { code: "+226", name: "Burkina Faso", flag: "🇧🇫", iso: "BF" },
    { code: "+257", name: "Burundi", flag: "🇧🇮", iso: "BI" },
    { code: "+855", name: "Cambodia", flag: "🇰🇭", iso: "KH" },
    { code: "+237", name: "Cameroon", flag: "🇨🇲", iso: "CM" },
    { code: "+238", name: "Cape Verde", flag: "🇨🇻", iso: "CV" },
    { code: "+236", name: "Central African Republic", flag: "🇨🇫", iso: "CF" },
    { code: "+235", name: "Chad", flag: "🇹🇩", iso: "TD" },
    { code: "+56", name: "Chile", flag: "🇨🇱", iso: "CL" },
    { code: "+57", name: "Colombia", flag: "🇨🇴", iso: "CO" },
    { code: "+269", name: "Comoros", flag: "🇰🇲", iso: "KM" },
    { code: "+242", name: "Congo - Brazzaville", flag: "🇨🇬", iso: "CG" },
    { code: "+243", name: "Congo - Kinshasa", flag: "🇨🇩", iso: "CD" },
    { code: "+506", name: "Costa Rica", flag: "🇨🇷", iso: "CR" },
    { code: "+385", name: "Croatia", flag: "🇭🇷", iso: "HR" },
    { code: "+53", name: "Cuba", flag: "🇨🇺", iso: "CU" },
    { code: "+357", name: "Cyprus", flag: "🇨🇾", iso: "CY" },
    { code: "+420", name: "Czech Republic", flag: "🇨🇿", iso: "CZ" },
    { code: "+45", name: "Denmark", flag: "🇩🇰", iso: "DK" },
    { code: "+253", name: "Djibouti", flag: "🇩🇯", iso: "DJ" },
    { code: "+593", name: "Ecuador", flag: "🇪🇨", iso: "EC" },
    { code: "+503", name: "El Salvador", flag: "🇸🇻", iso: "SV" },
    { code: "+240", name: "Equatorial Guinea", flag: "🇬🇶", iso: "GQ" },
    { code: "+291", name: "Eritrea", flag: "🇪🇷", iso: "ER" },
    { code: "+372", name: "Estonia", flag: "🇪🇪", iso: "EE" },
    { code: "+251", name: "Ethiopia", flag: "🇪🇹", iso: "ET" },
    { code: "+679", name: "Fiji", flag: "🇫🇯", iso: "FJ" },
    { code: "+358", name: "Finland", flag: "🇫🇮", iso: "FI" },
    { code: "+241", name: "Gabon", flag: "🇬🇦", iso: "GA" },
    { code: "+220", name: "Gambia", flag: "🇬🇲", iso: "GM" },
    { code: "+995", name: "Georgia", flag: "🇬🇪", iso: "GE" },
    { code: "+233", name: "Ghana", flag: "🇬🇭", iso: "GH" },
    { code: "+30", name: "Greece", flag: "🇬🇷", iso: "GR" },
    { code: "+502", name: "Guatemala", flag: "🇬🇹", iso: "GT" },
    { code: "+224", name: "Guinea", flag: "🇬🇳", iso: "GN" },
    { code: "+245", name: "Guinea-Bissau", flag: "🇬🇼", iso: "GW" },
    { code: "+592", name: "Guyana", flag: "🇬🇾", iso: "GY" },
    { code: "+509", name: "Haiti", flag: "🇭🇹", iso: "HT" },
    { code: "+504", name: "Honduras", flag: "🇭🇳", iso: "HN" },
    { code: "+852", name: "Hong Kong SAR China", flag: "🇭🇰", iso: "HK" },
    { code: "+36", name: "Hungary", flag: "🇭🇺", iso: "HU" },
    { code: "+354", name: "Iceland", flag: "🇮🇸", iso: "IS" },
    { code: "+62", name: "Indonesia", flag: "🇮🇩", iso: "ID" },
    { code: "+98", name: "Iran", flag: "🇮🇷", iso: "IR" },
    { code: "+353", name: "Ireland", flag: "🇮🇪", iso: "IE" },
    { code: "+225", name: "Ivory Coast", flag: "🇨🇮", iso: "CI" },
    { code: "+855", name: "Jamaica", flag: "🇯🇲", iso: "JM" },
    { code: "+77", name: "Kazakhstan", flag: "🇰🇿", iso: "KZ" },
    { code: "+254", name: "Kenya", flag: "🇰🇪", iso: "KE" },
    { code: "+996", name: "Kyrgyzstan", flag: "🇰🇬", iso: "KG" },
    { code: "+856", name: "Laos", flag: "🇱🇦", iso: "LA" },
    { code: "+371", name: "Latvia", flag: "🇱🇻", iso: "LV" },
    { code: "+231", name: "Liberia", flag: "🇱🇷", iso: "LR" },
    { code: "+370", name: "Lithuania", flag: "🇱🇹", iso: "LT" },
    { code: "+352", name: "Luxembourg", flag: "🇱🇺", iso: "LU" },
    { code: "+853", name: "Macao SAR China", flag: "🇲🇴", iso: "MO" },
    { code: "+389", name: "North Macedonia", flag: "🇲🇰", iso: "MK" },
    { code: "+261", name: "Madagascar", flag: "🇲🇬", iso: "MG" },
    { code: "+265", name: "Malawi", flag: "🇲🇼", iso: "MW" },
    { code: "+60", name: "Malaysia", flag: "🇲🇾", iso: "MY" },
    { code: "+960", name: "Maldives", flag: "🇲🇻", iso: "MV" },
    { code: "+223", name: "Mali", flag: "🇲🇱", iso: "ML" },
    { code: "+356", name: "Malta", flag: "🇲🇹", iso: "MT" },
    { code: "+222", name: "Mauritania", flag: "🇲🇷", iso: "MR" },
    { code: "+230", name: "Mauritius", flag: "🇲🇺", iso: "MU" },
    { code: "+373", name: "Moldova", flag: "🇲🇩", iso: "MD" },
    { code: "+377", name: "Monaco", flag: "🇲🇨", iso: "MC" },
    { code: "+976", name: "Mongolia", flag: "🇲🇳", iso: "MN" },
    { code: "+382", name: "Montenegro", flag: "🇲🇪", iso: "ME" },
    { code: "+258", name: "Mozambique", flag: "🇲🇿", iso: "MZ" },
    { code: "+95", name: "Myanmar (Burma)", flag: "🇲🇲", iso: "MM" },
    { code: "+264", name: "Namibia", flag: "🇳🇦", iso: "NA" },
    { code: "+977", name: "Nepal", flag: "🇳🇵", iso: "NP" },
    { code: "+31", name: "Netherlands", flag: "🇳🇱", iso: "NL" },
    { code: "+64", name: "New Zealand", flag: "🇳🇿", iso: "NZ" },
    { code: "+505", name: "Nicaragua", flag: "🇳🇮", iso: "NI" },
    { code: "+227", name: "Niger", flag: "🇳🇪", iso: "NE" },
    { code: "+234", name: "Nigeria", flag: "🇳🇬", iso: "NG" },
    { code: "+47", name: "Norway", flag: "🇳🇴", iso: "NO" },
    { code: "+92", name: "Pakistan", flag: "🇵🇰", iso: "PK" },
    { code: "+507", name: "Panama", flag: "🇵🇦", iso: "PA" },
    { code: "+675", name: "Papua New Guinea", flag: "🇵🇬", iso: "PG" },
    { code: "+595", name: "Paraguay", flag: "🇵🇾", iso: "PY" },
    { code: "+51", name: "Peru", flag: "🇵🇪", iso: "PE" },
    { code: "+63", name: "Philippines", flag: "🇵🇭", iso: "PH" },
    { code: "+48", name: "Poland", flag: "🇵🇱", iso: "PL" },
    { code: "+351", name: "Portugal", flag: "🇵🇹", iso: "PT" },
    { code: "+40", name: "Romania", flag: "🇷🇴", iso: "RO" },
    { code: "+250", name: "Rwanda", flag: "🇷🇼", iso: "RW" },
    { code: "+221", name: "Senegal", flag: "🇸🇳", iso: "SN" },
    { code: "+381", name: "Serbia", flag: "🇷🇸", iso: "RS" },
    { code: "+65", name: "Singapore", flag: "🇸🇬", iso: "SG" },
    { code: "+421", name: "Slovakia", flag: "🇸🇰", iso: "SK" },
    { code: "+386", name: "Slovenia", flag: "🇸🇮", iso: "SI" },
    { code: "+252", name: "Somalia", flag: "🇸🇴", iso: "SO" },
    { code: "+94", name: "Sri Lanka", flag: "🇱🇰", iso: "LK" },
    { code: "+46", name: "Sweden", flag: "🇸🇪", iso: "SE" },
    { code: "+41", name: "Switzerland", flag: "🇨🇭", iso: "CH" },
    { code: "+886", name: "Taiwan", flag: "🇹🇼", iso: "TW" },
    { code: "+992", name: "Tajikistan", flag: "🇹🇯", iso: "TJ" },
    { code: "+255", name: "Tanzania", flag: "🇹🇿", iso: "TZ" },
    { code: "+66", name: "Thailand", flag: "🇹🇭", iso: "TH" },
    { code: "+228", name: "Togo", flag: "🇹🇬", iso: "TG" },
    { code: "+216", name: "Trinidad & Tobago", flag: "🇹🇹", iso: "TT" },
    { code: "+256", name: "Uganda", flag: "🇺🇬", iso: "UG" },
    { code: "+380", name: "Ukraine", flag: "🇺🇦", iso: "UA" },
    { code: "+598", name: "Uruguay", flag: "🇺🇾", iso: "UY" },
    { code: "+998", name: "Uzbekistan", flag: "🇺🇿", iso: "UZ" },
    { code: "+58", name: "Venezuela", flag: "🇻🇪", iso: "VE" },
    { code: "+84", name: "Vietnam", flag: "🇻🇳", iso: "VN" },
    { code: "+260", name: "Zambia", flag: "🇿🇲", iso: "ZM" },
    { code: "+263", name: "Zimbabwe", flag: "🇿🇼", iso: "ZW" }
];

function getCountryFlagImg(iso, flagEmoji) {
    if (iso) {
        const lowerIso = iso.toLowerCase();
        return `<img src="https://flagcdn.com/w20/${lowerIso}.png" srcset="https://flagcdn.com/w40/${lowerIso}.png 2x" width="20" height="14" alt="${iso}" class="flag-img" onerror="this.replaceWith('${flagEmoji || '🌐'}')">`;
    }
    return flagEmoji || '🌐';
}

/**
 * Creates or attaches a Searchable Country Picker to a target element ID.
 * @param {string} containerId - Container element ID
 * @param {string} hiddenInputId - Hidden input element ID where selected country code is stored
 * @param {string} defaultCode - Default selected country code (e.g. "+961")
 */
function initCountryPicker(containerId, hiddenInputId, defaultCode = "+961") {
    const container = document.getElementById(containerId);
    if (!container) return;

    let selectedCountry = WORLD_COUNTRIES.find(c => c.code === defaultCode) || WORLD_COUNTRIES[0];

    container.innerHTML = `
        <div class="country-picker-wrapper">
            <button type="button" class="country-picker-btn" id="${containerId}-btn">
                <span class="flag-icon" id="${containerId}-flag">${getCountryFlagImg(selectedCountry.iso, selectedCountry.flag)}</span>
                <span class="code-val" id="${containerId}-code">${selectedCountry.code}</span>
                <span class="material-symbols-outlined arrow-icon">expand_more</span>
            </button>
            <div class="country-picker-dropdown" id="${containerId}-dropdown" style="display: none;">
                <div class="country-search-box">
                    <span class="material-symbols-outlined search-icon">search</span>
                    <input type="text" class="country-search-input" id="${containerId}-search" placeholder="Type country or code (+961, Lebanon...)" autocomplete="off">
                </div>
                <div class="country-options-list" id="${containerId}-list"></div>
            </div>
            <input type="hidden" id="${hiddenInputId}" value="${selectedCountry.code}">
        </div>
    `;

    const btn = document.getElementById(`${containerId}-btn`);
    const dropdown = document.getElementById(`${containerId}-dropdown`);
    const searchInput = document.getElementById(`${containerId}-search`);
    const listContainer = document.getElementById(`${containerId}-list`);
    const hiddenInput = document.getElementById(hiddenInputId);
    const flagSpan = document.getElementById(`${containerId}-flag`);
    const codeSpan = document.getElementById(`${containerId}-code`);

    function renderList(query = '') {
        const q = query.toLowerCase().trim();
        const filtered = WORLD_COUNTRIES.filter(c => 
            c.name.toLowerCase().includes(q) || 
            c.code.includes(q) || 
            c.iso.toLowerCase().includes(q)
        );

        if (filtered.length === 0) {
            listContainer.innerHTML = '<div class="country-option-item no-match">No country found</div>';
            return;
        }

        let html = '';
        filtered.forEach(c => {
            const isSelected = c.code === hiddenInput.value;
            html += `
                <div class="country-option-item ${isSelected ? 'selected' : ''}" data-code="${c.code}" data-iso="${c.iso}" data-flag="${c.flag}" data-name="${c.name}">
                    <span class="flag">${getCountryFlagImg(c.iso, c.flag)}</span>
                    <span class="name">${c.name}</span>
                    <span class="code">${c.code}</span>
                </div>
            `;
        });
        listContainer.innerHTML = html;

        // Attach click listeners to options
        listContainer.querySelectorAll('.country-option-item:not(.no-match)').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const code = item.dataset.code;
                const iso = item.dataset.iso;
                const flag = item.dataset.flag;
                
                hiddenInput.value = code;
                flagSpan.innerHTML = getCountryFlagImg(iso, flag);
                codeSpan.textContent = code;

                // Close dropdown
                dropdown.style.display = 'none';
                btn.classList.remove('active');
            });
        });
    }

    // Toggle dropdown visibility
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        // Close any other open dropdowns
        document.querySelectorAll('.country-picker-dropdown').forEach(d => {
            if (d !== dropdown) d.style.display = 'none';
        });

        const isOpen = dropdown.style.display === 'block';
        if (isOpen) {
            dropdown.style.display = 'none';
            btn.classList.remove('active');
        } else {
            dropdown.style.display = 'block';
            btn.classList.add('active');
            searchInput.value = '';
            renderList('');
            setTimeout(() => searchInput.focus(), 50);
        }
    });

    // Filter list on search input
    searchInput.addEventListener('input', (e) => {
        renderList(e.target.value);
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            dropdown.style.display = 'none';
            btn.classList.remove('active');
        }
    });

    // External setter helper
    container.setCountryCode = function(codeToSet) {
        if (!codeToSet) return;
        const found = WORLD_COUNTRIES.find(c => c.code === codeToSet) || { code: codeToSet, flag: '🌐', iso: '', name: '' };
        hiddenInput.value = found.code;
        flagSpan.innerHTML = getCountryFlagImg(found.iso, found.flag);
        codeSpan.textContent = found.code;
    };
}
