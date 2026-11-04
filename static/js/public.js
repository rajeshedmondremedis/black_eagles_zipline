/**
 * Black Eagles Zipline - Public Experience Scripts
 * Developed for PL SOFT TECH SOLUTIONS
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Transparent Navbar to Frosted Glass on Scroll
  const navbar = document.querySelector('.navbar-adventure');
  if (navbar) {
    const handleScroll = () => {
      if (window.scrollY > 40) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }

  // 2. Interactive Lightbox for Gallery Photos
  const galleryCards = document.querySelectorAll('.gallery-card');
  const lightboxModalEl = document.getElementById('galleryLightboxModal');
  const lightboxImg = document.getElementById('lightboxImage');
  const lightboxTitle = document.getElementById('lightboxTitle');
  const lightboxCaption = document.getElementById('lightboxCaption');

  if (lightboxModalEl && galleryCards.length > 0) {
    const bsModal = new bootstrap.Modal(lightboxModalEl);

    galleryCards.forEach(card => {
      card.addEventListener('click', function () {
        const src = this.getAttribute('data-img-src');
        const title = this.getAttribute('data-img-title') || 'Adventure Photograph';
        const caption = this.getAttribute('data-img-caption') || '';

        if (lightboxImg) {
          lightboxImg.src = src;
          lightboxImg.alt = title;
        }
        if (lightboxTitle) lightboxTitle.textContent = title;
        if (lightboxCaption) lightboxCaption.textContent = caption;

        bsModal.show();
      });
    });
  }

  // 3. Smooth scrolling for hash anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId !== '#') {
        const targetEl = document.querySelector(targetId);
        if (targetEl) {
          e.preventDefault();
          targetEl.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });

  // 4. Mobile Nav auto-collapse on item click
  const navCollapse = document.getElementById('mainNav');
  const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
  if (navCollapse && navLinks.length > 0) {
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 992 && navCollapse.classList.contains('show')) {
          const bsCollapse = bootstrap.Collapse.getInstance(navCollapse);
          if (bsCollapse) bsCollapse.hide();
        }
      });
    });
  }
});
