/* anim.js – vanilla JS utilities for scroll‑triggered animations */

/**
 * Checks if user prefers reduced motion and disables animations accordingly.
 */
function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Observe elements with a `data-anim` attribute and add the corresponding CSS class
 * when they enter the viewport. The `data-anim` value should match a CSS class
 * defined in `animations.css` (e.g., "fade-up", "slide-up", "scale-up").
 */
function initScrollAnimations() {
  if (prefersReducedMotion()) return; // Skip entirely.
  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const animClass = el.dataset.anim;
        if (animClass) el.classList.add(animClass);
        obs.unobserve(el); // Animate once.
      }
    });
  }, {
    threshold: 0.15,
  });

  document.querySelectorAll('[data-anim]').forEach(el => observer.observe(el));
}

/**
 * Simple scroll handler for the landing navbar – adds the `.scrolled` class
 * once the page has been scrolled a bit, to trigger the background transition.
 */
function initNavbarScroll() {
  const navbar = document.querySelector('.landing-navbar');
  if (!navbar) return;
  const toggle = () => {
    if (window.scrollY > 40) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  };
  window.addEventListener('scroll', toggle);
  // Initialise on load.
  toggle();
}

/**
 * Initialise all animation helpers after DOM ready.
 */
document.addEventListener('DOMContentLoaded', () => {
  initNavbarScroll();
  initScrollAnimations();
});

