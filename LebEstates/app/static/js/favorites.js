/* -------------------------------------------------------------
   LEBESTATES FAVORITE PROPERTIES MODULE INTERACTIVE JAVASCRIPT
   ------------------------------------------------------------- */

const initFavorites = () => {
    const propertiesGrid = document.getElementById('properties-grid');
    const detailsModal = document.getElementById('details-modal');
    const btnCloseDetailsModal = document.getElementById('btn-close-details-modal');
    const btnCloseDetailsBottom = document.getElementById('btn-close-details-bottom');
    const emptyView = document.getElementById('favorites-empty-view');

    /* ─────────────────────────────────────────────────────────
       1. INTERACTIVE FAVORITES TOGGLE (Removal animation on this page)
    ───────────────────────────────────────────────────────── */
    const favoriteBtns = document.querySelectorAll('.btn-favorite');
    favoriteBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            
            const propertyId = btn.dataset.id;
            if (!propertyId) return;

            const card = btn.closest('.property-card');
            if (!card) return;

            // Apply scale pop micro-interaction
            btn.style.transform = 'scale(1.2)';
            setTimeout(() => {
                btn.style.transform = 'scale(1)';
            }, 200);

            // AJAX Toggle Request
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
                    if (data.action === 'removed') {
                        // Add class to animate card removal
                        card.classList.add('removing');
                        
                        setTimeout(() => {
                            card.remove();
                            // Check if no cards remaining to display empty state
                            const remainingCards = document.querySelectorAll('.property-card');
                            if (remainingCards.length === 0) {
                                if (propertiesGrid) {
                                    propertiesGrid.style.display = 'none';
                                }
                                if (emptyView) {
                                    emptyView.style.display = 'flex';
                                }
                            }
                        }, 400);
                    }
                } else if (data && data.error) {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error toggling favorite:', error);
                alert('An error occurred. Please try again.');
            });
        });
    });

    /* ─────────────────────────────────────────────────────────
       2. VIEW DETAILS MODAL SERVICE
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
            if (detailsModal) {
                detailsModal.classList.remove('hidden');
            }
        });
    });

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
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFavorites);
} else {
    initFavorites();
}
