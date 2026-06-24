/* -------------------------------------------------------------
   LEBESTATES POST PROPERTY WIZARD JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    let currentStep = 1;
    const totalSteps = 3;

    // Determine user role and corresponding publish label
    const isEmployee = document.getElementById('input-owner') !== null;
    const publishButtonText = isEmployee ? 'Publish Listing' : 'Submit Request';
    const publishButtonIcon = isEmployee ? 'publish' : 'send';

    // Wizard DOM Elements
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const draftBtn = document.getElementById('draft-btn');
    const propertyForm = document.getElementById('property-form');
    const stepPanes = document.querySelectorAll('.wizard-pane');
    const stepNavs = document.querySelectorAll('.step-item');

    // Input Fields
    const inputTitle = document.getElementById('input-title');
    const inputPrice = document.getElementById('input-price');
    const inputArea = document.getElementById('input-area');
    const inputRegion = document.getElementById('input-region');
    const inputAddress = document.getElementById('input-address');
    const inputPropertyType = document.getElementById('input-property-type');
    const inputOwner = document.getElementById('input-owner');

    // Live Preview Card Elements
    const previewTitle = document.getElementById('preview-title');
    const previewPrice = document.getElementById('preview-price');
    const previewArea = document.getElementById('preview-area');
    const previewRegion = document.getElementById('preview-region');
    const previewPropertyType = document.getElementById('preview-property-type');
    const previewListingType = document.getElementById('preview-listing-type');
    const previewImg = document.getElementById('preview-img');
    const previewPlaceholder = document.getElementById('preview-placeholder');

    // Multi-File Upload Data
    let selectedFiles = [];
    const mediaDropzone = document.getElementById('media-dropzone');
    const fileInput = document.getElementById('input-photos');
    const photosGallery = document.getElementById('photos-gallery');

    // Interactive Leaflet Map logic
    let map = null;
    let marker = null;
    const regionCoordinates = {
        'Achrafieh': [33.8872, 35.5222],
        'Akkar': [34.5428, 36.0792],
        'Aley': [33.8056, 35.6028],
        'Baabda': [33.8344, 35.5414],
        'Baalbek': [34.0044, 36.2111],
        'Batroun': [34.2541, 35.6583],
        'Beirut': [33.8938, 35.5018],
        'Bint Jbeil': [33.1219, 35.4339],
        'Bsharri': [34.2514, 36.0125],
        'Byblos': [34.1228, 35.6521],
        'Byblos (Jbeil)': [34.1228, 35.6521],
        'Chouf': [33.6947, 35.5678],
        'Dahye': [33.8489, 35.5039],
        'Faraya': [34.0131, 35.8111],
        'Hasbaya': [33.3983, 35.6881],
        'Hermel': [34.3986, 36.3861],
        'Jezzine': [33.5419, 35.5861],
        'Keserwan': [33.9922, 35.6983],
        'Koura': [34.3414, 35.7956],
        'Marjeyoun': [33.3592, 35.5908],
        'Matn': [33.8933, 35.6667],
        'Miniyeh-Danniyeh': [34.4333, 36.0167],
        'Nabatieh': [33.3761, 35.4828],
        'North': [34.4379, 35.8367],
        'Rashaya': [33.5008, 35.8361],
        'Saida': [33.5597, 35.3725],
        'Sidon (Saida)': [33.5597, 35.3725],
        'South': [33.2708, 35.2039],
        'Sour': [33.2708, 35.1939],
        'Tyre (Sour)': [33.2708, 35.1939],
        'Tripoli': [34.4367, 35.8497],
        'West Bekaa': [33.6333, 35.7833],
        'Zahle': [33.8439, 35.9072],
        'Zgharta': [34.3989, 35.8958]
    };

    const initMap = () => {
        if (map) return;
        
        const defaultLat = 33.8938;
        const defaultLng = 35.5018;

        const mapContainer = document.getElementById('map-container');
        if (!mapContainer) return;

        // Initialize map
        map = L.map('map-container').setView([defaultLat, defaultLng], 12);

        // CartoDB Positron style to fit the premium light theme
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(map);

        // Add draggable marker
        marker = L.marker([defaultLat, defaultLng], { draggable: true }).addTo(map);

        // Set default inputs
        document.getElementById('input-latitude').value = defaultLat.toFixed(6);
        document.getElementById('input-longitude').value = defaultLng.toFixed(6);

        // Update inputs on drag
        marker.on('dragend', () => {
            const pos = marker.getLatLng();
            document.getElementById('input-latitude').value = pos.lat.toFixed(6);
            document.getElementById('input-longitude').value = pos.lng.toFixed(6);
        });

        // Update marker and inputs on map click
        map.on('click', (e) => {
            const pos = e.latlng;
            marker.setLatLng(pos);
            document.getElementById('input-latitude').value = pos.lat.toFixed(6);
            document.getElementById('input-longitude').value = pos.lng.toFixed(6);
        });
    };

    /* ─────────────────────────────────────────────────────────
       1. LIVE PREVIEW SYNCHRONIZATION
    ───────────────────────────────────────────────────────── */
    if (inputTitle) {
        inputTitle.addEventListener('input', (e) => {
            previewTitle.textContent = e.target.value.trim() || 'Property Title';
        });
    }

    if (inputPrice) {
        inputPrice.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            previewPrice.textContent = val >= 0 ? `$${val.toLocaleString()}` : '$0';
        });
    }

    if (inputArea) {
        inputArea.addEventListener('input', (e) => {
            previewArea.textContent = e.target.value ? `${e.target.value} m²` : '0 m²';
        });
    }

    if (inputRegion) {
        const handleRegionChange = (e) => {
            const val = e.target.value.trim();
            previewRegion.textContent = val || 'Select Region';
            
            // Pan map to the selected region center if initialized
            if (val && regionCoordinates[val]) {
                const coords = regionCoordinates[val];
                if (map) {
                    map.setView(coords, 13);
                }
                if (marker) {
                    marker.setLatLng(coords);
                }
                const latInput = document.getElementById('input-latitude');
                const lngInput = document.getElementById('input-longitude');
                if (latInput) latInput.value = coords[0].toFixed(6);
                if (lngInput) lngInput.value = coords[1].toFixed(6);
            }
        };
        inputRegion.addEventListener('change', handleRegionChange);
        inputRegion.addEventListener('input', handleRegionChange);
    }

    // Listing Type Radio Sync
    document.querySelectorAll('input[name="listing_type"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            previewListingType.textContent = `FOR ${e.target.value.toUpperCase()}`;
        });
    });

    // Property Type Button Selection
    const typeBtns = document.querySelectorAll('.type-btn');
    const customTypeWrapper = document.getElementById('custom-property-type-wrapper');
    const inputCustomPropertyType = document.getElementById('input-custom-property-type');

    if (inputCustomPropertyType) {
        inputCustomPropertyType.addEventListener('input', (e) => {
            const val = e.target.value.trim();
            inputPropertyType.value = val || 'Other';
            previewPropertyType.textContent = val || 'Custom Type';
            clearError('custom-property-type');
        });
    }

    typeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            typeBtns.forEach(b => b.classList.remove('type-btn-active'));
            btn.classList.add('type-btn-active');
            
            const selectedType = btn.dataset.type;
            if (selectedType === 'Other') {
                if (customTypeWrapper) customTypeWrapper.style.display = 'flex';
                const customVal = inputCustomPropertyType ? inputCustomPropertyType.value.trim() : '';
                inputPropertyType.value = customVal || 'Other';
                previewPropertyType.textContent = customVal || 'Custom Type';
            } else {
                if (customTypeWrapper) customTypeWrapper.style.display = 'none';
                inputPropertyType.value = selectedType;
                previewPropertyType.textContent = selectedType;
                clearError('custom-property-type');
            }
        });
    });

    /* ─────────────────────────────────────────────────────────
       2. COUNTER BUTTONS (ROOMS & BATHROOMS)
    ───────────────────────────────────────────────────────── */
    const setupCounter = (minusBtnId, plusBtnId, inputId, minVal = 1, maxVal = 20) => {
        const minusBtn = document.getElementById(minusBtnId);
        const plusBtn = document.getElementById(plusBtnId);
        const input = document.getElementById(inputId);

        if (minusBtn && plusBtn && input) {
            minusBtn.addEventListener('click', () => {
                let currentVal = parseInt(input.value) || minVal;
                if (currentVal > minVal) {
                    input.value = currentVal - 1;
                }
            });
            plusBtn.addEventListener('click', () => {
                let currentVal = parseInt(input.value) || minVal;
                if (currentVal < maxVal) {
                    input.value = currentVal + 1;
                }
            });
        }
    };

    setupCounter('rooms-minus', 'rooms-plus', 'input-rooms', 1, 20);
    setupCounter('bathrooms-minus', 'bathrooms-plus', 'input-bathrooms', 1, 10);

    /* ─────────────────────────────────────────────────────────
       3. DRAG & DROP MULTI-FILE UPLOAD GALLERY
    ───────────────────────────────────────────────────────── */
    if (mediaDropzone && fileInput) {
        // Clicking dropzone triggers the file input
        mediaDropzone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            handleSelectedFiles(e.target.files);
        });

        // Drag events
        ['dragenter', 'dragover'].forEach(eventName => {
            mediaDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                mediaDropzone.classList.add('media-upload-dropzone--active');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            mediaDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                mediaDropzone.classList.remove('media-upload-dropzone--active');
            }, false);
        });

        mediaDropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleSelectedFiles(files);
        });
    }

    const handleSelectedFiles = (files) => {
        const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif'];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (allowedTypes.includes(file.type)) {
                selectedFiles.push(file);
            }
        }
        renderGallery();
    };

    const renderGallery = () => {
        photosGallery.innerHTML = '';
        
        if (selectedFiles.length === 0) {
            if (previewImg) previewImg.style.display = 'none';
            if (previewPlaceholder) previewPlaceholder.style.display = 'flex';
            return;
        }

        selectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                // Set first image as the preview card cover
                if (index === 0) {
                    if (previewImg) {
                        previewImg.src = e.target.result;
                        previewImg.style.display = 'block';
                    }
                    if (previewPlaceholder) {
                        previewPlaceholder.style.display = 'none';
                    }
                }

                // Create gallery item element
                const item = document.createElement('div');
                item.className = 'gallery-item';
                item.innerHTML = `
                    <img src="${e.target.result}" alt="Property Photo ${index + 1}" />
                    <button type="button" class="remove-photo-btn" data-index="${index}">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                `;
                photosGallery.appendChild(item);

                // Add event listener to remove button
                item.querySelector('.remove-photo-btn').addEventListener('click', (ev) => {
                    ev.stopPropagation();
                    selectedFiles.splice(index, 1);
                    renderGallery();
                    // Clear error check if gallery is no longer empty
                    if (selectedFiles.length > 0) {
                        clearError('photos');
                    }
                });
            };
            reader.readAsDataURL(file);
        });

        // Hide validation error once a photo is present
        clearError('photos');
    };

    /* ─────────────────────────────────────────────────────────
       4. FORM CLIENT-SIDE VALIDATION
    ───────────────────────────────────────────────────────── */
    const showError = (fieldId, message = null) => {
        const field = document.getElementById(`input-${fieldId}`);
        const errMsg = document.getElementById(`err-${fieldId}`);
        if (field) field.classList.add('error-control');
        if (errMsg) {
            if (message) errMsg.textContent = message;
            errMsg.classList.add('error-msg-active');
        }
    };

    const clearError = (fieldId) => {
        const field = document.getElementById(`input-${fieldId}`);
        const errMsg = document.getElementById(`err-${fieldId}`);
        if (field) field.classList.remove('error-control');
        if (errMsg) errMsg.classList.remove('error-msg-active');
    };

    // Auto-clear validation indicators on input change
    const fieldsToAutoClear = ['title', 'price', 'area', 'region', 'address'];
    fieldsToAutoClear.forEach(fieldId => {
        const el = document.getElementById(`input-${fieldId}`);
        if (el) {
            el.addEventListener('input', () => clearError(fieldId));
            el.addEventListener('change', () => clearError(fieldId));
        }
    });

    const validateStep = (step) => {
        let isValid = true;

        if (step === 1) {
            // Owner selector for admin/employees
            if (isEmployee) {
                const ownerSelect = document.getElementById('input-owner');
                if (ownerSelect && !ownerSelect.value) {
                    ownerSelect.classList.add('error-control');
                    isValid = false;
                } else if (ownerSelect) {
                    ownerSelect.classList.remove('error-control');
                }
            }

            // Title
            if (!inputTitle.value.trim()) {
                showError('title');
                isValid = false;
            } else {
                clearError('title');
            }

            // Price
            const priceVal = parseFloat(inputPrice.value);
            if (isNaN(priceVal) || priceVal < 0) {
                showError('price');
                isValid = false;
            } else {
                clearError('price');
            }

            // Custom Property Type (Other) validation
            const activeTypeBtn = document.querySelector('.type-btn-active');
            if (activeTypeBtn && activeTypeBtn.dataset.type === 'Other') {
                if (inputCustomPropertyType && !inputCustomPropertyType.value.trim()) {
                    showError('custom-property-type');
                    isValid = false;
                } else {
                    clearError('custom-property-type');
                }
            }
        }

        if (step === 2) {
            // Total Area
            const areaVal = parseFloat(inputArea.value);
            if (isNaN(areaVal) || areaVal <= 0) {
                showError('area');
                isValid = false;
            } else {
                clearError('area');
            }
        }

        if (step === 3) {
            // Region
            if (!inputRegion.value) {
                showError('region');
                isValid = false;
            } else {
                clearError('region');
            }

            // Address
            if (!inputAddress.value.trim()) {
                showError('address');
                isValid = false;
            } else {
                clearError('address');
            }

            // Photos Gallery
            if (selectedFiles.length === 0) {
                showError('photos');
                isValid = false;
            } else {
                clearError('photos');
            }
        }

        return isValid;
    };

    /* ─────────────────────────────────────────────────────────
       5. MULTI-STEP NAVIGATION WIZARD LOGIC
    ───────────────────────────────────────────────────────── */
    const updateSteps = () => {
        // Toggle panes visibility
        stepPanes.forEach((pane, idx) => {
            pane.classList.toggle('pane-active', (idx + 1) === currentStep);
        });

        // Initialize or refresh map layout when step 3 is shown
        if (currentStep === 3) {
            setTimeout(() => {
                if (!map) {
                    initMap();
                } else {
                    map.invalidateSize();
                }
            }, 150);
        }

        // Update active class on tracker steps
        stepNavs.forEach((nav, idx) => {
            const stepNum = idx + 1;
            
            nav.classList.remove('step-active', 'step-inactive', 'step-completed');
            
            if (stepNum === currentStep) {
                nav.classList.add('step-active');
            } else if (stepNum < currentStep) {
                nav.classList.add('step-completed');
            } else {
                nav.classList.add('step-inactive');
            }
        });

        // Set Prev button state
        if (currentStep === 1) {
            prevBtn.classList.add('btn-hidden');
        } else {
            prevBtn.classList.remove('btn-hidden');
        }

        // Set Next/Publish button state
        if (currentStep === totalSteps) {
            nextBtn.innerHTML = `${publishButtonText} <span class="material-symbols-outlined">${publishButtonIcon}</span>`;
            nextBtn.classList.add('nav-btn-publish');
        } else {
            const nextLabel = currentStep === 1 ? 'Property Specs' : 'Location & Media';
            nextBtn.innerHTML = `Next: ${nextLabel} <span class="material-symbols-outlined">chevron_right</span>`;
            nextBtn.classList.remove('nav-btn-publish');
        }
    };

    // Next step button / Submit handler
    nextBtn.addEventListener('click', () => {
        if (validateStep(currentStep)) {
            if (currentStep < totalSteps) {
                currentStep++;
                updateSteps();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                // Perform final submission
                submitPropertyForm();
            }
        }
    });

    // Previous step button
    prevBtn.addEventListener('click', () => {
        if (currentStep > 1) {
            currentStep--;
            updateSteps();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    // Left sidebar clickable navigation steps (only if validation allows)
    stepNavs.forEach((nav, idx) => {
        nav.addEventListener('click', () => {
            const targetStep = idx + 1;
            if (targetStep === currentStep) return;

            // Prevent jumping ahead of unvalidated steps
            if (targetStep > currentStep) {
                for (let s = currentStep; s < targetStep; s++) {
                    if (!validateStep(s)) {
                        currentStep = s;
                        updateSteps();
                        return;
                    }
                }
            }

            currentStep = targetStep;
            updateSteps();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });

    // Save Draft click handler
    if (draftBtn) {
        draftBtn.addEventListener('click', () => {
            alert('Draft Saved Successfully (Simulated)!');
        });
    }

    /* ─────────────────────────────────────────────────────────
       6. AJAX SUBMISSION
    ───────────────────────────────────────────────────────── */
    const submitPropertyForm = () => {
        // Disable buttons and show saving indicator
        nextBtn.disabled = true;
        nextBtn.innerHTML = `Saving Listing... <span class="material-symbols-outlined animate-spin" style="animation: spin 1.5s linear infinite;">sync</span>`;
        if (prevBtn) prevBtn.disabled = true;
        if (draftBtn) draftBtn.disabled = true;

        // Build FormData
        const formData = new FormData(propertyForm);

        // Remove the default photos list from input file since we upload our custom array
        formData.delete('photos');
        selectedFiles.forEach((file) => {
            formData.append('photos', file);
        });

        // Perform request
        fetch('/sell-rent', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(res => {
            if (res.status === 201) {
                alert(res.body.message);
                // Redirect user based on role
                window.location.href = isEmployee ? '/dashboard' : '/';
            } else {
                alert(res.body.error || 'Failed to submit the listing. Please check the fields.');
                resetLoadingState();
            }
        })
        .catch(err => {
            console.error('Submission Error:', err);
            alert('An unexpected network error occurred while posting the listing.');
            resetLoadingState();
        });
    };


    const resetLoadingState = () => {
        nextBtn.disabled = false;
        if (prevBtn) prevBtn.disabled = false;
        if (draftBtn) draftBtn.disabled = false;
        updateSteps();
    };
});
