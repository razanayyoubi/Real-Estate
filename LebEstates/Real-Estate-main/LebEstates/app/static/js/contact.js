document.addEventListener('DOMContentLoaded', () => {
    const channelCards = document.querySelectorAll('.channel-card');

    channelCards.forEach(card => {
        const glowTracker = card.querySelector('.card-glow-tracker');
        if (!glowTracker) return;

        // Dynamic Spotlight tracking inside the luxury cards
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Set the radial gradient position to follow mouse coordinates
            glowTracker.style.background = `radial-gradient(circle 150px at ${x}px ${y}px, rgba(255, 255, 255, 0.12), transparent)`;
        });

        // Soft reset when mouse leaves the card boundaries
        card.addEventListener('mouseleave', () => {
            glowTracker.style.background = '';
        });
    });
});
