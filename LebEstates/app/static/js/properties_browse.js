/* -------------------------------------------------------------
   LEBESTATES BROWSE PROPERTIES MODULE INTERACTIVE JAVASCRIPT
   ------------------------------------------------------------- */

const init = () => {

    // Core Elements
    const propertiesGrid = document.getElementById('properties-grid');
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

    const applyFiltersBtn = document.getElementById('btn-apply-filters');
    const clearFiltersBtn = document.getElementById('btn-clear-filters');
    const sortSelect = document.getElementById('sort-select');

    // Details Modal Elements
    const detailsModal = document.getElementById('details-modal');
    const btnCloseDetailsModal = document.getElementById('btn-close-details-modal');
    const btnCloseDetailsBottom = document.getElementById('btn-close-details-bottom');

    // Load More Elements & State
    const loadMoreContainer = document.getElementById('load-more-container');
    const btnLoadMore = document.getElementById('btn-load-more');
    
    let offset = 6;
    const limit = 6;
    let totalCount = parseInt(propertiesCountSpan ? propertiesCountSpan.textContent : '0') || 0;

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
       1. SERVER-SIDE FETCHING & RENDERING LOGIC
    ───────────────────────────────────────────────────────── */
    
    const createPropertyCardHtml = (prop) => {
        // Format price
        const formattedPrice = Number(prop.price).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
        const priceSuffix = prop.listingType === 'Rent' ? '/mo' : '';
        
        // Format area
        const formattedArea = Number(prop.area).toFixed(0);
        
        // Image handling
        let imageHtml = '';
        if (prop.images && prop.images.length > 0) {
            imageHtml = `<img class="card-img" src="${prop.images[0].imageURL}" alt="${prop.title}" />`;
        } else {
            imageHtml = `
                <div class="card-img-placeholder">
                    <span class="material-symbols-outlined">image</span>
                </div>
            `;
        }
        
        // Badge exclusive
        const exclusiveBadge = Number(prop.price) > 1000000 
            ? `<span class="card-badge badge-exclusive">Exclusive</span>`
            : '';
            
        // Favorite active class
        const favoriteClass = prop.is_favorited ? 'active-favorite' : '';
        
        // Image URLs list for details modal
        const imageUrls = prop.images ? prop.images.map(img => img.imageURL).join(',') : '';
        
        return `
            <div class="property-card" data-id="${prop.propertyID}" data-title="${prop.title}"
                data-price="${prop.price}" data-type="${prop.propertyType}"
                data-listing-type="${prop.listingType}" data-location="${prop.location}"
                data-created="${prop.createdAt}" data-beds="${prop.rooms || 0}"
                data-baths="${prop.bathrooms || 0}" data-area="${prop.area}"
                data-floor="${prop.floorNumber || 0}"
                data-parking="${prop.parkingAvailable ? 'true' : 'false'}"
                data-address="${prop.address || ''}" data-latitude="${prop.latitude || ''}"
                data-longitude="${prop.longitude || ''}" data-description="${prop.description || ''}"
                data-owner-id="${prop.ownerID}" data-creator-id="${prop.createdBy}"
                data-image-urls="${imageUrls}">

                <div class="card-image-wrapper">
                    ${imageHtml}
                    <div class="card-badge-container">
                        ${exclusiveBadge}
                        <span class="card-badge badge-listing-type">For ${prop.listingType}</span>
                    </div>
                    <button type="button" class="btn-favorite ${favoriteClass}" data-id="${prop.propertyID}" title="Add to Favorites">
                        <span class="material-symbols-outlined">favorite</span>
                    </button>
                    <div class="card-title-overlay">
                        <h3 class="card-title">${prop.title}</h3>
                        <p class="card-location">
                            <span class="material-symbols-outlined">location_on</span> ${prop.location}
                        </p>
                    </div>
                </div>

                <div class="card-content">
                    <div class="card-price-specs">
                        <span class="card-price">$${formattedPrice}${priceSuffix}</span>
                        <div class="card-specs">
                            <span class="spec-item" title="Beds"><span
                                    class="material-symbols-outlined">bed</span> ${prop.rooms || 0}</span>
                            <span class="spec-item" title="Baths"><span
                                    class="material-symbols-outlined">bathtub</span> ${prop.bathrooms || 0}</span>
                            <span class="spec-item" title="Area"><span
                                    class="material-symbols-outlined">square_foot</span> ${formattedArea}m²</span>
                        </div>
                    </div>
                    <div class="card-buttons">
                        <button type="button" class="btn-card-action btn-card-details"
                            data-id="${prop.propertyID}">View Details</button>
                        <button type="button" class="btn-card-action btn-card-visit"
                            data-id="${prop.propertyID}">Request Visit</button>
                    </div>
                </div>
            </div>
        `;
    };

    const fetchProperties = (isAppend = false) => {
        if (!isAppend) {
            offset = 0;
        }

        // Gather all current filter values
        const query = searchInput ? searchInput.value.trim() : '';
        const selectedListingType = listingTypeSelect ? listingTypeSelect.value : 'All';
        const selectedLocation = locationSelect ? locationSelect.value : 'All';

        const checkedTypes = Array.from(typeCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        const minPrice = priceMinInput ? priceMinInput.value : '';
        const maxPrice = priceMaxInput ? priceMaxInput.value : '';

        const minArea = areaMinInput ? areaMinInput.value : '';
        const maxArea = areaMaxInput ? areaMaxInput.value : '';

        const minRooms = roomsInput ? roomsInput.value : '';
        const minBathrooms = bathroomsInput ? bathroomsInput.value : '';
        const floorFilter = floorInput ? floorInput.value : '';
        const selectedParking = parkingSelect ? parkingSelect.value : 'Any';
        const sortOrder = sortSelect ? sortSelect.value : 'newest';

        const payload = {
            q: query,
            listing_type: selectedListingType,
            location: selectedLocation,
            property_types: checkedTypes,
            price_min: minPrice,
            price_max: maxPrice,
            area_min: minArea,
            area_max: maxArea,
            rooms: minRooms,
            bathrooms: minBathrooms,
            floor: floorFilter,
            parking: selectedParking,
            sort: sortOrder,
            offset: offset,
            limit: limit
        };

        if (btnLoadMore) btnLoadMore.disabled = true;

        fetch('/properties/api/list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (btnLoadMore) btnLoadMore.disabled = false;

            if (data && data.success) {
                totalCount = data.total_count;
                if (propertiesCountSpan) {
                    propertiesCountSpan.textContent = totalCount;
                }

                if (!isAppend) {
                    // Reset grid HTML
                    propertiesGrid.innerHTML = '';
                }

                // Render properties
                if (data.properties && data.properties.length > 0) {
                    data.properties.forEach(prop => {
                        const cardHtml = createPropertyCardHtml(prop);
                        propertiesGrid.insertAdjacentHTML('beforeend', cardHtml);
                    });
                }

                // Update offset state
                offset += (data.properties ? data.properties.length : 0);

                // Update empty state display
                if (emptyStateEl) {
                    emptyStateEl.style.display = (totalCount === 0) ? 'block' : 'none';
                    if (totalCount === 0 && !propertiesGrid.contains(emptyStateEl)) {
                        propertiesGrid.appendChild(emptyStateEl);
                    }
                }

                // Show/hide Load More button
                if (loadMoreContainer) {
                    loadMoreContainer.style.display = (totalCount > offset) ? 'block' : 'none';
                }
            } else {
                console.error('API responded with error:', data ? data.error : 'Unknown error');
            }
        })
        .catch(err => {
            if (btnLoadMore) btnLoadMore.disabled = false;
            console.error('Error fetching properties:', err);
        });
    };

    // Trigger offset page loading on click
    if (btnLoadMore) {
        btnLoadMore.addEventListener('click', () => {
            fetchProperties(true);
        });
    }

    /* ─────────────────────────────────────────────────────────
       2. SYNCHRONIZE PRICE SLIDER & INPUTS
    ───────────────────────────────────────────────────────── */
    const updatePriceInputsFromSlider = () => {
        const val = parseInt(priceSlider.value);
        if (sliderMaxDisplay) sliderMaxDisplay.textContent = val.toLocaleString();
        if (priceMaxInput) priceMaxInput.value = val;
    };

    const updateSliderFromPriceInputs = () => {
        const maxVal = parseFloat(priceMaxInput.value);
        if (!isNaN(maxVal) && maxVal >= 0 && maxVal <= parseInt(priceSlider.max)) {
            priceSlider.value = maxVal;
            if (sliderMaxDisplay) sliderMaxDisplay.textContent = maxVal.toLocaleString();
        } else if (priceMaxInput.value === '') {
            priceSlider.value = priceSlider.max;
            if (sliderMaxDisplay) sliderMaxDisplay.textContent = parseInt(priceSlider.max).toLocaleString();
        }
    };

    if (priceSlider) {
        priceSlider.addEventListener('input', () => {
            updatePriceInputsFromSlider();
            fetchProperties(false);
        });
    }

    if (priceMaxInput) {
        priceMaxInput.addEventListener('change', () => {
            updateSliderFromPriceInputs();
            fetchProperties(false);
        });
    }

    if (priceMinInput) {
        priceMinInput.addEventListener('change', () => fetchProperties(false));
    }

    // Attach filter change listeners
    if (applyFiltersBtn) applyFiltersBtn.addEventListener('click', () => fetchProperties(false));
    if (listingTypeSelect) listingTypeSelect.addEventListener('change', () => fetchProperties(false));
    if (locationSelect) locationSelect.addEventListener('change', () => fetchProperties(false));
    if (parkingSelect) parkingSelect.addEventListener('change', () => fetchProperties(false));
    if (sortSelect) sortSelect.addEventListener('change', () => fetchProperties(false));

    const inputEvents = ['input', 'change'];
    const numericInputs = [priceMinInput, priceMaxInput, areaMinInput, areaMaxInput, roomsInput, bathroomsInput, floorInput];
    numericInputs.forEach(input => {
        if (input) {
            inputEvents.forEach(evt => input.addEventListener(evt, () => fetchProperties(false)));
        }
    });

    typeCheckboxes.forEach(cb => cb.addEventListener('change', () => fetchProperties(false)));

    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') fetchProperties(false);
        });
    }
    if (searchBtn) searchBtn.addEventListener('click', () => fetchProperties(false));

    /* ─────────────────────────────────────────────────────────
       3. CLEAR FILTERS LOGIC
    ───────────────────────────────────────────────────────── */
    const clearFilters = () => {
        if (searchInput) searchInput.value = '';
        if (listingTypeSelect) listingTypeSelect.value = 'All';
        if (locationSelect) locationSelect.value = 'All';

        typeCheckboxes.forEach(cb => cb.checked = false);

        if (priceMinInput) priceMinInput.value = '';
        if (priceMaxInput) priceMaxInput.value = '';
        if (priceSlider) {
            priceSlider.value = priceSlider.max;
            if (sliderMaxDisplay) sliderMaxDisplay.textContent = parseInt(priceSlider.max).toLocaleString();
        }

        if (areaMinInput) areaMinInput.value = '';
        if (areaMaxInput) areaMaxInput.value = '';
        if (roomsInput) roomsInput.value = '';
        if (bathroomsInput) bathroomsInput.value = '';
        if (floorInput) floorInput.value = '';
        if (parkingSelect) parkingSelect.value = 'Any';

        fetchProperties(false);
    };

    if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', clearFilters);

    /* ─────────────────────────────────────────────────────────
       4. INTERACTIVE EVENT DELEGATION FOR DETAIL & FAVORITE
    ───────────────────────────────────────────────────────── */
    if (propertiesGrid) {
        propertiesGrid.addEventListener('click', (e) => {
            // Check Favorite button click
            const favBtn = e.target.closest('.btn-favorite');
            if (favBtn) {
                e.stopPropagation();
                
                const propertyId = favBtn.dataset.id;
                if (!propertyId) return;

                favBtn.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    favBtn.style.transform = 'scale(1)';
                }, 200);

                fetch('/properties/favorite/toggle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ property_id: parseInt(propertyId) })
                })
                .then(response => {
                    if (response.status === 401) {
                        window.location.href = '/login';
                        return;
                    }
                    return response.json();
                })
                .then(data => {
                    if (data && data.success) {
                        if (data.action === 'added') {
                            favBtn.classList.add('active-favorite');
                        } else if (data.action === 'removed') {
                            favBtn.classList.remove('active-favorite');
                        }
                    } else if (data && data.error) {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error toggling favorite:', error);
                    alert('An error occurred. Please try again.');
                });
                return;
            }

            // Check View Details button click
            const detailsBtn = e.target.closest('.btn-card-details');
            if (detailsBtn) {
                e.stopPropagation();
                const card = detailsBtn.closest('.property-card');
                if (!card) return;

                const d = card.dataset;

                // Bind values to details modal
                document.getElementById('details-modal-title').textContent = `#LEB-${d.id} - Exclusive Collection Details`;
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
                if (detailsModal) {
                    detailsModal.classList.remove('hidden');
                }
            }
        });
    }

    const closeDetails = () => {
        if (detailsModal) {
            detailsModal.classList.add('hidden');
        }
    };

    if (btnCloseDetailsModal) btnCloseDetailsModal.addEventListener('click', closeDetails);
    if (btnCloseDetailsBottom) btnCloseDetailsBottom.addEventListener('click', closeDetails);

    // Dismiss modal on backdrop click
    window.addEventListener('click', (e) => {
        if (e.target === detailsModal) closeDetails();
    });

    // Check for query parameters on load
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('q') || urlParams.get('search');
    if (searchParam && searchInput) {
        searchInput.value = searchParam;
    }
    const listingTypeParam = urlParams.get('listing_type');
    if (listingTypeParam && listingTypeSelect) {
        listingTypeSelect.value = listingTypeParam;
    }
    const locationParam = urlParams.get('location');
    if (locationParam && locationSelect) {
        locationSelect.value = locationParam;
    }
    const priceMinParam = urlParams.get('price_min');
    if (priceMinParam && priceMinInput) {
        priceMinInput.value = priceMinParam;
    }
    const priceMaxParam = urlParams.get('price_max');
    if (priceMaxParam && priceMaxInput) {
        priceMaxInput.value = priceMaxParam;
        updateSliderFromPriceInputs();
    }
    const areaMinParam = urlParams.get('area_min');
    if (areaMinParam && areaMinInput) {
        areaMinInput.value = areaMinParam;
    }
    const areaMaxParam = urlParams.get('area_max');
    if (areaMaxParam && areaMaxInput) {
        areaMaxInput.value = areaMaxParam;
    }
    const roomsParam = urlParams.get('rooms');
    if (roomsParam && roomsInput) {
        roomsInput.value = roomsParam;
    }
    const bathroomsParam = urlParams.get('bathrooms');
    if (bathroomsParam && bathroomsInput) {
        bathroomsInput.value = bathroomsParam;
    }
    const floorParam = urlParams.get('floor');
    if (floorParam && floorInput) {
        floorInput.value = floorParam;
    }
    const parkingParam = urlParams.get('parking');
    if (parkingParam && parkingSelect) {
        parkingSelect.value = parkingParam;
    }
    const sortParam = urlParams.get('sort');
    if (sortParam && sortSelect) {
        sortSelect.value = sortParam;
    }
    const propertyTypesParam = urlParams.get('property_types');
    if (propertyTypesParam && typeCheckboxes.length > 0) {
        const typesList = propertyTypesParam.split(',').map(t => t.trim().toLowerCase());
        typeCheckboxes.forEach(cb => {
            if (typesList.includes(cb.value.trim().toLowerCase())) {
                cb.checked = true;
            }
        });
    }

    // Set initial load more container display
    if (loadMoreContainer) {
        loadMoreContainer.style.display = (totalCount > offset) ? 'block' : 'none';
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
