
      import * as THREE from 'three';
      import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

      const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      // --- 3.1 Nav toggles & 6. Smooth scroll (Lenis) ---
      const themeBtn = document.getElementById('themeBtn');
      const soundBtn = document.getElementById('soundBtn');
      let themeB = false;
      let soundOn = false;

      themeBtn?.addEventListener('click', () => {
        themeB = !themeB;
        themeBtn.textContent = themeB ? 'THEME[B]' : 'THEME[A]';
        document.documentElement.style.filter = themeB ? 'hue-rotate(-28deg) saturate(1.1)' : '';
      });

      soundBtn?.addEventListener('click', () => {
        soundOn = !soundOn;
        soundBtn.textContent = soundOn ? 'SOUND[+]' : 'SOUND[-]';
      });

      let lenis = null;
      if (!reducedMotion && typeof window.Lenis !== 'undefined') {
        lenis = new window.Lenis({
          lerp: 0.1,
          smoothWheel: true,
        });
      }

      document.querySelectorAll('a[href^="#"]').forEach((link) => {
        link.addEventListener('click', (e) => {
          const href = link.getAttribute('href');
          if (!href) return;
          const targetNav = link.getAttribute('data-navigate');
          if (targetNav && typeof window.navigateTo === 'function') {
            e.preventDefault();
            window.navigateTo(targetNav);
            return;
          }
          if (href === '#dashboard' || href === '#analyzer' || href === '#settings') {
            if (typeof window.navigateTo === 'function') {
              e.preventDefault();
              window.navigateTo(href.replace('#', ''));
              return;
            }
          }
          if (href === '#') {
            e.preventDefault();
            if (lenis) lenis.scrollTo(0);
            else window.scrollTo({ top: 0, behavior: reducedMotion ? 'auto' : 'smooth' });
            return;
          }
          const target = document.querySelector(href);
          if (target) {
            e.preventDefault();
            if (lenis) lenis.scrollTo(href);
            else target.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth' });
          }
        });
      });

      // --- 3.2 Footer live clock & pointer coords ---
      const clockEl = document.getElementById('clock');
      const coordsEl = document.getElementById('coords');

      function updateClock() {
        if (!clockEl) return;
        const now = new Date();
        const offMin = -now.getTimezoneOffset();
        const offHrs = offMin / 60;
        const sign = offHrs >= 0 ? '+' : '-';
        const absHrs = Math.abs(offHrs);
        const hStr = Number.isInteger(absHrs) ? String(absHrs) : absHrs.toFixed(1);
        const hh = String(now.getHours()).padStart(2, '0');
        const mm = String(now.getMinutes()).padStart(2, '0');
        clockEl.textContent = `GMT${sign}${hStr}  ${hh}:${mm}`;
      }
      updateClock();
      setInterval(updateClock, 10000);

      // --- 4.3 Hero Entrance ---
      const easeOutExpo = 'cubic-bezier(.16,1,.3,1)';
      let heroAnimStarted = false;

      function startHeroEntrance() {
        if (heroAnimStarted) return;
        heroAnimStarted = true;
        document.documentElement.classList.remove('anim');
        if (reducedMotion) return;

        const heroGrid = document.querySelector('.hero-grid');
        const nav = document.querySelector('.site-nav');
        const footer = document.querySelector('.site-footer');
        const lede = document.querySelector('.hero-lede');
        const mono1 = document.querySelector('.hero-mono-1');
        const mono2 = document.querySelector('.hero-mono-2');
        const hlLines = document.querySelectorAll('.hero-headline .hl-line em');

        heroGrid?.animate([{ opacity: 0 }, { opacity: 1 }], {
          duration: 900,
          delay: 300,
          easing: 'linear',
          fill: 'both',
        });

        [nav, footer].forEach((el) => {
          el?.animate(
            [
              { opacity: 0, transform: 'translateY(-8px)' },
              { opacity: 1, transform: 'translateY(0)' },
            ],
            { duration: 900, delay: 350, easing: easeOutExpo, fill: 'both' }
          );
        });

        [lede, mono1, mono2].forEach((el, idx) => {
          el?.animate(
            [
              { opacity: 0, transform: 'translateY(14px)' },
              { opacity: 1, transform: 'translateY(0)' },
            ],
            { duration: 1000, delay: 500 + idx * 110, easing: easeOutExpo, fill: 'both' }
          );
        });

        hlLines.forEach((em, idx) => {
          em.animate(
            [
              { transform: 'translateY(105%)' },
              { transform: 'translateY(0)' },
            ],
            { duration: 1200, delay: 650 + idx * 120, easing: easeOutExpo, fill: 'both' }
          );
        });
      }

      if (reducedMotion) {
        document.documentElement.classList.remove('anim');
      } else {
        const failsafe = setTimeout(startHeroEntrance, 3500);
        if (document.fonts && document.fonts.ready) {
          document.fonts.ready.then(() => {
            clearTimeout(failsafe);
            startHeroEntrance();
          });
        } else {
          startHeroEntrance();
        }
      }

      // --- 5.6 About Entrance ---
      const aboutSection = document.getElementById('about');
      const portraitCard = document.getElementById('portraitCard');
      const neonSig = document.getElementById('neonSig');
      const aboutRows = document.querySelectorAll('.about-row');

      if (reducedMotion) {
        if (portraitCard) portraitCard.style.opacity = '1';
        if (neonSig) neonSig.style.opacity = '1';
        aboutRows.forEach((r) => (r.style.opacity = '1'));
      } else if (aboutSection) {
        let aboutTriggered = false;
        const io = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting && !aboutTriggered) {
                aboutTriggered = true;
                io.disconnect();

                if (portraitCard) {
                  const cardAnim = portraitCard.animate(
                    [
                      { opacity: 0, clipPath: 'inset(100% 0 0 0)', transform: 'translateY(20px)' },
                      { opacity: 1, clipPath: 'inset(0 0 0 0)', transform: 'translateY(0)' },
                    ],
                    { duration: 1100, easing: easeOutExpo, fill: 'both' }
                  );
                  cardAnim.onfinish = () => {
                    portraitCard.style.opacity = '1';
                    portraitCard.style.clipPath = 'none';
                    portraitCard.style.transform = 'none';
                    cardAnim.cancel();
                  };
                }

                if (neonSig) {
                  const sigAnim = neonSig.animate(
                    [
                      { clipPath: 'inset(-60% 100% -60% -20%)', opacity: 0, offset: 0 },
                      { clipPath: 'inset(-60% 40% -60% -20%)', opacity: 0.4, offset: 0.6 },
                      { clipPath: 'inset(-60% -20% -60% -20%)', opacity: 1, offset: 1 },
                    ],
                    { duration: 1300, delay: 450, easing: 'cubic-bezier(.55,.1,.3,1)', fill: 'both' }
                  );
                  sigAnim.onfinish = () => {
                    neonSig.style.opacity = '1';
                    neonSig.style.clipPath = 'none';
                    sigAnim.cancel();
                  };

                  neonSig.animate(
                    [
                      { opacity: 1 },
                      { opacity: 0.82 },
                      { opacity: 1 },
                      { opacity: 0.9 },
                      { opacity: 1 },
                    ],
                    { duration: 4200, delay: 1800, iterations: Infinity }
                  );
                }

                aboutRows.forEach((row, idx) => {
                  const rowAnim = row.animate(
                    [
                      { opacity: 0, transform: 'translateY(22px)' },
                      { opacity: 1, transform: 'translateY(0)' },
                    ],
                    { duration: 1000, delay: 150 + idx * 80, easing: easeOutExpo, fill: 'both' }
                  );
                  rowAnim.onfinish = () => {
                    row.style.opacity = '1';
                    row.style.transform = 'none';
                    rowAnim.cancel();
                  };
                });
              }
            });
          },
          { threshold: 0.4 }
        );
        io.observe(aboutSection);
      }

      // --- Shared Calligraphic "Review Pilot" Stroke Data ---
      const REVIEW_PILOT_STROKES = [
        // 1. Capital "R" main vertical stem
        {
          radius: 0.28,
          segs: 96,
          pts: [
            [-10.20, 4.40, 0.05],
            [-10.25, 3.00, -0.05],
            [-10.32, 1.50, -0.10],
            [-10.42, 0.05, -0.12],
          ],
        },
        // 2. Capital "R" upper bowl
        {
          radius: 0.28,
          segs: 180,
          pts: [
            [-10.65, 3.85, 0.18],
            [-9.95, 4.50, 0.22],
            [-8.85, 4.45, 0.20],
            [-8.25, 3.70, 0.12],
            [-8.45, 2.85, 0.05],
            [-9.35, 2.42, 0.08],
            [-10.18, 2.38, 0.12],
          ],
        },
        // 3. Capital "R" diagonal leg flowing into first "e" loop and up to "v"
        {
          radius: 0.28,
          segs: 320,
          pts: [
            [-9.45, 2.38, 0.16],
            [-8.85, 1.75, 0.12],
            [-8.42, 0.72, -0.05],
            [-7.95, 0.04, -0.10],
            [-7.25, 0.48, 0.10],
            // first "e" open loop
            [-6.55, 1.15, 0.20],
            [-6.18, 1.68, 0.18],
            [-6.55, 2.12, 0.05],
            [-7.18, 1.75, -0.15],
            [-7.32, 0.92, -0.22],
            [-6.95, 0.12, -0.18],
            [-6.35, 0.02, -0.10],
            [-5.68, 0.85, 0.08],
            [-5.25, 2.05, 0.15],
          ],
        },
        // 4. Lowercase "v" bowl + cursive bridge to top of "i"
        {
          radius: 0.28,
          segs: 180,
          pts: [
            [-5.25, 2.05, 0.15],
            [-5.00, 0.95, -0.10],
            [-4.68, 0.06, -0.18],
            [-4.42, 0.06, -0.15],
            [-4.08, 0.95, 0.08],
            [-3.82, 2.05, 0.18],
            [-3.45, 1.78, 0.16],
            [-3.02, 2.05, 0.12],
          ],
        },
        // 5. Lowercase "i" stem flowing into second "e" open loop and up to "w"
        {
          radius: 0.28,
          segs: 300,
          pts: [
            [-3.02, 2.05, 0.12],
            [-3.08, 1.00, -0.12],
            [-2.92, 0.12, -0.18],
            [-2.52, 0.04, -0.08],
            [-1.85, 0.65, 0.12],
            // second "e" open loop
            [-1.22, 1.25, 0.20],
            [-0.92, 1.72, 0.18],
            [-1.28, 2.12, 0.05],
            [-1.92, 1.75, -0.15],
            [-2.05, 0.92, -0.22],
            [-1.68, 0.12, -0.18],
            [-1.08, 0.02, -0.10],
            [-0.48, 0.85, 0.08],
            [-0.12, 2.05, 0.15],
          ],
        },
        // 6. Lowercase "w" first bowl
        {
          radius: 0.28,
          segs: 140,
          pts: [
            [-0.12, 2.05, 0.15],
            [-0.02, 0.95, -0.12],
            [0.28, 0.06, -0.18],
            [0.58, 0.12, -0.12],
            [0.88, 1.05, 0.08],
            [1.02, 1.92, 0.16],
          ],
        },
        // 7. Lowercase "w" second bowl + rising exit flick
        {
          radius: 0.28,
          segs: 160,
          pts: [
            [1.02, 1.92, 0.16],
            [1.18, 0.95, -0.12],
            [1.48, 0.06, -0.18],
            [1.78, 0.12, -0.12],
            [2.12, 1.05, 0.10],
            [2.25, 2.05, 0.18],
            [2.68, 1.88, 0.15],
          ],
        },
        // 8. Capital "P" main vertical stem
        {
          radius: 0.28,
          segs: 96,
          pts: [
            [4.15, 4.40, 0.05],
            [4.08, 3.00, -0.05],
            [4.00, 1.50, -0.10],
            [3.90, 0.05, -0.12],
          ],
        },
        // 9. Capital "P" upper bowl
        {
          radius: 0.28,
          segs: 180,
          pts: [
            [3.68, 3.85, 0.18],
            [4.38, 4.50, 0.22],
            [5.48, 4.42, 0.20],
            [6.05, 3.65, 0.12],
            [5.82, 2.75, 0.05],
            [4.95, 2.32, 0.08],
            [4.05, 2.28, 0.12],
          ],
        },
        // 10. Lead-in ligature to "i" in "Pilot"
        {
          radius: 0.28,
          segs: 72,
          pts: [
            [4.75, 0.75, 0.08],
            [5.12, 1.42, 0.12],
            [5.45, 2.05, 0.15],
          ],
        },
        // 11. "i" down-stem flowing into tall open "l" loop and ligature to "o"
        {
          radius: 0.28,
          segs: 340,
          pts: [
            [5.45, 2.05, 0.15],
            [5.38, 0.95, -0.12],
            [5.55, 0.08, -0.18],
            [6.02, 0.12, -0.05],
            // tall open "l" loop
            [6.58, 1.15, 0.18],
            [7.12, 2.55, 0.24],
            [7.42, 3.78, 0.20],
            [7.22, 4.48, 0.05],
            [6.72, 4.35, -0.12],
            [6.42, 3.35, -0.25],
            [6.32, 1.95, -0.28],
            [6.42, 0.75, -0.25],
            [6.72, 0.06, -0.15],
            [7.22, 0.12, 0.02],
            [7.75, 0.95, 0.12],
            [8.15, 1.68, 0.15],
          ],
        },
        // 12. Closed "o" loop + upper tie sweeping up to top of "t"
        {
          radius: 0.28,
          segs: 280,
          pts: [
            [8.85, 1.92, 0.12],
            [8.42, 2.12, 0.08],
            [7.92, 1.62, -0.15],
            [7.85, 0.75, -0.22],
            [8.28, 0.05, -0.20],
            [8.88, 0.12, -0.12],
            [9.32, 0.82, 0.05],
            [9.25, 1.72, 0.16],
            [8.72, 1.95, 0.22],
            [8.65, 1.58, 0.24],
            [9.22, 1.52, 0.22],
            [9.85, 2.55, 0.18],
            [10.28, 3.85, 0.12],
          ],
        },
        // 13. Tall "t" down-stem + rising exit tail
        {
          radius: 0.28,
          segs: 150,
          pts: [
            [10.28, 3.85, 0.12],
            [10.20, 2.50, -0.12],
            [10.12, 1.10, -0.20],
            [10.28, 0.12, -0.18],
            [10.72, 0.05, -0.08],
            [11.28, 0.55, 0.10],
            [11.75, 1.28, 0.18],
          ],
        },
        // 14. Horizontal crossbar on "t"
        {
          radius: 0.24,
          segs: 72,
          pts: [
            [9.55, 2.82, 0.26],
            [10.22, 2.88, 0.28],
            [10.92, 2.94, 0.24],
          ],
        },
      ];

      const REVIEW_PILOT_DOTS = [
        [-2.98, 2.88, 0.14, 0.34],
        [5.48, 2.88, 0.14, 0.34],
      ];

      // --- 7. WebGL Scene (with pre-probed context so THREE.WebGLRenderer never logs errors when WebGL is disabled) ---
      const canvas = document.getElementById('gl');
      const heroEl = document.getElementById('hero');
      const isPhone = () => window.innerWidth < 820;

      // Pointer tracking shared across WebGL and Canvas2D fallback
      const pointer = {
        uv: new THREE.Vector2(0.5, 0.5),
        inside: false,
        bufPos: new THREE.Vector2(0, 0),
        prevBufPos: new THREE.Vector2(0, 0),
        delta: new THREE.Vector2(0, 0),
        lastMoveTime: 0,
        hasMoved: false,
      };

      window.addEventListener('pointermove', (e) => {
        const w = window.innerWidth;
        const h = window.innerHeight;
        const cx = Math.max(0, Math.min(1440, Math.round((e.clientX / w) * 1440)));
        const cy = Math.max(0, Math.min(900, Math.round((e.clientY / h) * 900)));
        if (coordsEl) {
          coordsEl.textContent = `${String(cx).padStart(4, '0')} X ${String(cy).padStart(4, '0')} Y`;
        }

        if (e.pointerType === 'mouse' || e.pointerType === 'pen' || !e.pointerType) {
          pointer.uv.set(e.clientX / w, 1 - e.clientY / h);
          pointer.inside = true;
          const dpr = Math.min(window.devicePixelRatio || 1, 2);
          const bx = e.clientX * dpr;
          const by = (h - e.clientY) * dpr;
          if (!pointer.hasMoved) {
            pointer.prevBufPos.set(bx, by);
            pointer.hasMoved = true;
          } else {
            pointer.prevBufPos.copy(pointer.bufPos);
          }
          pointer.bufPos.set(bx, by);
          const dx = pointer.bufPos.x - pointer.prevBufPos.x;
          const dy = pointer.bufPos.y - pointer.prevBufPos.y;
          pointer.delta.set(dx, dy);
          if (dx * dx + dy * dy > 1) {
            pointer.lastMoveTime = performance.now();
          }
        }
      });

      const onPointerOut = () => {
        pointer.inside = false;
      };
      document.addEventListener('pointerleave', onPointerOut);
      document.addEventListener('mouseleave', onPointerOut);
      window.addEventListener('blur', onPointerOut);

      // Probe WebGL context safely BEFORE invoking THREE.WebGLRenderer so disabled-GL browsers never emit console errors
      let glContext = null;
      let isSoftwareGl = false;
      let isWebGL2 = false;

      if (canvas) {
        const contextAttempts = [
          ['webgl2', { antialias: true, powerPreference: 'high-performance', alpha: false }],
          ['webgl2', { antialias: false, alpha: false }],
          ['webgl', { antialias: true, alpha: false }],
          ['webgl', { antialias: false, alpha: false }],
          ['experimental-webgl', { antialias: false }],
        ];
        for (const [type, attrs] of contextAttempts) {
          try {
            const probeCanvas = document.createElement('canvas');
            const probeCtx = probeCanvas.getContext(type, attrs);
            if (probeCtx) {
              const ext = probeCtx.getExtension('WEBGL_debug_renderer_info');
              const param = ext ? ext.UNMASKED_RENDERER_WEBGL : probeCtx.RENDERER;
              const gpu = String(probeCtx.getParameter(param) || '');
              isSoftwareGl = /SwiftShader|llvmpipe|softpipe|Software|Basic Render/i.test(gpu);
              probeCtx.getExtension('WEBGL_lose_context')?.loseContext();
              const realCtx = canvas.getContext(type, attrs);
              if (realCtx) {
                glContext = realCtx;
                isWebGL2 = type === 'webgl2';
                break;
              }
            }
          } catch (_) {
            // continue fallback attempts
          }
        }
      }

      let renderer = null;
      if (glContext) {
        try {
          renderer = new THREE.WebGLRenderer({
            canvas,
            context: glContext,
            antialias: !isSoftwareGl,
            powerPreference: 'high-performance',
          });
        } catch (_) {
          renderer = null;
        }
      }

      function cubicBezier(x1, y1, x2, y2, t) {
        if (t <= 0) return 0;
        if (t >= 1) return 1;
        let u = t;
        for (let i = 0; i < 8; i++) {
          const x =
            3 * (1 - u) * (1 - u) * u * x1 +
            3 * (1 - u) * u * u * x2 +
            u * u * u -
            t;
          const dx =
            3 * (1 - u) * (1 - u) * x1 +
            6 * (1 - u) * u * (x2 - x1) +
            3 * u * u * (1 - x2);
          if (Math.abs(dx) < 1e-6) break;
          u -= x / dx;
        }
        return (
          3 * (1 - u) * (1 - u) * u * y1 +
          3 * (1 - u) * u * u * y2 +
          u * u * u
        );
      }

      if (!renderer) {
        // Graceful 3D-Projected Canvas2D Fallback when WebGL is disabled in browser/sandbox
        document.documentElement.classList.add('no-gl');
        const ctx2d = canvas ? canvas.getContext('2d') : null;
        if (ctx2d && canvas) {
          canvas.classList.add('on');
          const deg = THREE.MathUtils.degToRad;
          const sampledStrokes = REVIEW_PILOT_STROKES.map((s) => {
            const curve = new THREE.CatmullRomCurve3(
              s.pts.map(([x, y, z]) => new THREE.Vector3(x * 0.84, (y - 2.1) * 0.78, z * 0.84)),
              false,
              'centripetal'
            );
            return {
              radius: s.radius * 0.84,
              pts: curve.getSpacedPoints(Math.max(24, Math.floor(s.segs / 5))),
            };
          });
          const sampledDots = REVIEW_PILOT_DOTS.map(([x, y, z, r]) => ({
            pos: new THREE.Vector3(x * 0.84, (y - 2.1) * 0.78, z * 0.84),
            radius: r * 0.84,
          }));

          let rotY = reducedMotion ? deg(4) : deg(240);
          const startTime = performance.now();
          let prevTime = startTime;

          function resize2D() {
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            canvas.width = Math.round(window.innerWidth * dpr);
            canvas.height = Math.round(window.innerHeight * dpr);
          }
          resize2D();
          window.addEventListener('resize', resize2D);

          function tick2D(now) {
            if (lenis) lenis.raf(now);
            const dt = Math.min(0.1, Math.max(0.001, (now - prevTime) / 1000));
            prevTime = now;
            const t = (now - startTime) / 1000;
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            const W = canvas.width;
            const H = canvas.height;
            const vh = Math.max(1, window.innerHeight);

            const heroRect = heroEl ? heroEl.getBoundingClientRect() : { top: 0, bottom: vh, height: vh };
            const p = THREE.MathUtils.clamp((vh - heroRect.bottom) / (vh - 0.25 * vh), 0, 1);

            // Background streaky teal gradient
            const px = pointer.inside ? pointer.uv.x * W : W * 0.5;
            const py = pointer.inside ? (1 - pointer.uv.y) * H : H * 0.5;
            const bgGrad = ctx2d.createRadialGradient(px, py, W * 0.05, W * 0.5, H * 0.5, Math.max(W, H) * 0.75);
            bgGrad.addColorStop(0, '#5cd8c4');
            bgGrad.addColorStop(0.45, '#135e59');
            bgGrad.addColorStop(1, '#06252c');
            ctx2d.fillStyle = bgGrad;
            ctx2d.fillRect(0, 0, W, H);

            // 3D rotation sequence (before 240 deg -> rest 4 deg -> after 90 deg)
            const scrollY = window.scrollY || window.pageYOffset || 0;
            const heroTopDoc = heroRect.top + scrollY;
            const rawEntry = (scrollY + vh - heroTopDoc) / vh;
            const entry = THREE.MathUtils.clamp(rawEntry, 0, 1);
            const after = THREE.MathUtils.clamp(rawEntry - 1, 0, 1);
            const rEntry = THREE.MathUtils.lerp(deg(240), deg(4), entry);
            const rTarget = THREE.MathUtils.lerp(rEntry, deg(90), after);
            rotY = reducedMotion ? rTarget : THREE.MathUtils.damp(rotY, rTarget, 6, dt);

            const baseZ = THREE.MathUtils.lerp(24, 32, p);
            const introP = reducedMotion ? 1 : Math.min(1, t / 1.2);
            const camZ = THREE.MathUtils.lerp(baseZ + 8, baseZ, cubicBezier(0.66, 0, 0.01, 1, introP));
            const floatY = !isPhone() && !reducedMotion ? 0.18 * Math.sin(1.2 * t) + 0.06 * Math.sin(0.6 * t) : 0;
            const scalePx = (Math.min(W, H) * 0.95) / camZ;
            const cosY = Math.cos(rotY);
            const sinY = Math.sin(rotY);
            const cyOff = H * 0.47 - scrollY * dpr * 0.72;

            if (p < 0.99) {
              ctx2d.save();
              ctx2d.lineCap = 'round';
              ctx2d.lineJoin = 'round';

              sampledStrokes.forEach((s) => {
                ctx2d.beginPath();
                s.pts.forEach((pt, idx) => {
                  const rx = pt.x * cosY + pt.z * sinY;
                  const rz = -pt.x * sinY + pt.z * cosY;
                  const ry = pt.y + floatY;
                  const persp = camZ / Math.max(4, camZ - rz - 2);
                  const sx = W * 0.5 + rx * scalePx * persp;
                  const sy = cyOff - ry * scalePx * persp;
                  if (idx === 0) ctx2d.moveTo(sx, sy);
                  else ctx2d.lineTo(sx, sy);
                });
                ctx2d.strokeStyle = 'rgba(130, 232, 212, 0.82)';
                ctx2d.lineWidth = s.radius * 2 * scalePx;
                ctx2d.stroke();

                ctx2d.strokeStyle = 'rgba(239, 255, 251, 0.92)';
                ctx2d.lineWidth = s.radius * 0.9 * scalePx;
                ctx2d.stroke();
              });

              sampledDots.forEach((d) => {
                const rx = d.pos.x * cosY + d.pos.z * sinY;
                const rz = -d.pos.x * sinY + d.pos.z * cosY;
                const ry = d.pos.y + floatY;
                const persp = camZ / Math.max(4, camZ - rz - 2);
                const sx = W * 0.5 + rx * scalePx * persp;
                const sy = cyOff - ry * scalePx * persp;
                ctx2d.beginPath();
                ctx2d.arc(sx, sy, d.radius * scalePx * persp, 0, Math.PI * 2);
                ctx2d.fillStyle = 'rgba(225, 255, 248, 0.9)';
                ctx2d.fill();
              });

              ctx2d.restore();
            }

            if (p > 0.01) {
              ctx2d.fillStyle = `rgba(9, 22, 24, ${p})`;
              ctx2d.fillRect(0, 0, W, H);
            }

            requestAnimationFrame(tick2D);
          }
          requestAnimationFrame(tick2D);
        }
      }

      if (renderer) {
        const getDpr = () => (isSoftwareGl ? 1 : Math.min(window.devicePixelRatio || 1, 2));
        renderer.setPixelRatio(getDpr());
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.toneMapping = THREE.NoToneMapping;
        renderer.setClearColor(0x091618, 1);

        const rtType = isWebGL2 ? THREE.HalfFloatType : THREE.UnsignedByteType;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 200);
        camera.layers.enable(0);
        camera.layers.enable(10);

        const orthoCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
        const fsQuadGeo = new THREE.PlaneGeometry(2, 2);

        function updateCameraFov() {
          const w = window.innerWidth;
          const h = window.innerHeight;
          const aspect = w / Math.max(1, h);
          const hfovDeg = w >= 1024 ? 60 : 38;
          const hfovRad = (hfovDeg * Math.PI) / 180;
          const vfovRad = 2 * Math.atan(Math.tan(hfovRad / 2) / aspect);
          camera.fov = (vfovRad * 180) / Math.PI;
          camera.aspect = aspect;
          camera.updateProjectionMatrix();
        }
        updateCameraFov();

        // 128x128 greyscale noise texture
        const noiseSize = 128;
        const noiseData = new Uint8Array(noiseSize * noiseSize * 4);
        for (let i = 0; i < noiseSize * noiseSize; i++) {
          const v = Math.floor(Math.random() * 256);
          noiseData[i * 4 + 0] = v;
          noiseData[i * 4 + 1] = v;
          noiseData[i * 4 + 2] = v;
          noiseData[i * 4 + 3] = 255;
        }
        const noiseTex = new THREE.DataTexture(noiseData, noiseSize, noiseSize, THREE.RGBAFormat);
        noiseTex.wrapS = THREE.RepeatWrapping;
        noiseTex.wrapT = THREE.RepeatWrapping;
        noiseTex.minFilter = THREE.LinearFilter;
        noiseTex.magFilter = THREE.LinearFilter;
        noiseTex.needsUpdate = true;

        // --- 7.1 Background Stack (5 ping-pong passes at 0.3x CSS viewport) ---
        const getBgSize = () => ({
          w: Math.max(2, Math.round(window.innerWidth * 0.3)),
          h: Math.max(2, Math.round(window.innerHeight * 0.3)),
        });
        let bgSize = getBgSize();
        const rtOpts = {
          minFilter: THREE.LinearFilter,
          magFilter: THREE.LinearFilter,
          format: THREE.RGBAFormat,
          depthBuffer: false,
          stencilBuffer: false,
        };
        let bgRtA = new THREE.WebGLRenderTarget(bgSize.w, bgSize.h, rtOpts);
        let bgRtB = new THREE.WebGLRenderTarget(bgSize.w, bgSize.h, rtOpts);

        const passVert = `
          varying vec2 vUv;
          void main() {
            vUv = uv;
            gl_Position = vec4(position.xy, 0.0, 1.0);
          }
        `;

        const cBgLinear = new THREE.Color('#86ead6').convertSRGBToLinear();
        const cVigLinear = new THREE.Color('#06252c').convertSRGBToLinear();
        const cOutLinear = new THREE.Color('#0f6b66').convertSRGBToLinear();

        // Pass 1: Vignette
        const matVignette = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform vec2 uP;
            uniform float uAspect;
            uniform vec3 uBg;
            uniform vec3 uVig;
            void main() {
              vec2 a = vec2(uAspect, 1.0);
              vec2 s = vec2(0.54, 0.46);
              float h = 0.354 * 0.5;
              float d = distance(vUv * a * s, uP * a * s);
              float f = smoothstep(h - 0.5 * h, h + 0.5 * h, d);
              f = mix(f, 1.0, 0.82);
              gl_FragColor = vec4(mix(uBg, uVig, f), 1.0);
            }
          `,
          uniforms: {
            uP: { value: new THREE.Vector2(0.5, 0.5) },
            uAspect: { value: window.innerWidth / window.innerHeight },
            uBg: { value: cBgLinear },
            uVig: { value: cVigLinear },
          },
          depthTest: false,
          depthWrite: false,
        });

        // Pass 2: Swirl
        const matSwirl = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D tIn;
            uniform vec2 uP;
            uniform float uAspect;
            uniform float uTime;
            void main() {
              float radius = 0.25;
              float angle = 0.1;
              vec2 d = vUv - uP;
              d.x *= uAspect;
              float r = length(d);
              float a = angle * 10.0 * smoothstep(radius, 0.0, r) + uTime / 20.0;
              float co = cos(a);
              float si = sin(a);
              vec2 rot = vec2(d.x * co - d.y * si, d.x * si + d.y * co);
              rot.x /= uAspect;
              vec2 swirled = mix(uP + rot, vUv, smoothstep(0.0, radius, r));
              vec2 uvOut = mix(vUv, swirled, 0.5);
              gl_FragColor = texture2D(tIn, clamp(uvOut, 0.0, 1.0));
            }
          `,
          uniforms: {
            tIn: { value: null },
            uP: { value: new THREE.Vector2(0.5, 0.5) },
            uAspect: { value: window.innerWidth / window.innerHeight },
            uTime: { value: 0 },
          },
          depthTest: false,
          depthWrite: false,
        });

        // Pass 3: Sine warp
        const matSine = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D tIn;
            uniform vec2 uP;
            uniform float uTime;
            void main() {
              vec2 s = vUv * 2.0 - 1.0;
              s.x += sin((s.y + uP.y) * 20.0 * 0.35 + 0.25 * uTime) * 1.18 * 0.2;
              vec2 uvOut = s * 0.5 + 0.5;
              gl_FragColor = texture2D(tIn, clamp(uvOut, 0.0, 1.0));
            }
          `,
          uniforms: {
            tIn: { value: null },
            uP: { value: new THREE.Vector2(0.5, 0.5) },
            uTime: { value: 0 },
          },
          depthTest: false,
          depthWrite: false,
        });

        // Pass 4: Shatter (Voronoi)
        const matShatter = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D tIn;
            uniform float uAspect;
            uniform float uTime;

            vec2 hash22(vec2 p) {
              vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
              p3 += dot(p3, p3.yzx + 33.33);
              return fract((p3.xx + p3.yz) * p3.zy);
            }

            void main() {
              vec2 p = (vUv - 0.5) * vec2(uAspect, 1.0) * 16.0;
              float ang = -0.78539816339;
              float co = cos(ang);
              float si = sin(ang);
              p = vec2(p.x * co - p.y * si, p.x * si + p.y * co);
              p.x *= (1.0 - 0.9 * 0.78);

              vec2 n = floor(p);
              vec2 f = fract(p);

              float f1 = 8.0;
              float f2 = 8.0;
              vec2 bestPt = vec2(0.5);

              for (int j = -1; j <= 1; j++) {
                for (int i = -1; i <= 1; i++) {
                  vec2 g = vec2(float(i), float(j));
                  vec2 h = hash22(n + g);
                  vec2 pt = 0.5 + 0.5 * sin(5.0 + 0.2 * uTime + 6.2831853 * h);
                  vec2 r = g + pt - f;
                  float d = length(r);
                  if (d < f1) {
                    f2 = f1;
                    f1 = d;
                    bestPt = pt;
                  } else if (d < f2) {
                    f2 = d;
                  }
                }
              }

              float spread = 0.9;
              vec2 offset = (bestPt * 0.4 * spread - 0.2 * spread);
              float edgeSoft = smoothstep(0.0, 0.02, f1) * smoothstep(0.0, 0.04, f2 - f1);
              vec2 uvOut = clamp(vUv + offset * edgeSoft, 0.0, 1.0);
              gl_FragColor = texture2D(tIn, uvOut);
            }
          `,
          uniforms: {
            tIn: { value: null },
            uAspect: { value: window.innerWidth / window.innerHeight },
            uTime: { value: 0 },
          },
          depthTest: false,
          depthWrite: false,
        });

        // Pass 5: Bokeh blur
        const matBokeh = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D tIn;
            uniform sampler2D tNoise;
            uniform vec2 uP;
            uniform float uAspect;
            void main() {
              float amount = 3.125 * 0.754;
              float d = distance(vUv, uP);
              float rad = amount * mix(1.0 - d, d, 0.5);
              vec2 stepSz = vec2(1.0 / uAspect, 1.0) * 0.003 * rad;

              float n = texture2D(tNoise, gl_FragCoord.xy / 128.0).r * 6.2831853;
              float r = 1.0;
              float theta = n;

              vec3 acc = vec3(0.0);
              vec3 wSum = vec3(0.0);

              for (int i = 0; i < 32; i++) {
                r += 1.0 / r;
                theta += 2.39996323;
                vec2 dir = vec2(cos(theta), sin(theta)) * (r - 1.0) * 0.12;
                vec3 c = texture2D(tIn, clamp(vUv + dir * stepSz, 0.0, 1.0)).rgb;
                vec3 w = vec3(5.0) + pow(max(c, vec3(0.0)), vec3(9.0)) * 150.0;
                acc += c * w;
                wSum += w;
              }
              gl_FragColor = vec4(acc / wSum, 1.0);
            }
          `,
          uniforms: {
            tIn: { value: null },
            tNoise: { value: noiseTex },
            uP: { value: new THREE.Vector2(0.5, 0.5) },
            uAspect: { value: window.innerWidth / window.innerHeight },
          },
          depthTest: false,
          depthWrite: false,
        });

        const passMesh = new THREE.Mesh(fsQuadGeo, matVignette);
        const passScene = new THREE.Scene();
        passScene.add(passMesh);

        function runPass(mat, target) {
          passMesh.material = mat;
          renderer.setRenderTarget(target);
          renderer.render(passScene, orthoCam);
        }

        // Composite background quad in main scene (renderOrder -10, layer 0)
        const matBgComposite = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D tStack;
            uniform vec3 uBg;
            uniform vec3 uOut;

            vec3 overlayBlend(vec3 b, vec3 s) {
              return mix(
                2.0 * b * s,
                1.0 - 2.0 * (1.0 - b) * (1.0 - s),
                step(0.5, b)
              );
            }

            vec3 linearToSRGB(vec3 c) {
              return mix(
                c * 12.92,
                1.055 * pow(max(c, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055,
                step(0.0031308, c)
              );
            }

            void main() {
              vec3 stack = texture2D(tStack, vUv).rgb;
              vec3 base = mix(uBg, overlayBlend(uBg, vec3(1.0)), 0.61);
              vec3 blend = clamp(stack + uOut * 0.35, 0.0, 1.0);
              vec3 lin = base * mix(vec3(1.0), blend, 0.95);
              gl_FragColor = vec4(linearToSRGB(lin), 1.0);
            }
          `,
          uniforms: {
            tStack: { value: bgRtA.texture },
            uBg: { value: cBgLinear },
            uOut: { value: cOutLinear },
          },
          depthTest: false,
          depthWrite: false,
        });

        const bgQuad = new THREE.Mesh(fsQuadGeo, matBgComposite);
        bgQuad.renderOrder = -10;
        bgQuad.frustumCulled = false;
        bgQuad.layers.set(0);
        scene.add(bgQuad);

        // --- 7.5 Dot Dissolve & 7.6 Dot Trail Quad (renderOrder 10, layer 0) ---
        const MAX_TRAIL = 14;
        const trailCells = Array.from({ length: MAX_TRAIL }, () => new THREE.Vector3(-9999, -9999, 0));

        const matDots = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform float uProgress;
            uniform float uDpr;
            uniform vec2 uCssSize;
            uniform vec3 uDotColor;
            uniform vec3 uTrailColor;
            uniform vec3 uTrail[14];
            uniform float uTrailActive;

            void main() {
              vec2 cssCoord = vec2(vUv.x * uCssSize.x, (1.0 - vUv.y) * uCssSize.y);
              vec2 cell = fract(cssCoord / 4.0) - 0.5;
              float dist = length(cell);
              float rad = 0.9 * uProgress;
              float aa = fwidth(dist);
              float alpha = 1.0 - smoothstep(rad - aa, rad + aa, dist);

              vec3 col = uDotColor;

              if (uTrailActive > 0.5) {
                vec2 grid16 = floor(cssCoord / 16.0);
                vec2 cell16 = fract(cssCoord / 16.0) - 0.5;
                float boxDist = max(abs(cell16.x), abs(cell16.y));
                float inSquare = 1.0 - smoothstep(0.49 - 0.03, 0.49 + 0.03, boxDist);
                float trailStrength = 0.0;
                for (int i = 0; i < 14; i++) {
                  vec3 tc = uTrail[i];
                  if (tc.z > 0.001 && abs(grid16.x - tc.x) < 0.25 && abs(grid16.y - tc.y) < 0.25) {
                    trailStrength = max(trailStrength, tc.z);
                  }
                }
                if (trailStrength > 0.001) {
                  col = mix(col, uTrailColor, trailStrength * inSquare);
                  alpha = max(alpha, trailStrength * inSquare);
                }
              }

              if (alpha < 0.002) discard;
              gl_FragColor = vec4(col, alpha);
            }
          `,
          uniforms: {
            uProgress: { value: 0 },
            uDpr: { value: renderer.getPixelRatio() },
            uCssSize: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
            uDotColor: { value: new THREE.Color('#091618') },
            uTrailColor: { value: new THREE.Color('#5fe0c4') },
            uTrail: { value: trailCells },
            uTrailActive: { value: 0 },
          },
          transparent: true,
          depthTest: false,
          depthWrite: false,
        });

        const dotQuad = new THREE.Mesh(fsQuadGeo, matDots);
        dotQuad.renderOrder = 10;
        dotQuad.frustumCulled = false;
        dotQuad.layers.set(0);
        scene.add(dotQuad);

        // --- 7.2 Glass Environment Target & Material ---
        const getEnvSize = () => {
          const dpr = renderer.getPixelRatio();
          return {
            w: Math.max(2, Math.round(window.innerWidth * dpr * 0.5)),
            h: Math.max(2, Math.round(window.innerHeight * dpr * 0.5)),
          };
        };
        let envSize = getEnvSize();
        const envRT = new THREE.WebGLRenderTarget(envSize.w, envSize.h, {
          minFilter: THREE.LinearFilter,
          magFilter: THREE.LinearFilter,
          format: THREE.RGBAFormat,
          type: rtType,
          depthBuffer: true,
        });

        const lightPos = new THREE.Vector3(4, 9, 0.5);
        const glassMaterials = [];

        function createGlassMaterial(tintHexA, tintHexB, yMin, yMax) {
          const mat = new THREE.ShaderMaterial({
            vertexShader: `
              varying vec3 vWorldNormal;
              varying vec3 vViewNormal;
              varying vec3 vWorldPos;
              varying vec3 vEye;
              varying float vLocalY;

              void main() {
                vLocalY = position.y;
                vec4 worldPos = modelMatrix * vec4(position, 1.0);
                vWorldPos = worldPos.xyz;
                vWorldNormal = normalize(mat3(modelMatrix) * normal);
                vViewNormal = normalize(normalMatrix * normal);
                vEye = normalize(worldPos.xyz - cameraPosition);
                gl_Position = projectionMatrix * viewMatrix * worldPos;
              }
            `,
            fragmentShader: `
              precision highp float;
              varying vec3 vWorldNormal;
              varying vec3 vViewNormal;
              varying vec3 vWorldPos;
              varying vec3 vEye;
              varying float vLocalY;

              uniform sampler2D tEnv;
              uniform sampler2D tNoise;
              uniform vec2 uBufferSize;
              uniform vec3 uTintA;
              uniform vec3 uTintB;
              uniform float uYMin;
              uniform float uYMax;
              uniform vec3 uLightPos;
              uniform int uSamples;

              vec3 hardLight(vec3 base, vec3 blend) {
                return mix(
                  2.0 * base * blend,
                  1.0 - 2.0 * (1.0 - base) * (1.0 - blend),
                  step(0.5, blend)
                );
              }

              void main() {
                vec2 screenUv = gl_FragCoord.xy / uBufferSize;
                vec3 n = normalize(vWorldNormal);
                vec3 vn = normalize(vViewNormal);
                vec3 e = normalize(vEye);

                vec3 refrR = refract(vec3(0.0, 0.0, -1.0), vn, 1.0 / 1.15);
                vec3 refrG = refract(vec3(0.0, 0.0, -1.0), vn, 1.0 / 1.18);
                vec3 refrB = refract(vec3(0.0, 0.0, -1.0), vn, 1.0 / 1.22);

                float noise = texture2D(tNoise, gl_FragCoord.xy / 128.0).r - 0.5;

                vec3 col = vec3(0.0);
                float fLoop = float(uSamples);
                for (int i = 0; i < 3; i++) {
                  if (i >= uSamples) break;
                  float s = (0.72 + (float(i) / fLoop) * 0.1 + noise * 0.025) * 0.14;
                  float r = texture2D(tEnv, clamp(screenUv + refrR.xy * s, 0.002, 0.998)).r;
                  float g = texture2D(tEnv, clamp(screenUv + refrG.xy * s, 0.002, 0.998)).g;
                  float b = texture2D(tEnv, clamp(screenUv + refrB.xy * s, 0.002, 0.998)).b;
                  col += vec3(r, g, b);
                }
                col /= fLoop;

                // Tone: saturation 1.2, brightness x0.6, contrast 0.98 around 0.5
                float luma = dot(col, vec3(0.2126, 0.7152, 0.0722));
                col = mix(vec3(luma), col, 1.2);
                col *= 0.6;
                col = (col - 0.5) * 0.98 + 0.5;
                col = clamp(col, 0.0, 1.0);

                // Vertical tint gradient from tintB (bottom) to tintA (top)
                float ty = clamp((vLocalY - uYMin) / max(0.0001, uYMax - uYMin), 0.0, 1.0);
                vec3 tint = mix(uTintB, uTintA, ty);
                float facing = abs(dot(n, -e));
                float tintAlpha = mix(0.4, 1.0, 1.0 - facing);
                col = mix(col, hardLight(col, tint), tintAlpha);

                // Specular (Blinn half-vector, shininess 100) + diffuse 0.05
                vec3 L = normalize(uLightPos - vWorldPos);
                vec3 V = -e;
                vec3 H = normalize(L + V);
                float spec = pow(max(0.0, dot(n, H)), 100.0);
                float diff = 0.05 * max(0.0, dot(n, L));
                col += (spec + diff) * 1.2;

                // Fresnel: (1 - |e.n|)^3 * 0.72 masked to side facing (-1, 1, -1)
                float fres = pow(clamp(1.0 - facing, 0.0, 1.0), 3.0) * 0.72;
                vec3 maskDir = normalize(vec3(-1.0, 1.0, -1.0));
                float sideMask = smoothstep(-0.5, 0.5, dot(n, maskDir));
                col += fres * sideMask;

                gl_FragColor = vec4(col, 1.0);
              }
            `,
            uniforms: {
              tEnv: { value: envRT.texture },
              tNoise: { value: noiseTex },
              uBufferSize: {
                value: new THREE.Vector2(
                  window.innerWidth * renderer.getPixelRatio(),
                  window.innerHeight * renderer.getPixelRatio()
                ),
              },
              uTintA: { value: new THREE.Color(tintHexA) },
              uTintB: { value: new THREE.Color(tintHexB) },
              uYMin: { value: yMin },
              uYMax: { value: yMax },
              uLightPos: { value: lightPos },
              uSamples: { value: isPhone() ? 2 : 3 },
            },
          });
          glassMaterials.push(mat);
          return mat;
        }

        // --- 7.3 The Five Objects ---
        const deg = THREE.MathUtils.degToRad;

        function buildTwistFreeTube(rawPoints, tubularSegments, radius, radialSegments) {
          const pts = rawPoints.map(([x, y, z]) => new THREE.Vector3(x, y, z));
          const initialCurve = new THREE.CatmullRomCurve3(pts, false, 'centripetal', 0.5);
          const sampled = initialCurve.getSpacedPoints(tubularSegments);



          const tangents = [];
          const normals = [];
          const binormals = [];

          for (let i = 0; i < sampled.length; i++) {
            const t = new THREE.Vector3();
            if (i === 0) t.subVectors(sampled[1], sampled[0]).normalize();
            else if (i === sampled.length - 1) t.subVectors(sampled[i], sampled[i - 1]).normalize();
            else t.subVectors(sampled[i + 1], sampled[i - 1]).normalize();
            tangents.push(t);
          }

          const n0 = new THREE.Vector3();
          const b0 = new THREE.Vector3();
          const ref = Math.abs(tangents[0].z) < 0.9 ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(0, 1, 0);
          b0.crossVectors(tangents[0], ref).normalize();
          n0.crossVectors(b0, tangents[0]).normalize();
          normals.push(n0);
          binormals.push(b0);

          const rotAxis = new THREE.Vector3();
          const quat = new THREE.Quaternion();
          for (let i = 1; i < sampled.length; i++) {
            const prevT = tangents[i - 1];
            const curT = tangents[i];
            const ni = normals[i - 1].clone();
            rotAxis.crossVectors(prevT, curT);
            if (rotAxis.lengthSq() > 1e-10) {
              rotAxis.normalize();
              const angle = Math.acos(THREE.MathUtils.clamp(prevT.dot(curT), -1, 1));
              quat.setFromAxisAngle(rotAxis, angle);
              ni.applyQuaternion(quat);
            }
            ni.addScaledVector(curT, -ni.dot(curT)).normalize();
            const bi = new THREE.Vector3().crossVectors(curT, ni).normalize();
            normals.push(ni);
            binormals.push(bi);
          }

          const positions = [];
          const normAttr = [];
          const uvs = [];
          const indices = [];

          for (let i = 0; i < sampled.length; i++) {
            const P = sampled[i];
            const N = normals[i];
            const B = binormals[i];
            const u = i / (sampled.length - 1);

            for (let j = 0; j <= radialSegments; j++) {
              const v = (j / radialSegments) * Math.PI * 2;
              const cosV = Math.cos(v);
              const sinV = Math.sin(v);

              const nx = cosV * N.x + sinV * B.x;
              const ny = cosV * N.y + sinV * B.y;
              const nz = cosV * N.z + sinV * B.z;

              positions.push(P.x + radius * nx, P.y + radius * ny, P.z + radius * nz);
              normAttr.push(nx, ny, nz);
              uvs.push(u, j / radialSegments);
            }
          }

          const stride = radialSegments + 1;
          for (let i = 0; i < sampled.length - 1; i++) {
            for (let j = 0; j < radialSegments; j++) {
              const a = i * stride + j;
              const b = (i + 1) * stride + j;
              const c = (i + 1) * stride + (j + 1);
              const d = i * stride + (j + 1);
              indices.push(a, b, d);
              indices.push(b, c, d);
            }
          }

          const tubeGeo = new THREE.BufferGeometry();
          tubeGeo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
          tubeGeo.setAttribute('normal', new THREE.Float32BufferAttribute(normAttr, 3));
          tubeGeo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
          tubeGeo.setIndex(indices);

          const startCap = new THREE.SphereGeometry(radius, radialSegments, 14);
          startCap.translate(sampled[0].x, sampled[0].y, sampled[0].z);

          const last = sampled[sampled.length - 1];
          const endCap = new THREE.SphereGeometry(radius, radialSegments, 14);
          endCap.translate(last.x, last.y, last.z);

          return mergeGeometries([tubeGeo, startCap, endCap], false);
        }

        // 1. "Review Pilot" calligraphic 3D geometry
        function buildHelloGeometry() {
          const RADIAL_SEGS = 28;
          const parts = [];

          for (const stroke of REVIEW_PILOT_STROKES) {
            parts.push(buildTwistFreeTube(stroke.pts, stroke.segs, stroke.radius, RADIAL_SEGS));
          }

          for (const [x, y, z, r] of REVIEW_PILOT_DOTS) {
            const dotGeo = new THREE.SphereGeometry(r, 28, 20);
            dotGeo.translate(x, y, z);
            parts.push(dotGeo);
          }

          const merged = mergeGeometries(parts, false);
          merged.scale(1, 0.86, 1);
          merged.computeVertexNormals();
          merged.center();
          merged.computeBoundingBox();

          const size = new THREE.Vector3();
          merged.boundingBox.getSize(size);
          const normScale = 15.3 / size.x;
          merged.scale(normScale, normScale, normScale);
          merged.computeBoundingBox();
          return merged;
        }

        // 2. Sparkle (four-point concave star)
        function buildSparkleGeometry() {
          const shape = new THREE.Shape();
          const c = 0.16;
          shape.moveTo(0, 1);
          shape.quadraticCurveTo(c, c, 1, 0);
          shape.quadraticCurveTo(c, -c, 0, -1);
          shape.quadraticCurveTo(-c, -c, -1, 0);
          shape.quadraticCurveTo(-c, c, 0, 1);

          const geo = new THREE.ExtrudeGeometry(shape, {
            depth: 0.12,
            bevelEnabled: true,
            bevelThickness: 0.16,
            bevelSize: 0.1,
            bevelSegments: 8,
            curveSegments: 24,
          });
          geo.center();
          geo.computeVertexNormals();
          geo.computeBoundingBox();
          return geo;
        }

        // 3. Pill (capsule rotated 110 deg about Z)
        function buildPillGeometry() {
          const geo = new THREE.CapsuleGeometry(0.5, 1.3, 20, 32);
          geo.rotateZ(deg(110));
          geo.center();
          geo.computeVertexNormals();
          geo.computeBoundingBox();
          return geo;
        }

        // 4. Pearl (sphere radius 0.76)
        function buildPearlGeometry() {
          const geo = new THREE.SphereGeometry(0.76, 48, 32);
          geo.computeBoundingBox();
          return geo;
        }

        // 5. Cursor arrow
        function buildCursorGeometry() {
          const shape = new THREE.Shape();
          shape.moveTo(0, 0);
          shape.lineTo(0, -3.1);
          shape.lineTo(0.82, -2.38);
          shape.lineTo(1.42, -3.62);
          shape.lineTo(1.98, -3.36);
          shape.lineTo(1.4, -2.16);
          shape.lineTo(2.42, -2.16);
          shape.closePath();

          const geo = new THREE.ExtrudeGeometry(shape, {
            depth: 0.35,
            bevelEnabled: true,
            bevelThickness: 0.28,
            bevelSize: 0.24,
            bevelSegments: 10,
          });
          geo.center();
          geo.computeVertexNormals();
          geo.computeBoundingBox();
          return geo;
        }

        const objects = [];

        function addGlassObject(cfg) {
          const geo = cfg.geo;
          const bb = geo.boundingBox;
          const mat = createGlassMaterial(cfg.tint[0], cfg.tint[1], bb.min.y, bb.max.y);
          const mesh = new THREE.Mesh(geo, mat);
          mesh.layers.set(10);

          let root = mesh;
          if (cfg.axisTiltZ) {
            const pivot = new THREE.Group();
            pivot.rotation.z = cfg.axisTiltZ;
            pivot.add(mesh);
            root = pivot;
          }

          mesh.rotation.set(
            reducedMotion ? cfg.restRot[0] : cfg.beforeRot[0],
            reducedMotion ? cfg.restRot[1] : cfg.beforeRot[1],
            reducedMotion ? cfg.restRot[2] : cfg.beforeRot[2]
          );

          root.visible = false;
          scene.add(root);

          objects.push({
            root,
            mesh,
            cfg,
            curRot: [
              mesh.rotation.x,
              mesh.rotation.y,
              mesh.rotation.z,
            ],
          });
        }

        addGlassObject({
          name: 'hello',
          geo: buildHelloGeometry(),
          tint: ['#effffb', '#9fe8d8'],
          deskPos: [-0.1, 0.7, 2],
          mobPos: [0, 0.4, 2],
          deskScale: 1,
          mobScale: 19 / 22,
          beforeRot: [0, deg(240), 0],
          restRot: [0, deg(4), 0],
          afterRot: [0, deg(90), 0],
        });

        addGlassObject({
          name: 'sparkle',
          geo: buildSparkleGeometry(),
          tint: ['#ffffff', '#d4e2e0'],
          deskPos: [-6.9, 3.9, 1],
          mobPos: [-4.6, 3.9, 1],
          deskScale: 0.82,
          mobScale: 0.62,
          beforeRot: [0, deg(-140), deg(8)],
          restRot: [0, deg(-14), deg(8)],
          afterRot: [0, deg(360), 0],
        });

        addGlassObject({
          name: 'pill',
          geo: buildPillGeometry(),
          tint: ['#c8f6ea', '#38c4a4'],
          deskPos: [6.3, 3.35, 0],
          mobPos: [4.7, 3.7, 0],
          deskScale: 1.0,
          mobScale: 0.75,
          beforeRot: [0, 0, deg(-90)],
          restRot: [0, 0, 0],
          afterRot: [0, 0, deg(180)],
        });

        addGlassObject({
          name: 'pearl',
          geo: buildPearlGeometry(),
          tint: ['#f6fffd', '#d4f6ee'],
          deskPos: [9.7, -0.1, 0.5],
          mobPos: [5.2, -2.8, 0.5],
          deskScale: 1.0,
          mobScale: 0.75,
          beforeRot: [0, 0, 0],
          restRot: [0, 0, 0],
          afterRot: [0, 0, 0],
        });

        addGlassObject({
          name: 'cursor',
          geo: buildCursorGeometry(),
          tint: ['#e4fbf5', '#6fd8c0'],
          deskPos: [8.9, -2.95, -1],
          mobPos: [3.6, -5.2, -1],
          deskScale: 0.58,
          mobScale: 0.46,
          axisTiltZ: deg(45),
          beforeRot: [0, deg(-180), deg(8)],
          restRot: [0, deg(10), deg(8)],
          afterRot: [0, deg(720), 0],
        });

        // --- 7.6 Pointer Fluid Simulation & Post-Process ---
        const getFullBufSize = () => {
          const dpr = renderer.getPixelRatio();
          return {
            w: Math.max(2, Math.round(window.innerWidth * dpr)),
            h: Math.max(2, Math.round(window.innerHeight * dpr)),
          };
        };
        let fullBuf = getFullBufSize();
        const sceneRT = new THREE.WebGLRenderTarget(fullBuf.w, fullBuf.h, {
          minFilter: THREE.LinearFilter,
          magFilter: THREE.LinearFilter,
          format: THREE.RGBAFormat,
          type: rtType,
          depthBuffer: true,
        });

        function getFluidGridSize() {
          const w = window.innerWidth;
          const h = window.innerHeight;
          const aspect = w / Math.max(1, h);
          if (w < h) {
            return { w: 160, h: Math.round(160 / aspect) };
          }
          return { w: Math.round(160 * aspect), h: 160 };
        }
        let fluidGrid = getFluidGridSize();
        const fluidRtOpts = {
          minFilter: THREE.LinearFilter,
          magFilter: THREE.LinearFilter,
          format: THREE.RGBAFormat,
          type: rtType,
          depthBuffer: false,
          stencilBuffer: false,
        };
        let velA = new THREE.WebGLRenderTarget(fluidGrid.w, fluidGrid.h, fluidRtOpts);
        let velB = new THREE.WebGLRenderTarget(fluidGrid.w, fluidGrid.h, fluidRtOpts);
        let divRT = new THREE.WebGLRenderTarget(fluidGrid.w, fluidGrid.h, fluidRtOpts);
        let curlRT = new THREE.WebGLRenderTarget(fluidGrid.w, fluidGrid.h, fluidRtOpts);
        let pressA = new THREE.WebGLRenderTarget(fluidGrid.w, fluidGrid.h, fluidRtOpts);
        let pressB = new THREE.WebGLRenderTarget(fluidGrid.w, fluidGrid.h, fluidRtOpts);

        const texelStep = new THREE.Vector2(1 / fluidGrid.w, 1 / fluidGrid.h);

        // 1. Curl
        const matCurl = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D uVelocity;
            uniform vec2 uTexel;
            void main() {
              float L = texture2D(uVelocity, vUv - vec2(uTexel.x, 0.0)).y;
              float R = texture2D(uVelocity, vUv + vec2(uTexel.x, 0.0)).y;
              float T = texture2D(uVelocity, vUv + vec2(0.0, uTexel.y)).x;
              float B = texture2D(uVelocity, vUv - vec2(0.0, uTexel.y)).x;
              float vort = R - L - T + B;
              gl_FragColor = vec4(0.5 * vort, 0.0, 0.0, 1.0);
            }
          `,
          uniforms: {
            uVelocity: { value: null },
            uTexel: { value: texelStep },
          },
          depthTest: false,
          depthWrite: false,
        });

        // 2. Splat
        const matSplat = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D uVelocity;
            uniform vec2 uPoint;
            uniform vec2 uDelta;
            uniform float uAspect;
            void main() {
              vec2 v = texture2D(uVelocity, vUv).xy;
              vec2 d = vUv - uPoint;
              d.x *= uAspect;
              vec2 splat = uDelta * exp(-dot(d, d) / 0.003) * 3000.0;
              v = clamp(v + splat, vec2(-1000.0), vec2(1000.0));
              gl_FragColor = vec4(v, 0.0, 1.0);
            }
          `,
          uniforms: {
            uVelocity: { value: null },
            uPoint: { value: new THREE.Vector2(0.5, 0.5) },
            uDelta: { value: new THREE.Vector2(0, 0) },
            uAspect: { value: window.innerWidth / window.innerHeight },
          },
          depthTest: false,
          depthWrite: false,
        });

        // 3. Divergence
        const matDiv = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D uVelocity;
            uniform vec2 uTexel;
            void main() {
              float L = texture2D(uVelocity, vUv - vec2(uTexel.x, 0.0)).x;
              float R = texture2D(uVelocity, vUv + vec2(uTexel.x, 0.0)).x;
              float T = texture2D(uVelocity, vUv + vec2(0.0, uTexel.y)).y;
              float B = texture2D(uVelocity, vUv - vec2(0.0, uTexel.y)).y;
              float div = 0.5 * (R - L + T - B);
              gl_FragColor = vec4(div, 0.0, 0.0, 1.0);
            }
          `,
          uniforms: {
            uVelocity: { value: null },
            uTexel: { value: texelStep },
          },
          depthTest: false,
          depthWrite: false,
        });

        // 4. Pressure Jacobi
        const matPressure = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D uPressure;
            uniform sampler2D uDivergence;
            uniform vec2 uTexel;
            void main() {
              float L = texture2D(uPressure, vUv - vec2(uTexel.x, 0.0)).x;
              float R = texture2D(uPressure, vUv + vec2(uTexel.x, 0.0)).x;
              float T = texture2D(uPressure, vUv + vec2(0.0, uTexel.y)).x;
              float B = texture2D(uPressure, vUv - vec2(0.0, uTexel.y)).x;
              float div = texture2D(uDivergence, vUv).x;
              float p = (L + R + B + T - div) * 0.25;
              gl_FragColor = vec4(p, 0.0, 0.0, 1.0);
            }
          `,
          uniforms: {
            uPressure: { value: null },
            uDivergence: { value: null },
            uTexel: { value: texelStep },
          },
          depthTest: false,
          depthWrite: false,
        });

        // 5. Subtract Pressure Gradient
        const matGradSub = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D uPressure;
            uniform sampler2D uVelocity;
            uniform vec2 uTexel;
            void main() {
              float L = texture2D(uPressure, vUv - vec2(uTexel.x, 0.0)).x;
              float R = texture2D(uPressure, vUv + vec2(uTexel.x, 0.0)).x;
              float T = texture2D(uPressure, vUv + vec2(0.0, uTexel.y)).x;
              float B = texture2D(uPressure, vUv - vec2(0.0, uTexel.y)).x;
              vec2 v = texture2D(uVelocity, vUv).xy;
              v -= 0.5 * vec2(R - L, T - B);
              gl_FragColor = vec4(v, 0.0, 1.0);
            }
          `,
          uniforms: {
            uPressure: { value: null },
            uVelocity: { value: null },
            uTexel: { value: texelStep },
          },
          depthTest: false,
          depthWrite: false,
        });

        // 6. Self-Advection
        const matAdvect = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D uVelocity;
            uniform vec2 uTexel;
            void main() {
              float dt = 0.016;
              float dissipation = 3.0;
              vec2 coord = vUv - dt * texture2D(uVelocity, vUv).xy * uTexel;
              vec2 result = texture2D(uVelocity, clamp(coord, 0.0, 1.0)).xy;
              float decay = 1.0 + dissipation * dt;
              gl_FragColor = vec4(result / decay, 0.0, 1.0);
            }
          `,
          uniforms: {
            uVelocity: { value: null },
            uTexel: { value: texelStep },
          },
          depthTest: false,
          depthWrite: false,
        });

        // Display pass
        const matFluidDisplay = new THREE.ShaderMaterial({
          vertexShader: passVert,
          fragmentShader: `
            precision highp float;
            varying vec2 vUv;
            uniform sampler2D tScene;
            uniform sampler2D uVelocity;
            uniform vec2 uGridSize;
            uniform float uFluidActive;

            vec3 ramp(float t) {
              vec3 c0 = vec3(0.62, 1.0, 0.9);
              vec3 c1 = vec3(0.25, 0.95, 0.62);
              vec3 c2 = vec3(0.04, 0.62, 0.55);
              return t < 0.5 ? mix(c0, c1, t * 2.0) : mix(c1, c2, (t - 0.5) * 2.0);
            }

            void main() {
              if (uFluidActive < 0.5) {
                gl_FragColor = texture2D(tScene, vUv);
                return;
              }
              vec2 vel = texture2D(uVelocity, vUv).xy;
              vec2 disp = vel / uGridSize;
              float m = length(disp);

              vec3 acc = vec3(0.0);
              vec3 wSum = vec3(0.0);

              for (int i = 0; i < 4; i++) {
                float k = float(i) / 3.0;
                vec2 uvTap = clamp(vUv - disp * 0.3 * (k + 0.3) * m, 0.001, 0.999);
                vec3 sampleCol = texture2D(tScene, uvTap).rgb;
                vec3 w = vec3(
                  0.55 + 0.45 * (1.0 - abs(2.0 * k - 1.0)),
                  1.0 - 0.2 * k,
                  0.75 + 0.25 * k
                );
                acc += sampleCol * w;
                wSum += w;
              }

              vec3 col = acc / wSum;
              float t = sin(2.0 * m) * 0.5 + 0.5;
              vec3 hi = ramp(t) * smoothstep(0.2, 0.8, m) * 0.25;
              col += hi;
              gl_FragColor = vec4(col, 1.0);
            }
          `,
          uniforms: {
            tScene: { value: sceneRT.texture },
            uVelocity: { value: velA.texture },
            uGridSize: { value: new THREE.Vector2(fluidGrid.w, fluidGrid.h) },
            uFluidActive: { value: 0 },
          },
          depthTest: false,
          depthWrite: false,
        });

        function stepFluidSim() {
          const dpr = renderer.getPixelRatio();
          const bufW = window.innerWidth * dpr;
          const bufH = window.innerHeight * dpr;

          // 1. Curl
          matCurl.uniforms.uVelocity.value = velA.texture;
          runPass(matCurl, curlRT);

          // 2. Splat
          matSplat.uniforms.uVelocity.value = velA.texture;
          matSplat.uniforms.uPoint.value.set(pointer.bufPos.x / bufW, pointer.bufPos.y / bufH);
          matSplat.uniforms.uDelta.value.set(pointer.delta.x / bufW, pointer.delta.y / bufH);
          matSplat.uniforms.uAspect.value = bufW / Math.max(1, bufH);
          runPass(matSplat, velB);
          [velA, velB] = [velB, velA];

          // 3. Divergence
          matDiv.uniforms.uVelocity.value = velA.texture;
          runPass(matDiv, divRT);

          // 4. Pressure: clear then 4 Jacobi iterations
          renderer.setRenderTarget(pressA);
          renderer.setClearColor(0x000000, 0);
          renderer.clear();
          renderer.setClearColor(0x091618, 1);

          for (let i = 0; i < 4; i++) {
            matPressure.uniforms.uPressure.value = pressA.texture;
            matPressure.uniforms.uDivergence.value = divRT.texture;
            runPass(matPressure, pressB);
            [pressA, pressB] = [pressB, pressA];
          }

          // 5. Subtract pressure gradient
          matGradSub.uniforms.uPressure.value = pressA.texture;
          matGradSub.uniforms.uVelocity.value = velA.texture;
          runPass(matGradSub, velB);
          [velA, velB] = [velB, velA];

          // 6. Self-advect
          matAdvect.uniforms.uVelocity.value = velA.texture;
          runPass(matAdvect, velB);
          [velA, velB] = [velB, velA];
        }

        // Resize handling
        window.addEventListener('resize', () => {
          const dpr = getDpr();
          renderer.setPixelRatio(dpr);
          renderer.setSize(window.innerWidth, window.innerHeight);
          updateCameraFov();

          const aspect = window.innerWidth / Math.max(1, window.innerHeight);
          matVignette.uniforms.uAspect.value = aspect;
          matSwirl.uniforms.uAspect.value = aspect;
          matShatter.uniforms.uAspect.value = aspect;
          matBokeh.uniforms.uAspect.value = aspect;

          bgSize = getBgSize();
          bgRtA.setSize(bgSize.w, bgSize.h);
          bgRtB.setSize(bgSize.w, bgSize.h);

          envSize = getEnvSize();
          envRT.setSize(envSize.w, envSize.h);

          fullBuf = getFullBufSize();
          sceneRT.setSize(fullBuf.w, fullBuf.h);

          fluidGrid = getFluidGridSize();
          velA.setSize(fluidGrid.w, fluidGrid.h);
          velB.setSize(fluidGrid.w, fluidGrid.h);
          divRT.setSize(fluidGrid.w, fluidGrid.h);
          curlRT.setSize(fluidGrid.w, fluidGrid.h);
          pressA.setSize(fluidGrid.w, fluidGrid.h);
          pressB.setSize(fluidGrid.w, fluidGrid.h);
          texelStep.set(1 / fluidGrid.w, 1 / fluidGrid.h);
          matFluidDisplay.uniforms.uGridSize.value.set(fluidGrid.w, fluidGrid.h);

          matDots.uniforms.uDpr.value = dpr;
          matDots.uniforms.uCssSize.value.set(window.innerWidth, window.innerHeight);

          const phone = isPhone();
          glassMaterials.forEach((m) => {
            m.uniforms.uBufferSize.value.set(fullBuf.w, fullBuf.h);
            m.uniforms.uSamples.value = phone ? 2 : 3;
          });
        });

        // --- 7.4 Scene Motion, Light Orbit, Intro Dolly & Loop ---
        const bgCenterP = new THREE.Vector2(0.5, 0.5);
        const camOffset = new THREE.Vector2(0, 0);
        const lookAtOffset = new THREE.Vector2(0, 0);
        const raycaster = new THREE.Raycaster();
        const zZeroPlane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
        const planeHit = new THREE.Vector3();

        const lightRadius = Math.hypot(4, 9);
        const restLightAngle = Math.atan2(9, 4);
        let currentLightAngle = restLightAngle;

        let dotsSolid = false;
        let lastTrailCellX = -9999;
        let lastTrailCellY = -9999;

        let frameCount = 0;
        const startTime = performance.now();
        let prevTime = startTime;

        function dampAngle(curr, target, lambda, dt) {
          let diff = ((target - curr + Math.PI) % (Math.PI * 2)) - Math.PI;
          if (diff < -Math.PI) diff += Math.PI * 2;
          return curr + diff * (1 - Math.exp(-lambda * dt));
        }

        function afterDraw(cb) {
          const gl = renderer.getContext();
          if (gl && gl.fenceSync) {
            const sync = gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0);
            gl.flush();
            const poll = () => {
              const state = sync && gl.getSyncParameter(sync, gl.SYNC_STATUS);
              if (state === gl.UNSIGNALED) {
                setTimeout(poll, 5);
              } else {
                if (sync) gl.deleteSync(sync);
                setTimeout(cb, 80);
              }
            };
            setTimeout(poll, 5);
          } else {
            setTimeout(cb, 80);
          }
        }

        function tick(now) {
          if (lenis) lenis.raf(now);

          const dt = Math.min(0.1, Math.max(0.001, (now - prevTime) / 1000));
          prevTime = now;
          const t = (now - startTime) / 1000;
          const phone = isPhone();
          const vh = Math.max(1, window.innerHeight);

          const heroRect = heroEl ? heroEl.getBoundingClientRect() : { top: 0, bottom: vh, height: vh };
          const p = THREE.MathUtils.clamp((vh - heroRect.bottom) / (vh - 0.25 * vh), 0, 1);
          const heroVisible = heroRect.bottom > 0 && heroRect.top < vh;

          // Hysteresis for solid dots
          if (!dotsSolid && p >= 0.9) dotsSolid = true;
          else if (dotsSolid && p <= 0.82) dotsSolid = false;

          // Fluid active check
          const fluidActive =
            !phone &&
            !reducedMotion &&
            !dotsSolid &&
            now - pointer.lastMoveTime < 600;

          if (!pointer.inside || now - pointer.lastMoveTime > 32) {
            pointer.delta.multiplyScalar(0.9);
          }

          // Dot trail update (about section on desktop)
          let hasActiveTrail = false;
          if (!phone && !reducedMotion && dotsSolid) {
            if (pointer.inside) {
              const dpr = renderer.getPixelRatio();
              const cssX = pointer.bufPos.x / dpr;
              const cssY = window.innerHeight - pointer.bufPos.y / dpr;
              const gx = Math.floor(cssX / 16);
              const gy = Math.floor(cssY / 16);
              if (gx !== lastTrailCellX || gy !== lastTrailCellY) {
                lastTrailCellX = gx;
                lastTrailCellY = gy;
                for (let i = MAX_TRAIL - 1; i > 0; i--) {
                  trailCells[i].copy(trailCells[i - 1]);
                }
                trailCells[0].set(gx, gy, 1.0);
              } else {
                trailCells[0].z = 1.0;
              }
            }
            const decay = Math.exp(-2.0 * dt);
            for (let i = pointer.inside ? 1 : 0; i < MAX_TRAIL; i++) {
              trailCells[i].z *= decay;
              if (trailCells[i].z < 0.01) trailCells[i].z = 0;
            }
            for (let i = 0; i < MAX_TRAIL; i++) {
              if (trailCells[i].z > 0.01) {
                hasActiveTrail = true;
                break;
              }
            }
          } else {
            for (let i = 0; i < MAX_TRAIL; i++) trailCells[i].z = 0;
          }

          // Idle skip check (§7.6)
          if (
            frameCount > 10 &&
            p >= 1 &&
            !heroVisible &&
            !fluidActive &&
            !hasActiveTrail &&
            now - pointer.lastMoveTime > 600
          ) {
            if (isSoftwareGl) afterDraw(() => requestAnimationFrame(tick));
            else requestAnimationFrame(tick);
            return;
          }

          // Background pointer centre P
          if (phone) {
            bgCenterP.set(0.5, -0.1);
          } else if (pointer.inside) {
            bgCenterP.lerp(pointer.uv, 0.1);
          } else {
            bgCenterP.x += (0.5 - bgCenterP.x) * 0.05;
            bgCenterP.y += (0.5 - bgCenterP.y) * 0.05;
          }

          // Background stack cadence: while p < 0.98, every 2nd frame (every 4th once p > 0.75)
          const bgMod = p > 0.75 ? 4 : 2;
          if (frameCount === 0 || (p < 0.98 && frameCount % bgMod === 0)) {
            matVignette.uniforms.uP.value.copy(bgCenterP);
            runPass(matVignette, bgRtA);

            matSwirl.uniforms.tIn.value = bgRtA.texture;
            matSwirl.uniforms.uP.value.copy(bgCenterP);
            matSwirl.uniforms.uTime.value = t;
            runPass(matSwirl, bgRtB);

            matSine.uniforms.tIn.value = bgRtB.texture;
            matSine.uniforms.uP.value.copy(bgCenterP);
            matSine.uniforms.uTime.value = t;
            runPass(matSine, bgRtA);

            matShatter.uniforms.tIn.value = bgRtA.texture;
            matShatter.uniforms.uTime.value = t;
            runPass(matShatter, bgRtB);

            matBokeh.uniforms.tIn.value = bgRtB.texture;
            matBokeh.uniforms.uP.value.copy(bgCenterP);
            runPass(matBokeh, bgRtA);
          }

          // Camera dolly & parallax (§7.4)
          const baseZ = THREE.MathUtils.lerp(24, 32, p);
          let camZ = baseZ;
          if (!reducedMotion) {
            const introProgress = Math.min(1, t / 1.2);
            const easedIntro = cubicBezier(0.66, 0, 0.01, 1, introProgress);
            camZ = THREE.MathUtils.lerp(baseZ + 8, baseZ, easedIntro);
          }

          if (!phone && !reducedMotion) {
            if (pointer.inside) {
              const tx = (0.5 - pointer.uv.x) * 2 * 1.4;
              const ty = (0.5 - pointer.uv.y) * 2 * 1.4 * 0.6;
              camOffset.x += (tx - camOffset.x) * 0.18;
              camOffset.y += (ty - camOffset.y) * 0.18;
              lookAtOffset.x += (-0.12 * tx - lookAtOffset.x) * 0.18;
              lookAtOffset.y += (-0.12 * ty - lookAtOffset.y) * 0.18;
            } else {
              camOffset.x += (0 - camOffset.x) * 0.05;
              camOffset.y += (0 - camOffset.y) * 0.05;
              lookAtOffset.x += (0 - lookAtOffset.x) * 0.05;
              lookAtOffset.y += (0 - lookAtOffset.y) * 0.05;
            }
          } else {
            camOffset.x += (0 - camOffset.x) * 0.05;
            camOffset.y += (0 - camOffset.y) * 0.05;
            lookAtOffset.x += (0 - lookAtOffset.x) * 0.05;
            lookAtOffset.y += (0 - lookAtOffset.y) * 0.05;
          }

          camera.position.set(camOffset.x, camOffset.y, camZ);
          camera.lookAt(lookAtOffset.x, lookAtOffset.y, 0);
          camera.updateMatrixWorld();

          // Light orbit (§7.2)
          let targetLightAngle = restLightAngle;
          if (!phone && pointer.inside) {
            const ndc = new THREE.Vector2(pointer.uv.x * 2 - 1, pointer.uv.y * 2 - 1);
            raycaster.setFromCamera(ndc, camera);
            if (raycaster.ray.intersectPlane(zZeroPlane, planeHit)) {
              targetLightAngle = Math.atan2(-planeHit.y, -planeHit.x);
            }
          }
          currentLightAngle = reducedMotion
            ? targetLightAngle
            : dampAngle(currentLightAngle, targetLightAngle, 6, dt);
          lightPos.set(
            Math.cos(currentLightAngle) * lightRadius,
            Math.sin(currentLightAngle) * lightRadius,
            0.5
          );

          // Update objects (§7.4: exact before -> rest -> after rotation sequence with lambda = 6/s)
          const scrollY = window.scrollY || window.pageYOffset || 0;
          const heroTopDoc = heroRect.top + scrollY;
          const heroCentreDocY = heroTopDoc + heroRect.height * 0.5;
          const rawEntry = (scrollY + vh - heroTopDoc) / vh;
          const entry = THREE.MathUtils.clamp(rawEntry, 0, 1);
          const after = THREE.MathUtils.clamp(rawEntry - 1, 0, 1);
          const floatOffset =
            !phone && !reducedMotion
              ? 0.18 * Math.sin(1.2 * t) + 0.06 * Math.sin(0.6 * t)
              : 0;
          const vFovRad = (camera.fov * Math.PI) / 180;

          objects.forEach((obj) => {
            obj.root.visible = heroVisible && frameCount >= 5;
            if (!obj.root.visible) return;

            const basePos = phone ? obj.cfg.mobPos : obj.cfg.deskPos;
            const sc = phone ? obj.cfg.mobScale : obj.cfg.deskScale;
            obj.root.scale.setScalar(sc);

            const distDepth = Math.max(0.1, camZ - basePos[2]);
            const Hz = 2 * distDepth * Math.tan(vFovRad * 0.5);
            const scrollRise =
              (0.5 - heroCentreDocY / vh) * Hz + (scrollY / vh) * Hz * 0.72;

            obj.root.position.set(
              basePos[0],
              basePos[1] + scrollRise + floatOffset,
              basePos[2]
            );

            for (let axis = 0; axis < 3; axis++) {
              const rEntry = THREE.MathUtils.lerp(
                obj.cfg.beforeRot[axis],
                obj.cfg.restRot[axis],
                entry
              );
              const rTarget = THREE.MathUtils.lerp(
                rEntry,
                obj.cfg.afterRot[axis],
                after
              );
              if (reducedMotion) {
                obj.curRot[axis] = rTarget;
              } else {
                obj.curRot[axis] = THREE.MathUtils.damp(
                  obj.curRot[axis],
                  rTarget,
                  6,
                  dt
                );
              }
            }
            obj.mesh.rotation.set(obj.curRot[0], obj.curRot[1], obj.curRot[2]);
          });

          // Update dot dissolve uniforms
          matDots.uniforms.uProgress.value = p;
          matDots.uniforms.uTrailActive.value = hasActiveTrail ? 1.0 : 0.0;

          // Glass environment capture cadence (§7.2)
          const envMod = phone ? 3 : p > 0.75 ? 4 : p > 0.5 ? 2 : 1;
          if (heroVisible && p < 0.99 && (frameCount === 0 || frameCount % envMod === 0)) {
            camera.layers.disable(10);
            renderer.setRenderTarget(envRT);
            renderer.clear();
            renderer.render(scene, camera);
            camera.layers.enable(10);
          }

          // Pointer fluid & final render
          if (fluidActive) {
            stepFluidSim();
            renderer.setRenderTarget(sceneRT);
            renderer.clear();
            renderer.render(scene, camera);

            matFluidDisplay.uniforms.tScene.value = sceneRT.texture;
            matFluidDisplay.uniforms.uVelocity.value = velA.texture;
            matFluidDisplay.uniforms.uFluidActive.value = 1.0;
            runPass(matFluidDisplay, null);
          } else {
            renderer.setRenderTarget(null);
            renderer.clear();
            renderer.render(scene, camera);
          }

          frameCount++;
          if (frameCount === 5) {
            canvas.classList.add('on');
            objects.forEach((obj) => {
              obj.root.visible = heroVisible;
            });
          }

          if (isSoftwareGl) {
            afterDraw(() => requestAnimationFrame(tick));
          } else {
            requestAnimationFrame(tick);
          }
        }

        requestAnimationFrame(tick);
      }
    