document.addEventListener('DOMContentLoaded', function() {
    const title = document.querySelector('.app-title h1');
    
    title.addEventListener('mouseleave', function() {
        this.style.animation = 'none';
        this.offsetHeight; // Trigger reflow
        this.style.animation = null;
    });

    title.addEventListener('animationend', function() {
        this.style.animation = '';
    });
}); 