document.addEventListener('DOMContentLoaded', () => {
    // Fade-in animation for all elements
    const content = document.querySelector('.content');
    setTimeout(() => {
        content.classList.add('fade-in');
    }, 100);

    // Ripple effect on background click
    document.body.addEventListener('click', (e) => {
        const ripple = document.createElement('div');
        ripple.classList.add('ripple-effect');
        ripple.style.left = `${e.clientX}px`;
        ripple.style.top = `${e.clientY}px`;
        document.body.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 1500);
    });

    // Smooth scroll animation
    const scrollElements = document.querySelectorAll('.content > *');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    scrollElements.forEach((el) => {
        el.style.opacity = 0;
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 1s ease-out, transform 1s ease-out';
        observer.observe(el);
    });
});
