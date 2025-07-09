// Pagination functionality can be added if necessary
// For example, handling button clicks for pagination or any dynamic content updates
document.addEventListener('DOMContentLoaded', function() {
    const prevButton = document.querySelector('.pagination a[rel="prev"]');
    const nextButton = document.querySelector('.pagination a[rel="next"]');
    
    if (prevButton) {
        prevButton.addEventListener('click', function(event) {
            event.preventDefault();
            const prevPage = parseInt(new URL(prevButton.href).searchParams.get('page'));
            updatePage(prevPage);
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', function(event) {
            event.preventDefault();
            const nextPage = parseInt(new URL(nextButton.href).searchParams.get('page'));
            updatePage(nextPage);
        });
    }
});

function updatePage(pageNumber) {
    // Perform actions for page change, such as making an AJAX request or updating the page content
    console.log('Navigating to page:', pageNumber);
}
