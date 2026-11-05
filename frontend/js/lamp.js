/**
 * Lamp Effect Interactive Controller — Aceternity UI style
 * Provides subtle interactive lighting and responsive beam alignment with the dark blue gradient theme.
 */
(function () {
  'use strict';

  function initLamp() {
    const lamp = document.getElementById('hero-lamp');
    if (!lamp) return;

    const beamLeft = lamp.querySelector('.lamp-beam-left');
    const beamRight = lamp.querySelector('.lamp-beam-right');
    const lampLine = lamp.querySelector('.lamp-line');
    const coreGlow = lamp.querySelector('.lamp-core-glow');

    let mouseX = 0;
    let targetX = 0;
    let isHovering = false;

    lamp.addEventListener('mousemove', (e) => {
      const rect = lamp.getBoundingClientRect();
      const relativeX = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 to 0.5
      targetX = relativeX * 24; // subtle max shift in px
      isHovering = true;
    });

    lamp.addEventListener('mouseleave', () => {
      targetX = 0;
      isHovering = false;
    });

    function animate() {
      mouseX += (targetX - mouseX) * 0.08;

      if (lampLine && (isHovering || Math.abs(mouseX) > 0.05)) {
        lampLine.style.transform = `translateX(calc(-50% + ${mouseX * 0.4}px))`;
      }
      if (coreGlow && (isHovering || Math.abs(mouseX) > 0.05)) {
        coreGlow.style.transform = `translate(calc(-50% + ${mouseX * 0.6}px), -35%)`;
      }
      if (beamLeft && (isHovering || Math.abs(mouseX) > 0.05)) {
        beamLeft.style.transform = `skewX(${mouseX * 0.25}deg)`;
      }
      if (beamRight && (isHovering || Math.abs(mouseX) > 0.05)) {
        beamRight.style.transform = `skewX(${mouseX * 0.25}deg)`;
      }

      requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLamp);
  } else {
    initLamp();
  }
})();

