let page = 1;
let loading = false;
let hasMore = true;

function loadMorePosts() {
    if (loading || !hasMore) return;
    
    loading = true;
    document.querySelector('.gallery-container').classList.add('loading');
    
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.set('page', page + 1);
    
    fetch(`${window.location.pathname}?${searchParams.toString()}`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        const galleryGrid = document.querySelector('.gallery-grid');
        galleryGrid.insertAdjacentHTML('beforeend', data.html);
        
        hasMore = data.has_more;
        if (hasMore) {
            page++;
        }
    })
    .catch(error => {
        console.error('Error loading more posts:', error);
    })
    .finally(() => {
        loading = false;
        document.querySelector('.gallery-container').classList.remove('loading');
    });
}

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !loading) {
            loadMorePosts();
        }
    });
}, {
    rootMargin: '100px'
});

document.addEventListener('DOMContentLoaded', () => {
    const sentinel = document.querySelector('.sentinel');
    if (sentinel) {
        observer.observe(sentinel);
    }
    
    const tagNav = document.querySelector('.tag-navigation');
    const leftBtn = document.querySelector('.scroll-left');
    const rightBtn = document.querySelector('.scroll-right');
    
    if (tagNav && leftBtn && rightBtn) {
        leftBtn.addEventListener('click', () => {
            tagNav.scrollBy({ left: -200, behavior: 'smooth' });
        });
        
        rightBtn.addEventListener('click', () => {
            tagNav.scrollBy({ left: 200, behavior: 'smooth' });
        });
        
        tagNav.addEventListener('scroll', () => {
            leftBtn.style.display = tagNav.scrollLeft > 0 ? 'block' : 'none';
            rightBtn.style.display = 
                tagNav.scrollLeft < (tagNav.scrollWidth - tagNav.clientWidth) 
                ? 'block' 
                : 'none';
        });
        
        leftBtn.style.display = 'none';
        rightBtn.style.display = 
            tagNav.scrollWidth > tagNav.clientWidth ? 'block' : 'none';
    }
    
    const activeTag = document.querySelector('.tag-item.active');
    if (activeTag && tagNav) {
        setTimeout(() => {
            const activeTagLeft = activeTag.offsetLeft;
            const navWidth = tagNav.clientWidth;
            const scrollTo = activeTagLeft - (navWidth / 2) + (activeTag.offsetWidth / 2);
            
            tagNav.scrollTo({
                left: Math.max(0, scrollTo),
                behavior: 'smooth'
            });
        }, 100);
    }
});