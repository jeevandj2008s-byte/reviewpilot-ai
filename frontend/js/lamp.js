/**
 * ReviewPilot Vela Dynamic Hero & Rotating Terms Controller
 * Cycles through the 4 terms with custom 3D badges and morphing pastel auras.
 */
(function () {
  'use strict';

  const TERMS = [
    {
      term: 'Analyze reviews',
      tag: 'in your terms',
      badgeBg: 'linear-gradient(135deg, #ffe4e6 0%, #fecdd3 100%)',
      badgeBorder: 'rgba(244, 63, 94, 0.25)',
      primaryAura: 'radial-gradient(circle, #fecdd3 0%, #ffe4e6 45%, rgba(254, 205, 211, 0) 70%)',
      secondaryAura: 'radial-gradient(circle, #fef3c7 0%, rgba(254, 243, 199, 0) 70%)',
      // 3D holographic wireframe sphere
      iconSvg: `
        <svg width="26" height="26" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" fill="url(#grad-sphere-1)" stroke="#f43f5e" stroke-width="1.2"/>
          <ellipse cx="16" cy="16" rx="14" ry="5.5" stroke="#f43f5e" stroke-width="1" stroke-dasharray="2 2"/>
          <ellipse cx="16" cy="16" rx="5.5" ry="14" stroke="#f43f5e" stroke-width="1" stroke-dasharray="2 2"/>
          <circle cx="12" cy="12" r="3" fill="#ffffff" opacity="0.6"/>
          <defs>
            <linearGradient id="grad-sphere-1" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
              <stop stop-color="#fff1f2"/>
              <stop offset="1" stop-color="#fecdd3"/>
            </linearGradient>
          </defs>
        </svg>
      `
    },
    {
      term: 'Reply politely',
      tag: 'in your terms',
      badgeBg: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
      badgeBorder: 'rgba(245, 158, 11, 0.25)',
      primaryAura: 'radial-gradient(circle, #fef08a 0%, #fef3c7 45%, rgba(254, 240, 138, 0) 70%)',
      secondaryAura: 'radial-gradient(circle, #fed7aa 0%, rgba(254, 215, 170, 0) 70%)',
      // 3D glossy chat bubble
      iconSvg: `
        <svg width="26" height="26" viewBox="0 0 32 32" fill="none">
          <path d="M6 14.5C6 9.8 9.8 6 14.5 6h3C22.2 6 26 9.8 26 14.5c0 4.7-3.8 8.5-8.5 8.5H12l-5 4v-4.8C6 20.7 6 18.8 6 14.5z" fill="url(#grad-bubble-2)" stroke="#d97706" stroke-width="1.2"/>
          <ellipse cx="13" cy="11" rx="4" ry="1.8" fill="#ffffff" opacity="0.7"/>
          <circle cx="12" cy="15" r="1.5" fill="#b45309"/>
          <circle cx="16" cy="15" r="1.5" fill="#b45309"/>
          <circle cx="20" cy="15" r="1.5" fill="#b45309"/>
          <defs>
            <linearGradient id="grad-bubble-2" x1="6" y1="6" x2="26" y2="26" gradientUnits="userSpaceOnUse">
              <stop stop-color="#fffbeb"/>
              <stop offset="1" stop-color="#fde68a"/>
            </linearGradient>
          </defs>
        </svg>
      `
    },
    {
      term: 'Protect brand',
      tag: 'in your terms',
      badgeBg: 'linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%)',
      badgeBorder: 'rgba(234, 88, 12, 0.25)',
      primaryAura: 'radial-gradient(circle, #fed7aa 0%, #ffedd5 45%, rgba(254, 215, 170, 0) 70%)',
      secondaryAura: 'radial-gradient(circle, #fecdd3 0%, rgba(254, 205, 211, 0) 70%)',
      // 3D star shield
      iconSvg: `
        <svg width="26" height="26" viewBox="0 0 32 32" fill="none">
          <path d="M16 4l10 4v7c0 7.5-4.5 12.5-10 14-5.5-1.5-10-6.5-10-14V8l10-4z" fill="url(#grad-shield-3)" stroke="#ea580c" stroke-width="1.2"/>
          <path d="M16 10l1.8 3.6 4 .6-2.9 2.8.7 4-3.6-1.9-3.6 1.9.7-4-2.9-2.8 4-.6L16 10z" fill="#ea580c"/>
          <defs>
            <linearGradient id="grad-shield-3" x1="6" y1="4" x2="26" y2="28" gradientUnits="userSpaceOnUse">
              <stop stop-color="#fff7ed"/>
              <stop offset="1" stop-color="#fed7aa"/>
            </linearGradient>
          </defs>
        </svg>
      `
    },
    {
      term: 'Grow revenue',
      tag: 'in your terms',
      badgeBg: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
      badgeBorder: 'rgba(5, 150, 105, 0.25)',
      primaryAura: 'radial-gradient(circle, #a7f3d0 0%, #d1fae5 45%, rgba(167, 243, 208, 0) 70%)',
      secondaryAura: 'radial-gradient(circle, #fef3c7 0%, rgba(254, 243, 199, 0) 70%)',
      // 3D rising growth arrows
      iconSvg: `
        <svg width="26" height="26" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="13" fill="url(#grad-growth-4)" stroke="#059669" stroke-width="1.2"/>
          <path d="M10 20l5-5 3.5 3.5 5.5-6.5" stroke="#047857" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M19 12h5v5" stroke="#047857" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          <defs>
            <linearGradient id="grad-growth-4" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
              <stop stop-color="#ecfdf5"/>
              <stop offset="1" stop-color="#a7f3d0"/>
            </linearGradient>
          </defs>
        </svg>
      `
    }
  ];

  let currentIndex = 0;
  let cycleInterval = null;

  function initHeroCycle() {
    const termEl = document.getElementById('hero-rotating-term');
    const badgeEl = document.getElementById('hero-3d-badge');
    const pillEl = document.getElementById('hero-rotator-pill');
    const auraPrimary = document.getElementById('hero-aura-primary');
    const auraSecondary = document.getElementById('hero-aura-secondary');

    if (!termEl || !badgeEl) return;

    function applyTerm(index, animate = true) {
      const item = TERMS[index];
      if (!item) return;

      if (animate) {
        termEl.style.opacity = '0';
        termEl.style.transform = 'translateY(8px)';
        badgeEl.style.transform = 'scale(0.8) rotate(-10deg)';

        setTimeout(() => {
          termEl.textContent = item.term;
          badgeEl.innerHTML = item.iconSvg;
          badgeEl.style.background = item.badgeBg;
          badgeEl.style.border = `1px solid ${item.badgeBorder}`;

          if (auraPrimary) auraPrimary.style.background = item.primaryAura;
          if (auraSecondary) auraSecondary.style.background = item.secondaryAura;

          termEl.style.opacity = '1';
          termEl.style.transform = 'translateY(0)';
          badgeEl.style.transform = 'scale(1) rotate(0deg)';
        }, 220);
      } else {
        termEl.textContent = item.term;
        badgeEl.innerHTML = item.iconSvg;
        badgeEl.style.background = item.badgeBg;
        badgeEl.style.border = `1px solid ${item.badgeBorder}`;

        if (auraPrimary) auraPrimary.style.background = item.primaryAura;
        if (auraSecondary) auraSecondary.style.background = item.secondaryAura;
      }
    }

    // Apply first term immediately
    applyTerm(0, false);

    // Transition styles
    termEl.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
    badgeEl.style.transition = 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)';

    // Cycle every 2.8s
    if (cycleInterval) clearInterval(cycleInterval);
    cycleInterval = setInterval(() => {
      currentIndex = (currentIndex + 1) % TERMS.length;
      applyTerm(currentIndex, true);
    }, 2800);

    // Subtle mouse parallax on hero container
    const hero = document.getElementById('hero-vela');
    if (hero) {
      hero.addEventListener('mousemove', (e) => {
        const rect = hero.getBoundingClientRect();
        const normX = (e.clientX - rect.left) / rect.width - 0.5;
        const normY = (e.clientY - rect.top) / rect.height - 0.5;

        if (auraPrimary) {
          auraPrimary.style.transform = `translate(calc(-50% + ${normX * 24}px), ${normY * 16}px)`;
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHeroCycle);
  } else {
    initHeroCycle();
  }
})();
