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

// Submit Change Password Form
function submitChangePassword(event) {
    event.preventDefault();

    const form = document.getElementById('change-password-form');
    if (!form) return;

    const currentPassword = document.getElementById('current_password').value;
    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;

    if (newPassword !== confirmPassword) {
        showToast('Validation Error', 'Confirm password does not match new password.', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showToast('Validation Error', 'Password must be at least 6 characters.', 'error');
        return;
    }

    fetch('/profile/change-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
            confirm_password: confirmPassword
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast('Error', data.error, 'error');
            } else {
                showToast('Success', 'Your password has been changed successfully.', 'success');
                form.reset();
                evaluatePasswordStrength(''); // Reset strength bar
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error', 'An error occurred while changing password.', 'error');
        });
}

// Dynamic Password Strength Evaluation
function evaluatePasswordStrength(password) {
    const bar1 = document.getElementById('strength-seg-1');
    const bar2 = document.getElementById('strength-seg-2');
    const bar3 = document.getElementById('strength-seg-3');
    const label = document.getElementById('strength-label');

    if (!bar1 || !bar2 || !bar3 || !label) return;

    // Reset
    bar1.style.backgroundColor = 'transparent';
    bar2.style.backgroundColor = 'transparent';
    bar3.style.backgroundColor = 'transparent';
    label.textContent = '';
    label.style.color = 'inherit';

    if (!password) return;

    let strength = 0;

    // Criteria 1: Length
    if (password.length >= 6) {
        strength = 1; // Weak
    }

    // Criteria 2: Mixed alpha-numeric
    if (password.length >= 6 && /[a-zA-Z]/.test(password) && /[0-9]/.test(password)) {
        strength = 2; // Medium
    }

    // Criteria 3: Complex features
    if (password.length >= 8 && /[a-z]/.test(password) && /[A-Z]/.test(password) && /[0-9]/.test(password) && /[^a-zA-Z0-9]/.test(password)) {
        strength = 3; // Strong
    }

    if (strength === 1) {
        bar1.style.backgroundColor = 'var(--error)';
        label.textContent = 'Weak';
        label.style.color = 'var(--error)';
    } else if (strength === 2) {
        bar1.style.backgroundColor = 'var(--color-warning)';
        bar2.style.backgroundColor = 'var(--color-warning)';
        label.textContent = 'Medium';
        label.style.color = 'var(--color-warning)';
    } else if (strength === 3) {
        bar1.style.backgroundColor = 'var(--color-success)';
        bar2.style.backgroundColor = 'var(--color-success)';
        bar3.style.backgroundColor = 'var(--color-success)';
        label.textContent = 'Strong & Secure';
        label.style.color = 'var(--color-success)';
    }
}

// Toggle Google Authenticator 2FA state
function toggleTwoFactor() {
    const toggle = document.getElementById('twofactor-toggle');
    const setupArea = document.getElementById('twofactor-setup-area');
    const qrContainer = document.getElementById('2fa-qr-container');
    const recoveryContainer = document.getElementById('2fa-recovery-container');

    if (!toggle || !setupArea || !qrContainer || !recoveryContainer) return;

    fetch('/profile/toggle-2fa', {
        method: 'POST'
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast('Error', data.error, 'error');
                toggle.checked = !toggle.checked; // Revert checkbox
            } else {
                showToast('Security Update', data.message, 'success');
                if (data.enabled) {
                    setupArea.style.display = 'flex';
                    qrContainer.style.display = 'block';
                    recoveryContainer.style.display = 'none';
                    
                    const secretKeyField = document.getElementById('mock-secret-key');
                    if (secretKeyField) {
                        secretKeyField.textContent = data.secret;
                    }

                    const qrImg = document.getElementById('2fa-qr-img');
                    const qrPlaceholder = document.getElementById('2fa-qr-placeholder');
                    if (qrImg && qrPlaceholder) {
                        if (data.qr_url) {
                            qrImg.src = data.qr_url;
                            qrImg.style.display = 'block';
                            qrPlaceholder.style.display = 'none';
                        } else {
                            qrImg.style.display = 'none';
                            qrPlaceholder.style.display = 'block';
                        }
                    }

                    // After a mock 5 seconds, "complete" configuration to show recovery tokens
                    setTimeout(() => {
                        qrContainer.style.display = 'none';
                        recoveryContainer.style.display = 'block';
                        showToast('2FA Configured', 'Google Authenticator linked. Backup recovery codes generated.', 'success');
                    }, 5000);
                } else {
                    setupArea.style.display = 'none';
                }
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error', 'An error occurred during 2FA configuration.', 'error');
            toggle.checked = !toggle.checked;
        });
}

// Revoke individual device session
function revokeSession(sessionId) {
    if (!confirm('Are you sure you want to revoke this session? If it is your current device, you will be logged out.')) {
        return;
    }

    fetch(`/profile/revoke-session/${sessionId}`, {
        method: 'POST'
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast('Revocation Failed', data.error, 'error');
            } else {
                showToast('Device Revoked', data.message, 'success');
                if (data.logged_out) {
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 1000);
                } else {
                    // Remove row from table
                    const row = document.getElementById(`session-row-${sessionId}`);
                    if (row) {
                        row.remove();
                    }
                }
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error', 'An error occurred while revoking session.', 'error');
        });
}

// Revoke all other device sessions
function revokeAllOtherSessions() {
    if (!confirm('Are you sure you want to terminate all other active sessions? All other logged-in devices will be disconnected.')) {
        return;
    }

    fetch('/profile/revoke-others', {
        method: 'POST'
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast('Error', data.error, 'error');
            } else {
                showToast('Devices Terminated', data.message, 'success');
                // Reload page to refresh the active sessions table
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error', 'An error occurred while revoking other sessions.', 'error');
        });
}
