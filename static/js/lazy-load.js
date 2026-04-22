// Lazy loading implementation for images with optimization for all users
document.addEventListener('DOMContentLoaded', function() {
    // Always use optimized image loading for all users
    
    // Apply lazy loading to all images
    const imagesToLazyLoad = document.querySelectorAll('img[data-src]');
    
    // Set up Intersection Observer for better performance
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const image = entry.target;
                    
                    // For older/slower devices, use low-res version when available
                    if (window.navigator.connection && 
                        (window.navigator.connection.saveData === true || 
                         window.navigator.connection.effectiveType === 'slow-2g' || 
                         window.navigator.connection.effectiveType === '2g') && 
                        image.hasAttribute('data-src-low')) {
                        image.src = image.getAttribute('data-src-low');
                    } else {
                        image.src = image.getAttribute('data-src');
                    }
                    
                    // Set appropriate loading attribute
                    image.loading = "lazy";
                    
                    // Once loaded, stop observing
                    observer.unobserve(image);
                }
            });
        }, {
            rootMargin: '100px',
            threshold: 0.1
        });
        
        // Start observing each image
        imagesToLazyLoad.forEach(function(image) {
            imageObserver.observe(image);
        });
    } else {
        // Fallback for browsers that don't support Intersection Observer
        imagesToLazyLoad.forEach(function(image) {
            // For slower connections, use low-res when available
            if (window.navigator.connection && 
                (window.navigator.connection.saveData === true || 
                 window.navigator.connection.effectiveType === 'slow-2g' || 
                 window.navigator.connection.effectiveType === '2g') && 
                image.hasAttribute('data-src-low')) {
                image.src = image.getAttribute('data-src-low');
            } else {
                image.src = image.getAttribute('data-src');
            }
            image.loading = "lazy";
        });
    }
    
    // Add lazy loading to background images loaded via CSS for all users
    // This improves performance on all devices
    document.body.classList.add('lazy-backgrounds');
});

// Utility function to defer non-critical scripts
function loadDeferredScripts() {
    const deferredScripts = document.querySelectorAll('script[data-defer]');
    deferredScripts.forEach(function(script) {
        const newScript = document.createElement('script');
        if (script.src) {
            newScript.src = script.src;
        } else {
            newScript.textContent = script.textContent;
        }
        document.body.appendChild(newScript);
    });
}

// Load deferred scripts after page load
window.addEventListener('load', loadDeferredScripts);

// Utility function to fetch data in chunks for smoother loading on all devices
async function fetchDataInChunks(url, chunkSize = 50) {
    // Always use chunked loading for large datasets to improve performance for all users
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        // If the data is small, return as is
        if (!data.items || data.items.length <= chunkSize) {
            return data;
        }
        
        // Process data in chunks to avoid UI freezing
        const chunks = [];
        for (let i = 0; i < data.items.length; i += chunkSize) {
            chunks.push(data.items.slice(i, i + chunkSize));
        }
        
        // Create a new data object with the first chunk
        const result = {...data, items: chunks[0]};
        
        // Load the rest of the chunks asynchronously
        setTimeout(() => {
            let currentChunk = 1;
            const loadNextChunk = () => {
                if (currentChunk < chunks.length) {
                    result.items = [...result.items, ...chunks[currentChunk]];
                    currentChunk++;
                    setTimeout(loadNextChunk, 300);
                }
            };
            loadNextChunk();
        }, 1000);
        
        return result;
    } catch (error) {
        console.error('Error fetching data in chunks:', error);
        throw error;
    }
}