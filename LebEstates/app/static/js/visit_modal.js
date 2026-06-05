// visit_modal.js
document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('visit-modal');
    const btnCloseModal = document.getElementById('btn-close-visit-modal');
    const propertiesGrid = document.getElementById('properties-grid');
    const visitForm = document.getElementById('visit-form');
    const visitSuccessToast = document.getElementById('visit-success-toast');
    const btnCloseToast = document.getElementById('btn-close-visit-toast');

    // UI Elements to populate
    const heroImg = document.getElementById('visit-modal-hero-img');
    const badgeText = document.getElementById('visit-modal-badge-text');
    const propTitle = document.getElementById('visit-modal-prop-title');
    const propLocation = document.getElementById('visit-modal-prop-location');
    const propPrice = document.getElementById('visit-modal-prop-price');
    const propIdInput = document.getElementById('visit-property-id');

    // Open Modal via Event Delegation
    propertiesGrid.addEventListener('click', (e) => {
        const visitBtn = e.target.closest('.btn-card-visit');
        if (visitBtn) {
            const card = visitBtn.closest('.property-card');
            if (card) {
                // Extract data
                const propId = card.dataset.id;
                const title = card.dataset.title;
                const location = card.dataset.location;
                const price = card.dataset.price;
                const listingType = card.dataset.listingType; // Sell or Rent
                const imageUrls = card.dataset.imageUrls ? card.dataset.imageUrls.split(',') : [];

                // Format Price
                const formattedPrice = new Intl.NumberFormat('en-US').format(price);
                const priceSuffix = listingType === 'Rent' ? '/mo' : '';

                // Populate
                propIdInput.value = propId;
                propTitle.textContent = title;
                propLocation.textContent = location;
                propPrice.textContent = `$${formattedPrice}${priceSuffix}`;

                if (imageUrls && imageUrls.length > 0 && imageUrls[0]) {
                    heroImg.src = imageUrls[0];
                } else {
                    heroImg.src = ''; // Fallback or clear
                }

                if (parseFloat(price) > 1000000) {
                    badgeText.textContent = 'Exclusive Listing';
                    badgeText.style.display = 'inline-block';
                } else {
                    badgeText.textContent = `For ${listingType}`;
                    badgeText.style.display = 'inline-block';
                }

                // Show Modal
                modalOverlay.style.display = 'flex'; // Ensure flex
                // Force reflow
                void modalOverlay.offsetWidth;
                modalOverlay.classList.remove('hidden');
            }
        }
    });

    function closeVisitModal() {
        modalOverlay.classList.add('hidden');
        setTimeout(() => {
            if (modalOverlay.classList.contains('hidden')) {
                modalOverlay.style.display = 'none';
            }
        }, 500); // match transition
    }

    btnCloseModal.addEventListener('click', closeVisitModal);

    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            closeVisitModal();
        }
    });

    // Form Submit
    visitForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById('btn-visit-submit');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="material-symbols-outlined spin" style="animation: spin 1s linear infinite;">sync</span> Submitting...';
        submitBtn.disabled = true;

        const propertyId = propIdInput.value;
        const pTitle = propTitle.textContent;
        const userNotes = document.getElementById('visit-notes').value;

        const payload = {
            property_id: propertyId,
            notes: userNotes,
            visit_date: document.getElementById('visit-date').value,
            visit_time: document.getElementById('visit-time').value
        };

        fetch('/visit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(data => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;

                if (data.success) {
                    visitForm.reset();
                    closeVisitModal();
                    showVisitSuccess();
                } else {
                    alert('Error: ' + data.message);
                    if (data.message.toLowerCase().includes('logged in') || data.message.toLowerCase().includes('registered customers')) {
                        window.location.href = '/login';
                    }
                }
            })
            .catch(err => {
                console.error('Error submitting visit request:', err);
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                alert('An error occurred. Please try again.');
            });
    });

    function showVisitSuccess() {
        visitSuccessToast.style.display = 'flex';
        void visitSuccessToast.offsetWidth;
        visitSuccessToast.classList.add('show');
        visitSuccessToast.classList.remove('hidden');

        setTimeout(() => {
            hideVisitSuccess();
        }, 4000);
    }

    function hideVisitSuccess() {
        visitSuccessToast.classList.remove('show');
        setTimeout(() => {
            visitSuccessToast.classList.add('hidden');
            visitSuccessToast.style.display = 'none';
        }, 500);
    }

    btnCloseToast.addEventListener('click', hideVisitSuccess);
});
