/* -------------------------------------------------------------
   LEBESTATES PROPERTY MANAGEMENT MODULE CUSTOM JAVASCRIPT
   ------------------------------------------------------------- */

document.addEventListener('DOMContentLoaded', () => {
    
    // Modal Overlay Elements
    const detailsModal = document.getElementById('details-modal');
    const editModal = document.getElementById('edit-modal');

    // Details Modal elements
    const btnCloseDetailsModal = document.getElementById('btn-close-details-modal');
    const btnCloseDetailsBottom = document.getElementById('btn-close-details-bottom');
    
    // Edit Modal elements
    const btnCloseEditModal = document.getElementById('btn-close-edit-modal');
    const btnCancelEdit = document.getElementById('btn-cancel-edit');
    const editForm = document.getElementById('edit-property-form');

    // Dynamic stats recalculation
    const recalculateValuation = () => {
        const activeRows = document.querySelectorAll('.mgmt-row-main[data-status="Published"]');
        let sum = 0;
        activeRows.forEach(row => {
            const price = parseFloat(row.dataset.price) || 0;
            sum += price;
        });
        const valEl = document.querySelector('.stat-card-dark .stat-value');
        if (valEl) {
            if (sum >= 1_000_000_000) {
                valEl.textContent = `$${(sum / 1_000_000_000).toFixed(1)}B`;
            } else if (sum >= 1_000_000) {
                valEl.textContent = `$${(sum / 1_000_000).toFixed(1)}M`;
            } else {
                valEl.textContent = `$${sum.toLocaleString()}`;
            }
        }
    };

    // Helper: Update local statistics values dynamically
    const updateStatsCounter = (statIndex, delta) => {
        // statIndex: 0 = Total, 1 = Active, 2 = Pending
        const statCards = document.querySelectorAll('.stat-card');
        if (statCards && statCards[statIndex]) {
            const valEl = statCards[statIndex].querySelector('.stat-value');
            if (valEl) {
                const currentVal = parseInt(valEl.textContent.replace(/,/g, '')) || 0;
                valEl.textContent = (currentVal + delta).toLocaleString();
            }
        }
    };

    // 1. OPEN DETAILS MODAL (PREMIUM VIEW DETAILS CARD)
    const viewButtons = document.querySelectorAll('.btn-view');
    viewButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            const row = document.getElementById(`row-main-${id}`);
            if (!row) return;

            const d = row.dataset;

            // Populate text elements
            document.getElementById('details-modal-title').textContent = `#LEB-${id} - Details`;
            document.getElementById('details-title-text').textContent = d.title;
            document.getElementById('details-desc').textContent = d.description || 'No description provided.';
            
            // Badges
            const listingBadge = document.getElementById('details-listing-type');
            listingBadge.textContent = d.listingType.toUpperCase();
            
            const statusBadge = document.getElementById('details-status');
            statusBadge.textContent = d.status.toUpperCase();
            statusBadge.className = 'status-badge'; // Reset classes
            if (d.status === 'Published') statusBadge.classList.add('badge-published');
            else if (d.status === 'Pending') statusBadge.classList.add('badge-pending');
            else if (d.status === 'Sold') statusBadge.classList.add('badge-sold');
            else if (d.status === 'Rented') statusBadge.classList.add('badge-rented');
            else if (d.status === 'Rejected') statusBadge.classList.add('badge-rejected');
            
            const priceNum = parseFloat(d.price) || 0;
            document.getElementById('details-price-text').textContent = `$${priceNum.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
            
            document.getElementById('details-beds').textContent = d.rooms;
            document.getElementById('details-baths').textContent = d.bathrooms;
            document.getElementById('details-area').textContent = d.area;
            document.getElementById('details-floor').textContent = d.floor || 'N/A';
            document.getElementById('details-parking').textContent = d.parking === 'true' ? 'Available' : 'None';
            document.getElementById('details-property-type').textContent = d.type;
            
            document.getElementById('details-location').textContent = d.location;
            document.getElementById('details-address').textContent = d.address || 'N/A';
            document.getElementById('details-lat').textContent = d.latitude || 'N/A';
            document.getElementById('details-lng').textContent = d.longitude || 'N/A';
            
            document.getElementById('details-owner').textContent = `#CUST-${d.ownerId}`;
            document.getElementById('details-creator').textContent = `#USER-${d.creatorId}`;

            // Populate hero image and thumbnails gallery
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

                    // Click handler to update hero image in details view
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
                        <span>No images uploaded for this listing</span>
                    </div>
                `;
            }

            // Show details modal
            detailsModal.classList.remove('hidden');
        });
    });

    // Close Details Modal
    const closeDetails = () => {
        detailsModal.classList.add('hidden');
    };
    if (btnCloseDetailsModal) btnCloseDetailsModal.addEventListener('click', closeDetails);
    if (btnCloseDetailsBottom) btnCloseDetailsBottom.addEventListener('click', closeDetails);

    // 2. OPEN EDIT MODAL (PRE-FILLED EDITING CARD)
    const editButtons = document.querySelectorAll('.btn-edit');
    editButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.dataset.id;
            const row = document.getElementById(`row-main-${id}`);
            if (!row) return;

            const d = row.dataset;

            // Pre-fill all input fields
            document.getElementById('edit-prop-id').value = id;
            document.getElementById('edit-title').value = d.title;
            document.getElementById('edit-listing-type').value = d.listingType;
            document.getElementById('edit-price').value = d.price;
            document.getElementById('edit-property-type').value = d.type;
            document.getElementById('edit-area').value = d.area;
            document.getElementById('edit-rooms').value = d.rooms;
            document.getElementById('edit-bathrooms').value = d.bathrooms;
            document.getElementById('edit-floor').value = d.floor;
            document.getElementById('edit-parking').value = d.parking === 'true' ? 1 : 0;
            document.getElementById('edit-region').value = d.location; // select option
            document.getElementById('edit-address').value = d.address;
            document.getElementById('edit-latitude').value = d.latitude;
            document.getElementById('edit-longitude').value = d.longitude;
            document.getElementById('edit-description').value = d.description;

            // Render existing photos with trash remove buttons
            const existingPhotosContainer = document.getElementById('edit-existing-photos');
            existingPhotosContainer.innerHTML = '';
            document.getElementById('edit-deleted-images').value = '';
            const deletedImageIds = [];

            if (d.imageUrls && d.imageUrls.trim() !== '') {
                const urls = d.imageUrls.split(',');
                urls.forEach(url => {
                    const parts = url.split('/');
                    const imageId = parts[parts.length - 1];

                    const photoDiv = document.createElement('div');
                    photoDiv.className = 'edit-photo-item';

                    const img = document.createElement('img');
                    img.src = url;
                    img.alt = d.title;

                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className = 'btn-photo-remove';
                    removeBtn.innerHTML = '<span class="material-symbols-outlined">delete</span>';

                    removeBtn.addEventListener('click', () => {
                        deletedImageIds.push(imageId);
                        document.getElementById('edit-deleted-images').value = deletedImageIds.join(',');
                        photoDiv.remove();
                    });

                    photoDiv.appendChild(img);
                    photoDiv.appendChild(removeBtn);
                    existingPhotosContainer.appendChild(photoDiv);
                });
            } else {
                existingPhotosContainer.innerHTML = '<p style="font-size: 13px; color: var(--outline); margin: 0;">No existing photos.</p>';
            }

            // Show edit modal
            editModal.classList.remove('hidden');
        });
    });

    // Close Edit Modal
    const closeEdit = () => {
        editModal.classList.add('hidden');
        editForm.reset();
    };
    if (btnCloseEditModal) btnCloseEditModal.addEventListener('click', closeEdit);
    if (btnCancelEdit) btnCancelEdit.addEventListener('click', closeEdit);

    // Close Modals on Outer Overlay Click
    window.addEventListener('click', (e) => {
        if (e.target === detailsModal) closeDetails();
        if (e.target === editModal) closeEdit();
    });

    // 3. EDIT FORM SUBMISSION (AJAX)
    if (editForm) {
        editForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const id = document.getElementById('edit-prop-id').value;
            const saveBtn = document.getElementById('btn-save-edit');
            
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';

            const formData = new FormData(editForm);

            fetch(`/properties/${id}/edit`, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);

                    // Update local dataset and table UI instantly
                    const row = document.getElementById(`row-main-${id}`);
                    if (row) {
                        // Gather input values
                        const titleVal = document.getElementById('edit-title').value;
                        const listingTypeVal = document.getElementById('edit-listing-type').value;
                        const priceVal = document.getElementById('edit-price').value;
                        const typeVal = document.getElementById('edit-property-type').value;
                        const areaVal = document.getElementById('edit-area').value;
                        const roomsVal = document.getElementById('edit-rooms').value;
                        const bathroomsVal = document.getElementById('edit-bathrooms').value;
                        const floorVal = document.getElementById('edit-floor').value;
                        const parkingVal = parseInt(document.getElementById('edit-parking').value) > 0 ? 'true' : 'false';
                        const regionVal = document.getElementById('edit-region').value;
                        const addressVal = document.getElementById('edit-address').value;
                        const latVal = document.getElementById('edit-latitude').value;
                        const lngVal = document.getElementById('edit-longitude').value;
                        const descVal = document.getElementById('edit-description').value;

                        // Update dataset attributes
                        row.dataset.title = titleVal;
                        row.dataset.listingType = listingTypeVal;
                        row.dataset.price = priceVal;
                        row.dataset.type = typeVal;
                        row.dataset.area = areaVal;
                        row.dataset.rooms = roomsVal;
                        row.dataset.bathrooms = bathroomsVal;
                        row.dataset.floor = floorVal;
                        row.dataset.parking = parkingVal;
                        row.dataset.location = regionVal;
                        row.dataset.address = addressVal;
                        row.dataset.latitude = latVal;
                        row.dataset.longitude = lngVal;
                        row.dataset.description = descVal;
                        row.dataset.imageUrls = data.image_urls || '';

                        // Update DOM table cells
                        row.querySelector('.property-title-text').textContent = titleVal;
                        row.querySelector('.col-type').textContent = typeVal;
                        row.querySelector('.location-cell-wrapper span').textContent = regionVal;
                        row.querySelector('.col-price').textContent = `$${parseFloat(priceVal).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

                        // Update table thumbnail image
                        const thumbImg = row.querySelector('.table-thumb');
                        if (data.image_urls && data.image_urls.trim() !== '') {
                            const firstUrl = data.image_urls.split(',')[0];
                            if (thumbImg) {
                                thumbImg.src = firstUrl;
                            } else {
                                const placeholder = row.querySelector('.table-thumb-placeholder');
                                if (placeholder) {
                                    const newImg = document.createElement('img');
                                    newImg.className = 'table-thumb';
                                    newImg.src = firstUrl;
                                    newImg.alt = titleVal;
                                    placeholder.replaceWith(newImg);
                                }
                            }
                        } else {
                            if (thumbImg) {
                                const placeholder = document.createElement('div');
                                placeholder.className = 'table-thumb-placeholder';
                                placeholder.innerHTML = '<span class="material-symbols-outlined">image</span>';
                                thumbImg.replaceWith(placeholder);
                            }
                        }
                    }

                    // Recalculate Portfolio Valuation stat card
                    recalculateValuation();

                    closeEdit();
                } else {
                    alert(data.error || 'Failed to update property details.');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Network error occurred.');
            })
            .finally(() => {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save Changes';
            });
        });
    }

    // 4. CLIENT-SIDE DROPDOWN SELECT FILTERS
    const filterStatus = document.getElementById('filter-status');
    const filterType = document.getElementById('filter-type');
    const filterLocation = document.getElementById('filter-location');
    const mainRows = document.querySelectorAll('.mgmt-row-main');
    const showingCountSpan = document.getElementById('showing-count');

    const applyFilters = () => {
        const selectedStatus = filterStatus.value.toLowerCase();
        const selectedType = filterType.value.toLowerCase();
        const selectedLocation = filterLocation.value.toLowerCase();

        let visibleCount = 0;

        mainRows.forEach(row => {
            const propStatus = row.dataset.status.toLowerCase();
            const propType = row.dataset.type.toLowerCase();
            const propLocation = row.dataset.location.toLowerCase();

            const statusMatch = (selectedStatus === 'all') || (propStatus === selectedStatus) || 
                                (selectedStatus === 'published' && propStatus === 'published') ||
                                (selectedStatus === 'pending' && propStatus === 'pending');
            const typeMatch = (selectedType === 'all') || (propType === selectedType);
            const locationMatch = (selectedLocation === 'all') || (propLocation === selectedLocation);

            if (statusMatch && typeMatch && locationMatch) {
                row.style.display = 'table-row';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        if (showingCountSpan) {
            showingCountSpan.textContent = visibleCount;
        }

        let emptyRow = document.querySelector('.table-empty-row');
        if (visibleCount === 0) {
            if (!emptyRow) {
                const tbody = document.getElementById('inventory-table-body');
                emptyRow = document.createElement('tr');
                emptyRow.className = 'table-empty-row';
                emptyRow.innerHTML = `
                    <td colspan="7" style="text-align: center;">
                        <div class="table-empty-state" style="padding: 60px; color: var(--on-surface-variant); display: flex; flex-direction: column; align-items: center; gap: 12px;">
                            <span class="material-symbols-outlined" style="font-size: 48px; color: var(--outline-variant);">inventory_2</span>
                            <p style="margin: 0; font-size: 14px;">No matching listings found for the selected filters.</p>
                        </div>
                    </td>
                `;
                tbody.appendChild(emptyRow);
            } else {
                emptyRow.style.display = 'table-row';
            }
        } else if (emptyRow) {
            emptyRow.style.display = 'none';
        }
    };

    if (filterStatus) filterStatus.addEventListener('change', applyFilters);
    if (filterType) filterType.addEventListener('change', applyFilters);
    if (filterLocation) filterLocation.addEventListener('change', applyFilters);


    // 5. APPROVE PROPERTY ACTION (AJAX)
    const pendingQueueList = document.getElementById('pending-queue-list');

    const checkQueueEmpty = () => {
        if (pendingQueueList && pendingQueueList.children.length === 0) {
            pendingQueueList.innerHTML = `
                <div class="queue-empty-state">
                    <span class="material-symbols-outlined">done_all</span>
                    <p>No listings require review. All submissions are current.</p>
                </div>
            `;
        }
    };

    document.querySelectorAll('.btn-approve').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;
            
            btn.disabled = true;
            btn.textContent = 'Approve...';

            fetch(`/properties/${id}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    
                    const statusTd = document.getElementById(`row-status-${id}`);
                    if (statusTd) {
                        statusTd.innerHTML = `<span class="status-badge badge-published">PUBLISHED</span>`;
                    }
                    
                    const mainRow = document.getElementById(`row-main-${id}`);
                    if (mainRow) {
                        mainRow.dataset.status = 'Published';
                    }

                    const queueItem = document.getElementById(`queue-item-${id}`);
                    if (queueItem) {
                        queueItem.remove();
                    }
                    
                    updateStatsCounter(2, -1);
                    updateStatsCounter(1, 1);
                    
                    checkQueueEmpty();
                    recalculateValuation();
                    applyFilters();
                } else {
                    alert(data.error || 'Failed to approve listing.');
                    btn.disabled = false;
                    btn.textContent = 'Approve';
                }
            })
            .catch(err => {
                console.error(err);
                alert('Network error occurred.');
                btn.disabled = false;
                btn.textContent = 'Approve';
            });
        });
    });


    // 6. REJECT PROPERTY ACTION (AJAX)
    document.querySelectorAll('.btn-reject').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;

            btn.disabled = true;
            btn.textContent = 'Reject...';

            fetch(`/properties/${id}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);

                    const statusTd = document.getElementById(`row-status-${id}`);
                    if (statusTd) {
                        statusTd.innerHTML = `<span class="status-badge badge-rejected">REJECTED</span>`;
                    }
                    
                    const mainRow = document.getElementById(`row-main-${id}`);
                    if (mainRow) {
                        mainRow.dataset.status = 'Rejected';
                    }

                    const queueItem = document.getElementById(`queue-item-${id}`);
                    if (queueItem) {
                        queueItem.remove();
                    }
                    
                    updateStatsCounter(2, -1);
                    
                    checkQueueEmpty();
                    recalculateValuation();
                    applyFilters();
                } else {
                    alert(data.error || 'Failed to reject listing.');
                    btn.disabled = false;
                    btn.textContent = 'Reject';
                }
            })
            .catch(err => {
                console.error(err);
                alert('Network error occurred.');
                btn.disabled = false;
                btn.textContent = 'Reject';
            });
        });
    });


    // 7. DELETE PROPERTY LISTING ACTION (AJAX)
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.dataset.id;
            
            if (confirm('Are you sure you want to permanently delete this property listing? This action is irreversible.')) {
                fetch(`/properties/${id}/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        
                        const mainRow = document.getElementById(`row-main-${id}`);
                        const queueItem = document.getElementById(`queue-item-${id}`);

                        let wasPending = false;
                        let wasPublished = false;
                        if (mainRow) {
                            wasPending = mainRow.dataset.status.toLowerCase() === 'pending';
                            wasPublished = mainRow.dataset.status.toLowerCase() === 'published';
                            mainRow.remove();
                        }
                        if (queueItem) queueItem.remove();

                        updateStatsCounter(0, -1);
                        if (wasPending) updateStatsCounter(2, -1);
                        if (wasPublished) updateStatsCounter(1, -1);

                        checkQueueEmpty();
                        recalculateValuation();
                        applyFilters();
                    } else {
                        alert(data.error || 'Failed to delete property listing.');
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert('Network error occurred.');
                });
            }
        });
    });
    // 8. UPDATE PROPERTY STATUS FROM DROPDOWN
    document.querySelectorAll('.status-dropdown').forEach(dropdown => {
        dropdown.dataset.originalStatus = dropdown.value;
        
        dropdown.addEventListener('change', (e) => {
            const id = dropdown.dataset.id;
            const newStatus = dropdown.value;
            const oldStatus = dropdown.dataset.originalStatus;
            
            if (!confirm(`Are you sure you want to change the status to ${newStatus}?`)) {
                dropdown.value = oldStatus;
                return;
            }

            fetch(`/properties/${id}/update_status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    dropdown.className = `status-dropdown status-${newStatus.toLowerCase()}`;
                    dropdown.dataset.originalStatus = newStatus;
                    
                    const mainRow = document.getElementById(`row-main-${id}`);
                    if (mainRow) {
                        mainRow.dataset.status = newStatus;
                    }

                    if (oldStatus.toLowerCase() === 'published') updateStatsCounter(1, -1);
                    if (oldStatus.toLowerCase() === 'pending') updateStatsCounter(2, -1);
                    
                    if (newStatus.toLowerCase() === 'published') updateStatsCounter(1, 1);
                    if (newStatus.toLowerCase() === 'pending') updateStatsCounter(2, 1);

                    const queueItem = document.getElementById(`queue-item-${id}`);
                    if (queueItem && newStatus.toLowerCase() !== 'pending') {
                        queueItem.remove();
                        checkQueueEmpty();
                    }
                    
                    recalculateValuation();
                    applyFilters();
                } else {
                    alert(data.error || 'Failed to update property status.');
                    dropdown.value = oldStatus;
                }
            })
            .catch(err => {
                console.error(err);
                alert('Network error occurred.');
                dropdown.value = oldStatus;
            });
        });
    });
});
