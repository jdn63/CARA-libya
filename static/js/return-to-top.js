// Return to top button functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get the button element
    const returnToTopBtn = document.getElementById('return-to-top');
    
    // If the button doesn't exist (e.g., on the home page), exit early
    if (!returnToTopBtn) return;
    
    // When the user scrolls down 300px from the top of the document, show the button
    window.addEventListener('scroll', function() {
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            returnToTopBtn.style.display = 'flex';
            returnToTopBtn.style.justifyContent = 'center';
            returnToTopBtn.style.alignItems = 'center';
        } else {
            returnToTopBtn.style.display = 'none';
        }
    });
    
    // When the user clicks on the button, scroll to the top of the document
    returnToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});