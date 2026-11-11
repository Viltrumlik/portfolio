'use strict';

document.addEventListener('DOMContentLoaded', function () {

    // ─── Element References ────────────────────────────────────────────────────
    const header = document.querySelector('header');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');
    const hamburger = document.querySelector('.hamburger');
    const heroSubitle = document.getElementById('rotating-profession');
    const contactForm = document.getElementById('contactForm');

    // ─── Navbar Scroll Effect ──────────────────────────────────────────────────
    function onScroll() {
        if (window.scrollY > 50) {
            header?.classList.add('scrolled');
        } else {
            header?.classList.remove('scrolled');
        }
    }

    let scrollTicking = false;
    window.addEventListener('scroll', () => {
        if (!scrollTicking) {
            requestAnimationFrame(() => { onScroll(); scrollTicking = false; });
            scrollTicking = true;
        }
    });

    onScroll(); // run once on load

    // ─── Mobile Menu ───────────────────────────────────────────────────────────
    function toggleMenu() {
        hamburger?.classList.toggle('active');
        navMenu?.classList.toggle('active');
        document.body.style.overflow = navMenu?.classList.contains('active') ? 'hidden' : '';
    }

    hamburger?.addEventListener('click', toggleMenu);

    // Close menu when a link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (navMenu?.classList.contains('active')) toggleMenu();
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', e => {
        if (
            navMenu?.classList.contains('active') &&
            !navMenu.contains(e.target) &&
            !hamburger?.contains(e.target)
        ) toggleMenu();
    });

    // ─── Smooth scroll for same-page hash links ────────────────────────────────
    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href && href.includes('#') && href.split('#')[0] === window.location.pathname.replace(/\/$/, '')) {
                const id = '#' + href.split('#')[1];
                const target = document.querySelector(id);
                if (target) {
                    e.preventDefault();
                    const offset = (header?.offsetHeight || 80) + 20;
                    window.scrollTo({ top: target.offsetTop - offset, behavior: 'smooth' });
                }
            }
        });
    });

    // ─── Active nav from scroll (home page sections) ───────────────────────────
    const sections = document.querySelectorAll('section[id]');
    function updateActiveNav() {
        const scrollY = window.scrollY + (header?.offsetHeight || 80) + 20;
        sections.forEach(section => {
            const top = section.offsetTop;
            const bottom = top + section.offsetHeight;
            const id = '#' + section.getAttribute('id');
            const link = document.querySelector(`.nav-link[href="${id}"]`);
            if (link) {
                link.classList.toggle('active', scrollY >= top && scrollY < bottom);
            }
        });
    }

    if (sections.length) {
        window.addEventListener('scroll', updateActiveNav, { passive: true });
        updateActiveNav();
    }

    // ─── Keyboard navigation ───────────────────────────────────────────────────
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && navMenu?.classList.contains('active')) toggleMenu();
    });

    // ─── Typewriter Effect ─────────────────────────────────────────────────────
    if (heroSubitle) {
        const professions = [
            'Backend Developer',
            'Software Engineer',
            'Python & Django Developer',
            'Problem Solver'
        ];
        let pi = 0, ci = 0, deleting = false;

        function type() {
            const word = professions[pi];
            if (deleting) {
                heroSubitle.innerHTML = "I'm a " + word.substring(0, ci - 1) + '<span class="cursor">|</span>';
                ci--;
            } else {
                heroSubitle.innerHTML = "I'm a " + word.substring(0, ci + 1) + '<span class="cursor">|</span>';
                ci++;
            }

            let delay = deleting ? 75 : 150;
            if (!deleting && ci === word.length) { delay = 2000; deleting = true; }
            if (deleting && ci === 0) { deleting = false; pi = (pi + 1) % professions.length; delay = 500; }

            setTimeout(type, delay);
        }
        type();
    }

    // ─── Scroll Reveal (IntersectionObserver) ─────────────────────────────────
    // Elements that should NOT get the JS reveal (they use CSS-only animations)
    const revealSkipSelectors = ['article-header-premium'];

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            el.classList.add('active');

            // Stagger child items if present
            el.querySelectorAll('.stagger-item').forEach((child, i) => {
                child.style.transitionDelay = `${(i + 1) * 0.1}s`;
                child.style.opacity = '1';
                child.style.transform = 'translateY(0)';
            });

            revealObserver.unobserve(el); // fire once
        });
    }, {
        threshold: 0.05,
        rootMargin: '0px'
    });

    document.querySelectorAll('.reveal, .animate-on-scroll').forEach(el => {
        // Skip elements that use CSS-only animations
        if (revealSkipSelectors.some(cls => el.classList.contains(cls))) return;

        // Set up stagger children for grids
        if (
            el.classList.contains('projects-grid') ||
            el.classList.contains('services-grid') ||
            el.classList.contains('skills-grid') ||
            el.classList.contains('experience-timeline')
        ) {
            el.querySelectorAll('.project-card, .service-card, .skill-card, .skill-category, .experience-item')
                .forEach(child => {
                    child.classList.add('stagger-item');
                    child.style.opacity = '0';
                    child.style.transform = 'translateY(20px)';
                    child.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
                });
        }

        el.classList.add('reveal'); // ensure the class is there for CSS
        revealObserver.observe(el);
    });

    // Immediately activate elements already in the viewport on load
    document.querySelectorAll('.reveal').forEach(el => {
        if (revealSkipSelectors.some(cls => el.classList.contains(cls))) return;
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.classList.add('active');
            revealObserver.unobserve(el);
        }
    });

    // ─── Button Ripple Effect ─────────────────────────────────────────────────
    document.querySelectorAll('.cta-btn, .hire-btn, .about-btn, .submit-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.cssText = `
                position:absolute; border-radius:50%; pointer-events:none;
                width:${size}px; height:${size}px;
                left:${e.clientX - rect.left - size / 2}px;
                top:${e.clientY - rect.top - size / 2}px;
                background:rgba(255,255,255,0.4);
                transform:scale(0); animation:ripple 0.6s linear;
            `;
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // ─── Contact Form (AJAX POST to Django) ──────────────────────────────────
    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const data = new FormData(this);
            const submitBtn = this.querySelector('[type="submit"]');
            const originalText = submitBtn ? submitBtn.innerHTML : '';

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span>Sending…</span>';
            }

            fetch(this.action || window.location.href, {
                method: 'POST',
                body: data,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(r => r.json())
                .then(json => {
                    showNotification(json.message, json.success ? 'success' : 'error');
                    if (json.success) this.reset();
                })
                .catch(() => showNotification('Network error — please try again.', 'error'))
                .finally(() => {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                });
        });
    }

    // ─── Animate data-level progress bars (on scroll into view) ───────────────
    const bars = document.querySelectorAll('.premium-progress-fill[data-level], .skill-fill[data-level]');
    if (bars.length) {
        const barObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                const el = entry.target;
                el.style.width = (el.dataset.level || 0) + '%';
                barObserver.unobserve(el);
            });
        }, { threshold: 0.2 });
        bars.forEach(el => { el.style.width = '0%'; barObserver.observe(el); });
    }

    // ─── Animated stat counters ───────────────────────────────────────────────
    function animateCount(el) {
        const raw = el.textContent.trim();
        const match = raw.match(/^(\D*)(\d+)(.*)$/);   // prefix, number, suffix (e.g. "40+", "$5k")
        if (!match) return;                            // skip non-numeric (e.g. "∞")
        const prefix = match[1], target = parseInt(match[2], 10), suffix = match[3];
        const duration = 1400, start = performance.now();
        function tick(now) {
            const p = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 3);      // easeOutCubic
            el.textContent = prefix + Math.round(target * eased) + suffix;
            if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    const counters = document.querySelectorAll('.stat-number, .stat-num, .stat-val');
    if (counters.length) {
        const countObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                animateCount(entry.target);
                countObserver.unobserve(entry.target);
            });
        }, { threshold: 0.5 });
        counters.forEach(el => countObserver.observe(el));
    }

    // ─── Notification Helper ──────────────────────────────────────────────────
    function showNotification(msg, type = 'info') {
        const n = document.createElement('div');
        n.style.cssText = `
            position:fixed; top:24px; right:24px; z-index:9999;
            background:${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : 'var(--accent-primary)'};
            color:#fff; padding:1rem 1.5rem; border-radius:12px;
            font-weight:600; font-size:0.9rem;
            box-shadow:0 10px 30px rgba(0,0,0,0.3);
            transform:translateX(120%); transition:transform 0.3s ease;
        `;
        n.textContent = msg;
        document.body.appendChild(n);
        requestAnimationFrame(() => { n.style.transform = 'translateX(0)'; });
        setTimeout(() => {
            n.style.transform = 'translateX(120%)';
            setTimeout(() => n.remove(), 350);
        }, 3500);
    }

    // ─── Ripple keyframe injection ────────────────────────────────────────────
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple { to { transform: scale(4); opacity: 0; } }
        .nav-link:focus-visible,
        .social-icon:focus-visible,
        .cta-btn:focus-visible {
            outline: 2px solid var(--accent-primary);
            outline-offset: 2px;
        }
    `;
    document.head.appendChild(style);

    // ─── Done ─────────────────────────────────────────────────────────────────
    document.body.classList.add('js-loaded');
    console.log('Portfolio initialized ✓');
});

// ─── Global error handler ─────────────────────────────────────────────────────
window.addEventListener('error', e => console.error('JS Error:', e.error));
window.addEventListener('unhandledrejection', e => console.error('Unhandled:', e.reason));