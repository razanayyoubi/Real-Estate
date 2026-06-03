document.addEventListener('DOMContentLoaded', () => {
    // Reveal animations on scroll using pure CSS classes
    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    document.querySelectorAll('section > div').forEach(el => {
        el.classList.add('reveal-el');
        observer.observe(el);
    });
});
