document.addEventListener('DOMContentLoaded', () => {
    const content = document.querySelector('.content');
    content.classList.add('fade-in');

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
});
