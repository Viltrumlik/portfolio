/* ============================================================================
   site-fx.js — standalone (no React runtime)
   <hud-orb> Three.js web component + vanilla DOM effects:
   reveal-on-scroll, count-up, skill bars, card tilt, typewriter, mobile nav.
   ========================================================================== */
(function () {
  "use strict";

  /* ----------------------------- <hud-orb> ------------------------------ */
  function initOrb(el) {
    var THREE = window.THREE;
    if (!THREE) { el._t = setTimeout(function () { initOrb(el); }, 120); return; }
    var w = el.clientWidth || 0, h = el.clientHeight || 0;
    if (w < 2 || h < 2) { el._t = setTimeout(function () { initOrb(el); }, 120); return; }
    var canvas = el._canvas;
    var renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(w, h, false);
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    camera.position.z = 4.7;

    var accent = new THREE.Color(el.getAttribute("accent") || "#4f7cff");
    var accent2 = new THREE.Color(el.getAttribute("accent2") || "#9bb6ff");
    var radius = parseFloat(el.getAttribute("radius") || "1.5");
    var detail = parseInt(el.getAttribute("detail") || "1");
    var starN = parseInt(el.getAttribute("stars") || "460");

    var grp = new THREE.Group(); scene.add(grp);
    var ico = new THREE.IcosahedronGeometry(radius, detail);
    grp.add(new THREE.LineSegments(new THREE.WireframeGeometry(ico), new THREE.LineBasicMaterial({ color: accent, transparent: true, opacity: 0.6 })));
    var core = new THREE.Mesh(new THREE.IcosahedronGeometry(radius * 0.66, 0), new THREE.MeshBasicMaterial({ color: 0x16306e, transparent: true, opacity: 0.38 }));
    grp.add(core);
    grp.add(new THREE.Points(ico, new THREE.PointsMaterial({ color: accent2, size: radius * 0.05, transparent: true, opacity: 0.95 })));
    var ring = new THREE.Mesh(new THREE.TorusGeometry(radius * 1.5, 0.011, 8, 140), new THREE.MeshBasicMaterial({ color: accent, transparent: true, opacity: 0.55 }));
    ring.rotation.x = Math.PI * 0.42; grp.add(ring);
    var ring2 = new THREE.Mesh(new THREE.TorusGeometry(radius * 1.83, 0.008, 8, 140), new THREE.MeshBasicMaterial({ color: accent2, transparent: true, opacity: 0.32 }));
    ring2.rotation.x = Math.PI * 0.62; ring2.rotation.y = Math.PI * 0.2; grp.add(ring2);

    var pos = new Float32Array(starN * 3);
    for (var i = 0; i < starN; i++) {
      var r = 3.2 + Math.random() * 7, th = Math.random() * Math.PI * 2, ph = Math.acos(2 * Math.random() - 1);
      pos[i * 3] = r * Math.sin(ph) * Math.cos(th);
      pos[i * 3 + 1] = r * Math.sin(ph) * Math.sin(th);
      pos[i * 3 + 2] = r * Math.cos(ph);
    }
    var sg = new THREE.BufferGeometry();
    sg.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    var stars = new THREE.Points(sg, new THREE.PointsMaterial({ color: 0x6f86c8, size: 0.028, transparent: true, opacity: 0.6 }));
    scene.add(stars);

    var target = { x: 0, y: 0 }, cur = { x: 0, y: 0 };
    el._onMove = function (ev) {
      var rc = canvas.getBoundingClientRect();
      target.x = (ev.clientX - rc.left) / rc.width - 0.5;
      target.y = (ev.clientY - rc.top) / rc.height - 0.5;
    };
    window.addEventListener("pointermove", el._onMove);
    el._ro = new ResizeObserver(function () {
      w = el.clientWidth || w; h = el.clientHeight || h;
      renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    });
    el._ro.observe(el);

    var clock = new THREE.Clock();
    function loop() {
      if (!el.isConnected) return;
      var t = clock.getElapsedTime();
      cur.x += (target.x - cur.x) * 0.05; cur.y += (target.y - cur.y) * 0.05;
      grp.rotation.y = t * 0.16 + cur.x * 0.9;
      grp.rotation.x = cur.y * 0.6 + Math.sin(t * 0.3) * 0.1;
      ring.rotation.z = t * 0.24; ring2.rotation.z = -t * 0.17;
      stars.rotation.y = t * 0.02; core.scale.setScalar(1 + Math.sin(t * 1.6) * 0.05);
      renderer.render(scene, camera);
      el._raf = requestAnimationFrame(loop);
    }
    loop();
  }

  if (!customElements.get("hud-orb")) {
    customElements.define("hud-orb", class extends HTMLElement {
      connectedCallback() {
        this.style.display = "block"; this.style.position = "absolute"; this.style.inset = "0";
        if (!this._canvas) {
          var c = document.createElement("canvas");
          c.style.cssText = "position:absolute;inset:0;width:100%;height:100%;display:block";
          this.appendChild(c); this._canvas = c;
        }
        initOrb(this);
      }
      disconnectedCallback() {
        if (this._raf) cancelAnimationFrame(this._raf);
        if (this._t) clearTimeout(this._t);
        if (this._onMove) window.removeEventListener("pointermove", this._onMove);
        if (this._ro) this._ro.disconnect();
      }
    });
  }

  /* --------------------------- DOM effects ----------------------------- */
  function countUp(el) {
    if (el._done) return; el._done = true;
    var target = parseInt(el.getAttribute("data-count")) || 0;
    var suffix = el.getAttribute("data-suffix") || "";
    var dur = 1300, t0 = performance.now();
    (function step(t) {
      var p = Math.min(1, (t - t0) / dur);
      el.textContent = Math.floor((1 - Math.pow(1 - p, 3)) * target) + suffix;
      if (p < 1) requestAnimationFrame(step);
    })(performance.now());
  }

  function fillBars(scope) {
    (scope || document).querySelectorAll(".bar > span[data-level]").forEach(function (b) {
      b.style.width = (parseInt(b.getAttribute("data-level")) || 0) + "%";
    });
  }

  function typewriter(el) {
    var words; try { words = JSON.parse(el.getAttribute("data-words") || "[]"); } catch (e) { words = []; }
    if (!words.length) return;
    var wi = 0, ci = 0, del = false;
    (function tick() {
      var word = words[wi];
      el.textContent = word.slice(0, ci);
      if (!del && ci < word.length) { ci++; setTimeout(tick, 70); }
      else if (!del && ci === word.length) { del = true; setTimeout(tick, 1500); }
      else if (del && ci > 0) { ci--; setTimeout(tick, 35); }
      else { del = false; wi = (wi + 1) % words.length; setTimeout(tick, 350); }
    })();
  }

  function tilt(card) {
    card.addEventListener("pointermove", function (ev) {
      var r = card.getBoundingClientRect();
      var px = (ev.clientX - r.left) / r.width - 0.5;
      var py = (ev.clientY - r.top) / r.height - 0.5;
      card.style.transform = "perspective(1000px) rotateY(" + (px * 6) + "deg) rotateX(" + (-py * 6) + "deg) translateY(-4px)";
    });
    card.addEventListener("pointerleave", function () {
      card.style.transform = "perspective(1000px) rotateY(0) rotateX(0) translateY(0)";
    });
  }

  function init() {
    // Reveal on scroll (+ trigger bars/counts inside revealed blocks)
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("in");
        e.target.querySelectorAll("[data-count]").forEach(countUp);
        fillBars(e.target);
        io.unobserve(e.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".rv").forEach(function (el) { io.observe(el); });

    // Elements with counts/bars that aren't inside a .rv: fire on view too
    document.querySelectorAll("[data-count]").forEach(function (el) {
      if (!el.closest(".rv")) io2(el, function () { countUp(el); });
    });
    if (!document.querySelector(".rv")) fillBars(document);

    document.querySelectorAll("[data-typewriter]").forEach(typewriter);
    document.querySelectorAll("[data-tilt]").forEach(tilt);

    // Mobile nav
    var burger = document.querySelector(".nav-burger");
    if (burger) burger.addEventListener("click", function () {
      document.querySelector(".nav").classList.toggle("open");
    });
  }

  function io2(el, cb) {
    var o = new IntersectionObserver(function (en) {
      en.forEach(function (e) { if (e.isIntersecting) { cb(); o.unobserve(el); } });
    }, { threshold: 0.3 });
    o.observe(el);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
