/**
 * LebEstates - User Profile Settings JS Controller
 */

// Toast Notification System
function showToast(title, message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconName = type === 'success' ? 'check_circle' : 'error';

    toast.innerHTML = `
        <span class="material-symbols-outlined toast-icon">${iconName}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-msg">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    // Trigger reflow for transition animation
    toast.offsetHeight;
    toast.classList.add('show');

    // Automatically hide and remove after 4 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.remove());
    }, 4000);
}

// Preview and AJAX upload avatar
function previewAndUploadAvatar(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Visual validation on type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
        showToast('Invalid File Type', 'Please upload a PNG, JPG, JPEG, or GIF image.', 'error');
        return;
    }

    // Show local preview immediately
    const reader = new FileReader();
    reader.onload = function (e) {
        const preview = document.getElementById('avatar-preview');
        if (preview) {
            preview.src = e.target.result;
        }
    };
    reader.readAsDataURL(file);

    // Upload instantly
    const formData = new FormData();
    formData.append('avatar', file);
    
    const fullNameInput = document.getElementById('full_name');
    const phoneNumberInput = document.getElementById('phone_number');
    
    formData.append('full_name', fullNameInput ? fullNameInput.value : '');
    formData.append('phone_number', phoneNumberInput ? phoneNumberInput.value : '');

    fetch('/profile/edit-details', {
        method: 'POST',
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast('Upload Failed', data.error, 'error');
            } else {
                showToast('Success', 'Profile picture updated successfully.', 'success');
                // Reload page after a short delay to propagate avatar to nav bar headers
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error', 'An error occurred during upload.', 'error');
        });
}

// Submit general details (fullName, phone)
function submitEditProfile(event) {
    event.preventDefault();

    const form = document.getElementById('edit-profile-form');
    if (!form) return;
    
    const formData = new FormData(form);

    fetch('/profile/edit-details', {
        method: 'POST',
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast('Update Failed', data.error, 'error');
            } else {
                showToast('Success', 'Personal information saved.', 'success');
                // Update identity widget heading if exists
                const nameHeading = document.querySelector('.identity-name');
                const fullNameVal = document.getElementById('full_name');
                if (nameHeading && fullNameVal) {
                    nameHeading.textContent = fullNameVal.value;
                }
                // Reload page after delay to update nav headings
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error', 'An error occurred while updating profile.', 'error');
        });
}
