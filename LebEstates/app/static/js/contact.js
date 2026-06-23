document.addEventListener('DOMContentLoaded', () => {
    // Micro-interactions for form labels
    const inputs = document.querySelectorAll('.form-input, .form-select, .form-textarea');
    inputs.forEach(input => {
        const label = input.parentElement.querySelector('.form-label');
        if (!label) return;

        input.addEventListener('focus', () => {
            label.style.color = 'var(--secondary)';
        });
        input.addEventListener('blur', () => {
            if (!input.value) {
                label.style.color = '';
            }
        });
    });

    // Simple parallax effect for hero background
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const heroImage = document.querySelector('.hero-bg-img');
        if (heroImage) {
            heroImage.style.transform = `translateY(${scrolled * 0.35}px)`;
        }
    });
});
