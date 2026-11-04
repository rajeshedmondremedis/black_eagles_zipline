/**
 * Black Eagles Zipline - Main Website Scripts
 * Developed for PL SOFT TECH SOLUTIONS
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Transparent Navbar to Solid on Scroll
  const navbar = document.querySelector('.navbar-adventure');
  if (navbar) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  // 2. Simple Image Lightbox Modal for Gallery
  const galleryCards = document.querySelectorAll('.gallery-card');
  const lightboxModal = document.getElementById('galleryLightboxModal');
  const lightboxImg = document.getElementById('lightboxImage');
  const lightboxTitle = document.getElementById('lightboxTitle');
  const lightboxCaption = document.getElementById('lightboxCaption');

  if (lightboxModal && galleryCards.length > 0) {
    galleryCards.forEach(card => {
      card.addEventListener('click', function () {
        const src = this.getAttribute('data-img-src');
        const title = this.getAttribute('data-img-title');
        const caption = this.getAttribute('data-img-caption');

        if (lightboxImg) lightboxImg.src = src;
        if (lightboxTitle) lightboxTitle.textContent = title;
        if (lightboxCaption) lightboxCaption.textContent = caption;

        const modal = new bootstrap.Modal(lightboxModal);
        modal.show();
      });
    });
  }
});

