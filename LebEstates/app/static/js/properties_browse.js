/* -------------------------------------------------------------
   LEBESTATES BROWSE PROPERTIES MODULE INTERACTIVE JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    
    // Core Elements
    const propertiesGrid = document.getElementById('properties-grid');
    const propertyCards = Array.from(document.querySelectorAll('.property-card'));
    const propertiesCountSpan = document.getElementById('properties-count');
    
    // Filter Inputs
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('btn-search-trigger');
    const listingTypeSelect = document.getElementById('filter-listing-type');
    const locationSelect = document.getElementById('filter-location');
    const typeCheckboxes = document.querySelectorAll('.filter-type-checkbox');
    const priceMinInput = document.getElementById('filter-price-min');
    const priceMaxInput = document.getElementById('filter-price-max');
    const priceSlider = document.getElementById('filter-price-slider');
    const sliderMaxDisplay = document.getElementById('slider-max-display');
    const areaMinInput = document.getElementById('filter-area-min');
    const areaMaxInput = document.getElementById('filter-area-max');
    const roomsInput = document.getElementById('filter-rooms');
    const bathroomsInput = document.getElementById('filter-bathrooms');
    const floorInput = document.getElementById('filter-floor');
    const parkingSelect = document.getElementById('filter-parking');
    const amenityCheckboxes = document.querySelectorAll('.filter-amenity-checkbox');
    
    const applyFiltersBtn = document.getElementById('btn-apply-filters');
    const clearFiltersBtn = document.getElementById('btn-clear-filters');
    const sortSelect = document.getElementById('sort-select');

    // Details Modal Elements
    const detailsModal = document.getElementById('details-modal');
    const btnCloseDetailsModal = document.getElementById('btn-close-details-modal');
    const btnCloseDetailsBottom = document.getElementById('btn-close-details-bottom');

    // Empty state element helper
    let emptyStateEl = document.querySelector('.browse-empty-state');
    if (!emptyStateEl && propertiesGrid) {
        emptyStateEl = document.createElement('div');
        emptyStateEl.className = 'browse-empty-state';
        emptyStateEl.style.display = 'none';
        emptyStateEl.innerHTML = `
            <span class="material-symbols-outlined">inventory_2</span>
            <p>No properties match your current filters. Try relaxing some options.</p>
        `;
        propertiesGrid.appendChild(emptyStateEl);
    }

    /* ─────────────────────────────────────────────────────────
       1. SYNCHRONIZE PRICE SLIDER & INPUTS
    ───────────────────────────────────────────────────────── */
    const updatePriceInputsFromSlider = () => {
        const val = parseInt(priceSlider.value);
        sliderMaxDisplay.textContent = val.toLocaleString();
        priceMaxInput.value = val;
    };

    const updateSliderFromPriceInputs = () => {
        const maxVal = parseFloat(priceMaxInput.value);
        if (!isNaN(maxVal) && maxVal >= 0 && maxVal <= parseInt(priceSlider.max)) {
            priceSlider.value = maxVal;
            sliderMaxDisplay.textContent = maxVal.toLocaleString();
        } else if (priceMaxInput.value === '') {
            // default fallback to max slider if empty
            priceSlider.value = priceSlider.max;
            sliderMaxDisplay.textContent = parseInt(priceSlider.max).toLocaleString();
        }
    };

    if (priceSlider) {
        priceSlider.addEventListener('input', () => {
            updatePriceInputsFromSlider();
            applyFilters();
        });
    }

    if (priceMaxInput) {
        priceMaxInput.addEventListener('change', () => {
            updateSliderFromPriceInputs();
            applyFilters();
        });
    }

    if (priceMinInput) {
        priceMinInput.addEventListener('change', applyFilters);
    }

    /* ─────────────────────────────────────────────────────────
       2. APPLY FILTERING LOGIC
    ───────────────────────────────────────────────────────── */
    const applyFilters = () => {
        const query = searchInput.value.toLowerCase().trim();
        const selectedListingType = listingTypeSelect ? listingTypeSelect.value.toLowerCase() : 'all';
        const selectedLocation = locationSelect.value.toLowerCase();
        
        // Gather selected property types
        const checkedTypes = Array.from(typeCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value.toLowerCase());
            
        // Gather price range boundary
        const minPrice = parseFloat(priceMinInput.value) || 0;
        const maxPrice = parseFloat(priceMaxInput.value) || Infinity;

        // Gather area range boundary
        const minArea = parseFloat(areaMinInput.value) || 0;
        const maxArea = parseFloat(areaMaxInput.value) || Infinity;

        // Gather rooms, bathrooms, floor, parking
        const minRooms = parseInt(roomsInput.value) || 0;
        const minBathrooms = parseInt(bathroomsInput.value) || 0;
        const floorFilter = floorInput.value !== '' ? parseInt(floorInput.value) : null;
        const selectedParking = parkingSelect ? parkingSelect.value.toLowerCase() : 'any';
        
        // Gather selected amenities
        const checkedAmenities = Array.from(amenityCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value.toLowerCase());

        let visibleCount = 0;

        propertyCards.forEach(card => {
            const d = card.dataset;
            const title = d.title.toLowerCase();
            const desc = d.description.toLowerCase();
            const listingType = d.listingType ? d.listingType.toLowerCase() : '';
            const location = d.location.toLowerCase();
            const type = d.type.toLowerCase();
            const price = parseFloat(d.price) || 0;
            const area = parseFloat(d.area) || 0;
            const beds = parseInt(d.beds) || 0;
            const baths = parseInt(d.baths) || 0;
            const floor = d.floor !== 'None' && d.floor !== '' ? parseInt(d.floor) || 0 : 0;
            const parking = d.parking === 'true';
            
            // Search string matching
            const searchMatch = query === '' || 
                                title.includes(query) || 
                                desc.includes(query) || 
                                location.includes(query);
                                
            // Listing type matching
            const listingTypeMatch = selectedListingType === 'all' || listingType === selectedListingType;
            
            // Location dropdown matching
            const locationMatch = selectedLocation === 'all' || location === selectedLocation;
            
            // Property type matching
            const typeMatch = checkedTypes.length === 0 || checkedTypes.includes(type);
            
            // Pricing range matching
            const priceMatch = price >= minPrice && price <= maxPrice;

            // Area matching
            const areaMatch = area >= minArea && area <= maxArea;

            // Rooms & Bathrooms matching
            const roomsMatch = beds >= minRooms;
            const bathroomsMatch = baths >= minBathrooms;

            // Floor number matching
            const floorMatch = floorFilter === null || floor === floorFilter;

            // Parking matching
            const parkingMatch = selectedParking === 'any' || (selectedParking === 'available' && parking);
            
            // Amenities matching (search within description & details)
            let amenitiesMatch = true;
            if (checkedAmenities.length > 0) {
                checkedAmenities.forEach(amenity => {
                    if (amenity === 'sea') {
                        // check description keywords
                        const matchesSea = desc.includes('sea') || desc.includes('ocean') || title.includes('sea') || title.includes('ocean');
                        if (!matchesSea) amenitiesMatch = false;
                    } else if (amenity === 'pool') {
                        const matchesPool = desc.includes('pool') || title.includes('pool');
                        if (!matchesPool) amenitiesMatch = false;
                    } else if (amenity === 'historic') {
                        const matchesHistoric = desc.includes('historic') || desc.includes('heritage') || desc.includes('stone') || 
                                               title.includes('historic') || title.includes('heritage') || title.includes('stone');
                        if (!matchesHistoric) amenitiesMatch = false;
                    }
                });
            }

            // Combine all filter checks
            if (searchMatch && listingTypeMatch && locationMatch && typeMatch && priceMatch && areaMatch && roomsMatch && bathroomsMatch && floorMatch && parkingMatch && amenitiesMatch) {
                card.style.display = 'flex';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        // Update count display
        if (propertiesCountSpan) {
            propertiesCountSpan.textContent = visibleCount;
        }

        // Show/hide empty state message
        if (emptyStateEl) {
            emptyStateEl.style.display = (visibleCount === 0) ? 'block' : 'none';
        }
    };

    // Attach filter listeners
    if (applyFiltersBtn) applyFiltersBtn.addEventListener('click', applyFilters);
    if (listingTypeSelect) listingTypeSelect.addEventListener('change', applyFilters);
    if (locationSelect) locationSelect.addEventListener('change', applyFilters);
    if (parkingSelect) parkingSelect.addEventListener('change', applyFilters);

    const inputEvents = ['input', 'change'];
    const numericInputs = [priceMinInput, priceMaxInput, areaMinInput, areaMaxInput, roomsInput, bathroomsInput, floorInput];
    numericInputs.forEach(input => {
        if (input) {
            inputEvents.forEach(evt => input.addEventListener(evt, applyFilters));
        }
    });

    typeCheckboxes.forEach(cb => cb.addEventListener('change', applyFilters));
    amenityCheckboxes.forEach(cb => cb.addEventListener('change', applyFilters));

    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') applyFilters();
        });
    }
    if (searchBtn) searchBtn.addEventListener('click', applyFilters);

    /* ─────────────────────────────────────────────────────────
       3. CLEAR FILTERS LOGIC
    ───────────────────────────────────────────────────────── */
    const clearFilters = () => {
        searchInput.value = '';
        if (listingTypeSelect) listingTypeSelect.value = 'All';
        locationSelect.value = 'All';
        
        typeCheckboxes.forEach(cb => cb.checked = false);
        amenityCheckboxes.forEach(cb => cb.checked = false);
        
        priceMinInput.value = '';
        priceMaxInput.value = '';
        priceSlider.value = priceSlider.max;
        sliderMaxDisplay.textContent = parseInt(priceSlider.max).toLocaleString();

        if (areaMinInput) areaMinInput.value = '';
        if (areaMaxInput) areaMaxInput.value = '';
        if (roomsInput) roomsInput.value = '';
        if (bathroomsInput) bathroomsInput.value = '';
        if (floorInput) floorInput.value = '';
        if (parkingSelect) parkingSelect.value = 'Any';

        applyFilters();
    };

    if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearFilters);

    /* ─────────────────────────────────────────────────────────
       4. DYNAMIC SORTING
    ───────────────────────────────────────────────────────── */
    const sortProperties = () => {
        const criteria = sortSelect.value;
        
        // Sort cards array
        propertyCards.sort((a, b) => {
            const priceA = parseFloat(a.dataset.price) || 0;
            const priceB = parseFloat(b.dataset.price) || 0;
            
            const areaA = parseFloat(a.dataset.area) || 0;
            const areaB = parseFloat(b.dataset.area) || 0;
            
            const dateA = new Date(a.dataset.created);
            const dateB = new Date(b.dataset.created);

            if (criteria === 'price-desc') {
                return priceB - priceA;
            } else if (criteria === 'price-asc') {
                return priceA - priceB;
            } else if (criteria === 'area-desc') {
                return areaB - areaA;
            } else {
                // newest
                return dateB - dateA;
            }
        });

        // Re-append sorted cards in propertiesGrid container
        propertyCards.forEach(card => {
            // appendChild moves existing element to the end, effectively sorting them in place
            propertiesGrid.appendChild(card);
        });

        // Ensure empty state remains at the bottom of the grid
        if (emptyStateEl) {
            propertiesGrid.appendChild(emptyStateEl);
        }
    };

    if (sortSelect) {
        sortSelect.addEventListener('change', sortProperties);
    }

    /* ─────────────────────────────────────────────────────────
       5. INTERACTIVE FAVORITES TOGGLE
    ───────────────────────────────────────────────────────── */
    const favoriteBtns = document.querySelectorAll('.btn-favorite');
    favoriteBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            btn.classList.toggle('active-favorite');
            
            // Apply scale pop micro-interaction
            btn.style.transform = 'scale(1.2)';
            setTimeout(() => {
                btn.style.transform = 'scale(1)';
            }, 200);

            // Optional: ajax call to save user favorite could be added here
        });
    });

    /* ─────────────────────────────────────────────────────────
       6. VIEW DETAILS MODAL SERVICE
    ───────────────────────────────────────────────────────── */
    const detailsButtons = document.querySelectorAll('.btn-card-details');
    detailsButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            const card = document.querySelector(`.property-card[data-id="${id}"]`);
            if (!card) return;

            const d = card.dataset;

            // Bind values to details modal
            document.getElementById('details-modal-title').textContent = `#LEB-${id} - Exclusive Collection Details`;
            document.getElementById('details-title-text').textContent = d.title;
            document.getElementById('details-desc').textContent = d.description || 'No description available for this property.';
            
            const listingBadge = document.getElementById('details-listing-type');
            const cardBadgeType = card.querySelector('.badge-listing-type');
            listingBadge.textContent = cardBadgeType ? cardBadgeType.textContent.trim().toUpperCase() : 'FOR SALE';
            
            const statusBadge = document.getElementById('details-status');
            statusBadge.textContent = 'AVAILABLE';
            statusBadge.className = 'status-badge badge-published';
            
            const priceNum = parseFloat(d.price) || 0;
            document.getElementById('details-price-text').textContent = `$${priceNum.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
            
            document.getElementById('details-beds').textContent = d.beds;
            document.getElementById('details-baths').textContent = d.baths;
            document.getElementById('details-area').textContent = d.area;
            document.getElementById('details-floor').textContent = d.floor || 'N/A';
            document.getElementById('details-parking').textContent = d.parking === 'true' ? 'Available' : 'None';
            document.getElementById('details-property-type').textContent = d.type;
            
            document.getElementById('details-location').textContent = d.location;
            document.getElementById('details-address').textContent = d.address || 'N/A';
            document.getElementById('details-lat').textContent = d.latitude || 'N/A';
            document.getElementById('details-lng').textContent = d.longitude || 'N/A';

            // Populate hero image and gallery thumbnails
            const heroImg = document.getElementById('details-hero-img');
            const heroContainer = document.querySelector('.details-hero-container');
            const galleryContainer = document.getElementById('details-gallery');
            
            galleryContainer.innerHTML = '';

            if (d.imageUrls && d.imageUrls.trim() !== '') {
                const urls = d.imageUrls.split(',');
                
                heroContainer.style.display = 'block';
                heroImg.src = urls[0];

                urls.forEach((url, index) => {
                    const img = document.createElement('img');
                    img.src = url;
                    img.alt = d.title;
                    if (index === 0) {
                        img.classList.add('active-thumb');
                    }

                    // Gallery thumbnails interactive listener
                    img.addEventListener('click', () => {
                        heroImg.src = url;
                        galleryContainer.querySelectorAll('img').forEach(t => t.classList.remove('active-thumb'));
                        img.classList.add('active-thumb');
                    });

                    galleryContainer.appendChild(img);
                });
            } else {
                heroContainer.style.display = 'none';
                galleryContainer.innerHTML = `
                    <div class="details-gallery-empty">
                        <span class="material-symbols-outlined">image</span>
                        <span>No images available for this listing</span>
                    </div>
                `;
            }

            // Open details modal overlay
            detailsModal.classList.remove('hidden');
        });
    });

    const closeDetails = () => {
        detailsModal.classList.add('hidden');
    };

    if (btnCloseDetailsModal) btnCloseDetailsModal.addEventListener('click', closeDetails);
    if (btnCloseDetailsBottom) btnCloseDetailsBottom.addEventListener('click', closeDetails);

    // Dismiss modal on backdrop click
    window.addEventListener('click', (e) => {
        if (e.target === detailsModal) closeDetails();
    });

    // Run sort on page load to match default filter selection
    sortProperties();
});
