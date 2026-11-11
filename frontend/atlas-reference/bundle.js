/* @ds-bundle: {"format":4,"namespace":"Atlas","components":[{"name":"Icon"},{"name":"Button"},{"name":"Kbd"},{"name":"TextField"},{"name":"Switch"},{"name":"Badge"},{"name":"ServiceCode"},{"name":"Window"},{"name":"Desktop"},{"name":"Dock"},{"name":"SiteHeader"},{"name":"CommandPalette"},{"name":"SectionHeader"},{"name":"ProjectRow"},{"name":"Stat"},{"name":"ContributionGraph"},{"name":"RepoCard"},{"name":"ActivityFeed"},{"name":"NowCard"},{"name":"IntegrationCard"},{"name":"AutomationRule"}]} */
(function () {
  'use strict';
  var React = window.React;
  var h = React.createElement;
  var useState = React.useState;
  var useEffect = React.useEffect;
  var useMemo = React.useMemo;
  var useId = React.useId;

  function cx() {
    var out = [];
    for (var i = 0; i < arguments.length; i++) if (arguments[i]) out.push(arguments[i]);
    return out.join(' ');
  }

  /* Atlas glyphs: 24px grid, 1.5 stroke, round caps. Strings are paths; {c:[cx,cy,r]} circles; {p:'…'} polygons. */
  var ICONS = {
    'arrow-up-right': ['M7 17 17 7', 'M8 7h9v9'],
    'arrow-right': ['M4 12h15', 'M13 6l6 6-6 6'],
    check: ['M5 12.5l4.5 4.5L19 7.5'],
    x: ['M6 6l12 12', 'M18 6 6 18'],
    plus: ['M12 5v14', 'M5 12h14'],
    search: [{ c: [10.5, 10.5, 6.5] }, 'M15.5 15.5 20.5 20.5'],
    refresh: ['M20 12a8 8 0 1 1-8-8c2.2 0 4.2.9 5.65 2.35L20 8.5', 'M20 4v4.5h-4.5'],
    link: ['M9.5 14.5l5-5', 'M11 6.5l1.5-1.5a4.24 4.24 0 0 1 6 6L17 12.5', 'M13 17.5 11.5 19a4.24 4.24 0 0 1-6-6L7 11.5'],
    star: [{ p: '12 3.5 14.6 9 20.5 9.6 16 13.6 17.3 19.5 12 16.5 6.7 19.5 8 13.6 3.5 9.6 9.4 9' }],
    fork: [{ c: [6, 5, 2] }, { c: [18, 5, 2] }, { c: [12, 19, 2] }, 'M6 7v1.5a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3V7', 'M12 11.5V17'],
    commit: [{ c: [12, 12, 3.5] }, 'M3 12h5.5', 'M15.5 12H21'],
    clock: [{ c: [12, 12, 8.5] }, 'M12 7.5V12l3 2'],
    alert: [{ c: [12, 12, 8.5] }, 'M12 7.5v5', 'M12 16.25v.5'],
    zap: ['M13 3 5 13.5h6.5L10.5 21 19 10.5h-6.5L13 3z'],
    music: ['M9 18V6l10-2v12', { c: [6.5, 18, 2.5] }, { c: [16.5, 16, 2.5] }],
    code: ['M8.5 7 3.5 12l5 5', 'M15.5 7l5 5-5 5'],
    pin: ['M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z', { c: [12, 10, 2.25] }],
    power: ['M12 3.5v8', 'M6.5 6.5a7.5 7.5 0 1 0 11 0']
  };

  function Icon(props) {
    var def = ICONS[props.name];
    if (!def) return null;
    var size = props.size || 16;
    var kids = def.map(function (d, i) {
      if (typeof d === 'string') return h('path', { key: i, d: d });
      if (d.c) return h('circle', { key: i, cx: d.c[0], cy: d.c[1], r: d.c[2] });
      return h('polygon', { key: i, points: d.p });
    });
    return h('svg', {
      className: cx('at-icon', props.className),
      width: size, height: size, viewBox: '0 0 24 24', fill: 'none',
      stroke: 'currentColor', strokeWidth: props.strokeWidth || 1.5,
      strokeLinecap: 'round', strokeLinejoin: 'round',
      role: props.title ? 'img' : undefined,
      'aria-hidden': props.title ? undefined : true,
      'aria-label': props.title || undefined
    }, kids);
  }
  Icon.names = Object.keys(ICONS);

  function Button(props) {
    var variant = props.variant || 'secondary';
    var size = props.size || 'md';
    var rest = Object.assign({}, props);
    ['variant', 'size', 'icon', 'iconRight', 'href', 'className', 'children'].forEach(function (k) { delete rest[k]; });
    var iconSize = size === 'sm' ? 14 : 16;
    var hasLabel = props.children != null && props.children !== false;
    var cls = cx('at-btn', 'at-btn--' + variant, size === 'sm' && 'at-btn--sm', !hasLabel && 'at-btn--icon', props.className);
    var inner = [
      props.icon ? h(Icon, { key: 'i', name: props.icon, size: iconSize }) : null,
      hasLabel ? h('span', { key: 'l' }, props.children) : null,
      props.iconRight ? h(Icon, { key: 'r', name: props.iconRight, size: iconSize }) : null
    ];
    if (props.href) return h('a', Object.assign({ href: props.href, className: cls }, rest), inner);
    return h('button', Object.assign({ type: 'button', className: cls }, rest), inner);
  }

  function Kbd(props) {
    return h('kbd', { className: cx('at-kbd', props.className) }, props.children);
  }

  function TextField(props) {
    var auto = useId();
    var fid = props.id || auto;
    var msgId = fid + '-msg';
    var rest = Object.assign({}, props);
    ['label', 'hint', 'error', 'id', 'className'].forEach(function (k) { delete rest[k]; });
    var msg = props.error || props.hint;
    return h('div', { className: cx('at-field', props.error && 'at-field--error', props.className) },
      props.label ? h('label', { className: 'at-field__label', htmlFor: fid }, props.label) : null,
      h('input', Object.assign({
        id: fid, className: 'at-field__input',
        'aria-invalid': props.error ? true : undefined,
        'aria-describedby': msg ? msgId : undefined
      }, rest)),
      msg ? h('p', { id: msgId, className: 'at-field__msg' },
        props.error ? h(Icon, { name: 'alert', size: 14 }) : null,
        h('span', null, msg)) : null);
  }

  function Switch(props) {
    var st = useState(props.defaultChecked != null ? props.defaultChecked : false);
    var on = props.checked != null ? props.checked : st[0];
    var auto = useId();
    var sid = props.id || auto;
    function toggle() {
      if (props.disabled) return;
      var next = !on;
      if (props.checked == null) st[1](next);
      if (props.onChange) props.onChange(next);
    }
    return h('span', { className: cx('at-switch-wrap', props.className) },
      h('button', {
        id: sid, type: 'button', role: 'switch', 'aria-checked': on,
        disabled: props.disabled, className: cx('at-switch', on && 'is-on'), onClick: toggle
      }, h('span', { className: 'at-switch__thumb' })),
      props.label ? h('label', { htmlFor: sid, className: 'at-switch__label' }, props.label) : null);
  }

  function Badge(props) {
    var tone = props.tone || 'neutral';
    return h('span', { className: cx('at-badge', 'at-badge--' + tone, props.className) },
      props.dot ? h('span', { className: cx('at-badge__dot', props.pulse && 'is-pulse'), 'aria-hidden': true }) : null,
      props.children);
  }

  function ServiceCode(props) {
    var size = props.size || 'md';
    return h('span', {
      className: cx('at-code', 'at-code--' + size, props.className),
      role: props.label ? 'img' : undefined,
      'aria-label': props.label || undefined,
      'aria-hidden': props.label ? undefined : true,
      title: props.label || undefined
    }, props.code);
  }

  function Window(props) {
    return h('section', {
      className: cx('at-win', props.active && 'is-active', props.className),
      style: props.style, role: props.role, 'aria-label': props.label || props.title, 'data-win': props.id
    },
      h('div', { className: 'at-win__bar', onPointerDown: props.onBarPointerDown },
        h('span', { className: 'at-win__ctl', 'aria-hidden': true }, h('i', null), h('i', null), h('i', null)),
        h('span', { className: 'at-win__title' }, props.title),
        props.barEnd ? h('span', { className: 'at-win__end' }, props.barEnd) : null),
      h('div', { className: cx('at-win__body', props.bodyClassName) }, props.children));
  }

  function Desktop(props) {
    var items = props.items || [];
    var deskRef = React.useRef(null);
    var ps = useState(function () {
      var m = {};
      items.forEach(function (it, i) { m[it.id] = { x: it.x, y: it.y, z: i + 1 }; });
      return m;
    });
    var pos = ps[0], setPos = ps[1];
    var as = useState(props.activeId || (items[0] && items[0].id));
    var active = as[0], setActive = as[1];
    var ds = useState(null);
    var dragging = ds[0], setDragging = ds[1];
    function topZ() {
      var z = 0;
      Object.keys(pos).forEach(function (k) { if (pos[k].z > z) z = pos[k].z; });
      return z + 1;
    }
    function start(id, e) {
      if (e.button != null && e.button !== 0) return;
      setActive(id);
      var desk = deskRef.current;
      if (!desk || (window.matchMedia && window.matchMedia('(max-width: 720px)').matches)) return;
      e.preventDefault();
      var win = e.currentTarget.parentNode;
      var dr = desk.getBoundingClientRect(), wr = win.getBoundingClientRect();
      var ox = e.clientX - wr.left, oy = e.clientY - wr.top;
      var z = topZ();
      var bar = e.currentTarget;
      if (bar.setPointerCapture) bar.setPointerCapture(e.pointerId);
      setDragging(id);
      setPos(function (p) { var n = Object.assign({}, p); n[id] = Object.assign({}, n[id], { z: z }); return n; });
      function mv(ev) {
        var x = Math.max(0, Math.min(dr.width - wr.width, ev.clientX - dr.left - ox));
        var y = Math.max(0, Math.min(dr.height - wr.height, ev.clientY - dr.top - oy));
        setPos(function (p) { var n = Object.assign({}, p); n[id] = { x: x + 'px', y: y, z: z }; return n; });
      }
      function up() {
        bar.removeEventListener('pointermove', mv);
        bar.removeEventListener('pointerup', up);
        bar.removeEventListener('pointercancel', up);
        setDragging(null);
      }
      bar.addEventListener('pointermove', mv);
      bar.addEventListener('pointerup', up);
      bar.addEventListener('pointercancel', up);
    }
    return h('div', { className: cx('at-desk', props.className), ref: deskRef, style: { '--desk-h': (props.height || 520) + 'px' } },
      items.map(function (it, i) {
        var p = pos[it.id] || { x: it.x, y: it.y, z: i + 1 };
        return h(Window, {
          key: it.id, id: it.id, title: it.title, label: it.label, active: active === it.id,
          className: cx(dragging === it.id && 'is-dragging', it.className),
          style: { '--x': p.x, '--y': (typeof p.y === 'number' ? p.y + 'px' : p.y), '--w': it.w, '--delay': (i * 100) + 'ms', zIndex: p.z },
          onBarPointerDown: function (e) { start(it.id, e); }
        }, it.content);
      }),
      props.children);
  }

  function Dock(props) {
    var items = props.items || [];
    return h('nav', { className: cx('at-dock', props.className), 'aria-label': props.label || 'Dock' },
      items.map(function (it, i) {
        var Tag = it.href ? 'a' : 'button';
        return h(Tag, {
          key: i, href: it.href, type: it.href ? undefined : 'button', onClick: it.onClick,
          className: cx('at-dock__item', it.active && 'is-active'), title: it.label, 'aria-label': it.label
        }, it.code);
      }));
  }

  function SiteHeader(props) {
    var links = props.links || [];
    var time = useClock(props.timeZone || 'Asia/Tashkent', true);
    return h('header', { className: 'at-menubar' },
      h('a', { className: 'at-menubar__brand', href: props.homeHref || '/' },
        h('span', { className: 'at-menubar__logo', 'aria-hidden': true }), props.name),
      h('nav', { className: 'at-menubar__nav', 'aria-label': 'Primary' },
        links.map(function (l, i) {
          return h('a', {
            key: i, href: l.href || '#', className: cx('at-menubar__link', l.active && 'is-active'),
            'aria-current': l.active ? 'page' : undefined
          }, l.label);
        })),
      h('div', { className: 'at-menubar__end' },
        props.status ? h('span', { className: 'at-menubar__status' },
          h('i', { className: props.status.pulse ? 'is-pulse' : undefined, 'aria-hidden': true }), props.status.label) : null,
        props.city ? h('span', { className: 'at-menubar__clock' }, props.city + ' ', h('time', null, time)) : null,
        h('button', { type: 'button', className: 'at-menubar__cmd', onClick: props.onCommand, 'aria-label': 'Open command palette' },
          h(Kbd, null, '⌘K'))));
  }

  function CommandPalette(props) {
    var groups = props.groups || [];
    var qs = useState('');
    var q = qs[0];
    var as = useState(0);
    var active = as[0];
    var setActive = as[1];
    var listId = useId();
    var flat = useMemo(function () {
      var out = [];
      var needle = q.trim().toLowerCase();
      groups.forEach(function (g) {
        (g.items || []).forEach(function (it) {
          var hay = (it.label + ' ' + (it.hint || '') + ' ' + (it.keywords || '')).toLowerCase();
          if (!needle || hay.indexOf(needle) !== -1) out.push(Object.assign({ group: g.label }, it));
        });
      });
      return out;
    }, [groups, q]);
    useEffect(function () { setActive(0); }, [q]);
    function choose(it) { if (props.onSelect) props.onSelect(it); }
    function onKey(e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setActive(function (a) { return Math.min(flat.length - 1, a + 1); }); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(function (a) { return Math.max(0, a - 1); }); }
      else if (e.key === 'Enter' && flat[active]) { e.preventDefault(); choose(flat[active]); }
      else if (e.key === 'Escape' && props.onClose) { props.onClose(); }
    }
    var rows = [];
    var last = null;
    flat.forEach(function (it, i) {
      if (it.group !== last) {
        rows.push(h('li', { key: 'g' + i, className: 'at-cmd__group', role: 'presentation' }, it.group));
        last = it.group;
      }
      rows.push(h('li', {
        key: i, id: listId + 'o' + i, role: 'option', 'aria-selected': i === active,
        className: cx('at-cmd__item', i === active && 'is-active'),
        onMouseMove: function () { if (active !== i) setActive(i); },
        onClick: function () { choose(it); }
      },
        it.icon ? h(Icon, { name: it.icon, size: 16 }) : h('span', { className: 'at-cmd__spacer', 'aria-hidden': true }),
        h('span', { className: 'at-cmd__label' }, it.label),
        it.hint ? h('span', { className: 'at-cmd__hint' }, it.hint) : null,
        it.shortcut ? h(Kbd, null, it.shortcut) : null));
    });
    return h(Window, { className: cx('at-cmd', props.className), role: 'dialog', label: props.label || 'Command palette', title: props.title || 'search', active: true },
      h('div', { className: 'at-cmd__search' },
        h(Icon, { name: 'search', size: 18 }),
        h('input', {
          className: 'at-cmd__input', value: q, placeholder: props.placeholder || 'Search pages, projects, actions…',
          onChange: function (e) { qs[1](e.target.value); }, onKeyDown: onKey,
          role: 'combobox', 'aria-expanded': true, 'aria-controls': listId, 'aria-autocomplete': 'list',
          'aria-activedescendant': flat[active] ? listId + 'o' + active : undefined,
          autoFocus: !!props.autoFocus
        }),
        h(Kbd, null, 'esc')),
      h('ul', { id: listId, role: 'listbox', className: 'at-cmd__list' },
        rows.length ? rows : h('li', { className: 'at-cmd__empty', role: 'presentation' }, 'Nothing matches “' + q + '”')));
  }

  function SectionHeader(props) {
    return h('header', { className: 'at-section' },
      h('div', { className: 'at-section__meta' },
        props.index ? h('span', { className: 'at-section__index' }, props.index) : null,
        props.kicker ? h('span', { className: 'at-section__kicker' }, props.kicker) : null),
      h('div', { className: 'at-section__row' },
        h('h2', { className: 'at-section__title' }, props.title),
        props.action || null));
  }

  function ProjectRow(props) {
    var Tag = props.href ? 'a' : 'div';
    var stack = props.stack || [];
    return h(Tag, { className: 'at-prow', href: props.href },
      h('span', { className: 'at-prow__index' }, props.index),
      h('span', { className: 'at-prow__main' },
        h('span', { className: 'at-prow__title' }, props.title,
          props.status ? h(Badge, { tone: props.status.tone || 'neutral', dot: props.status.dot }, props.status.label) : null),
        props.summary ? h('span', { className: 'at-prow__summary' }, props.summary) : null),
      h('span', { className: 'at-prow__stack' }, stack.join(' · ')),
      h('span', { className: 'at-prow__year' }, props.meta != null ? props.meta : props.year,
        props.href ? h(Icon, { name: 'arrow-up-right', size: 16 }) : null));
  }

  function Stat(props) {
    return h('div', { className: 'at-stat' },
      h('div', { className: 'at-stat__value' }, props.value,
        props.unit ? h('span', { className: 'at-stat__unit' }, props.unit) : null),
      h('div', { className: 'at-stat__label' }, props.label),
      props.delta ? h('div', { className: cx('at-stat__delta', props.trend === 'down' && 'is-down') }, props.delta) : null);
  }

  function sampleDays(n, seed) {
    var s = seed || 7;
    var out = [];
    for (var i = 0; i < n; i++) {
      s = (s * 9301 + 49297) % 233280;
      var r = s / 233280;
      var weekend = (i % 7 === 0 || i % 7 === 6) ? 0.35 : 1;
      var wave = Math.sin(i / 11) * 0.5 + 0.5;
      out.push(r < 0.24 / weekend * 0.6 ? 0 : Math.round(r * 9 * weekend * (0.35 + wave)));
    }
    return out;
  }

  function ContributionGraph(props) {
    var weeks = props.weeks || 26;
    var days = props.data || sampleDays(weeks * 7, props.seed);
    var cell = props.cell || 11;
    var gap = props.gap != null ? props.gap : 3;
    var max = 1;
    days.forEach(function (c) { if (c > max) max = c; });
    function lvl(c) { return c <= 0 ? 0 : c <= max * 0.25 ? 1 : c <= max * 0.5 ? 2 : c <= max * 0.75 ? 3 : 4; }
    var cols = Math.ceil(days.length / 7);
    var w = cols * (cell + gap) - gap;
    var ht = 7 * (cell + gap) - gap;
    var sum = props.total != null ? props.total : days.reduce(function (a, b) { return a + b; }, 0);
    var label = props.label || 'contributions in the last six months';
    return h('figure', { className: 'at-graph' },
      h('div', { className: 'at-graph__scroll' },
        h('svg', { width: w, height: ht, viewBox: '0 0 ' + w + ' ' + ht, role: 'img', 'aria-label': sum + ' ' + label },
          days.map(function (c, i) {
            return h('rect', {
              key: i, x: Math.floor(i / 7) * (cell + gap), y: (i % 7) * (cell + gap),
              width: cell, height: cell, rx: 2, className: 'at-graph__cell at-heat-' + lvl(c)
            }, h('title', null, c + (c === 1 ? ' contribution' : ' contributions')));
          }))),
      h('figcaption', { className: 'at-graph__caption' },
        h('span', null, h('strong', null, sum.toLocaleString('en-US')), ' ' + label),
        h('span', { className: 'at-graph__legend', 'aria-hidden': true }, 'Less',
          [0, 1, 2, 3, 4].map(function (l) { return h('i', { key: l, className: 'at-heat-' + l }); }), 'More')));
  }

  function RepoCard(props) {
    var Tag = props.href ? 'a' : 'div';
    return h(Tag, { className: 'at-repo', href: props.href },
      h('div', { className: 'at-repo__head' },
        h('span', { className: 'at-repo__name' },
          props.owner ? h('span', { className: 'at-repo__owner' }, props.owner + '/') : null, props.name),
        props.pinned ? h(Badge, null, 'Pinned') : null),
      props.description ? h('p', { className: 'at-repo__desc' }, props.description) : null,
      h('div', { className: 'at-repo__meta' },
        props.language ? h('span', { className: 'at-repo__lang' }, h('i', { 'aria-hidden': true }), props.language) : null,
        h('span', null, h(Icon, { name: 'star', size: 14 }), props.stars || 0, h('span', { className: 'at-sr' }, ' stars')),
        h('span', null, h(Icon, { name: 'fork', size: 14 }), props.forks || 0, h('span', { className: 'at-sr' }, ' forks')),
        props.updated ? h('span', { className: 'at-repo__updated' }, props.updated) : null));
  }

  function ActivityFeed(props) {
    var items = props.items || [];
    return h('ol', { className: 'at-feed', 'aria-label': props.label || 'Activity' },
      items.map(function (it, i) {
        return h('li', { key: i, className: cx('at-feed__row', it.tone === 'danger' && 'is-danger') },
          h('time', { className: 'at-feed__time', dateTime: it.datetime }, it.time),
          h(ServiceCode, { code: it.code, label: it.source, size: 'sm' }),
          h('span', { className: 'at-feed__text' },
            it.tone === 'danger' ? h(Icon, { name: 'alert', size: 14, title: 'Failed' }) : null,
            it.text,
            it.meta ? h('span', { className: 'at-feed__meta' }, it.meta) : null));
      }));
  }

  function useClock(timeZone, short) {
    var st = useState(function () { return new Date(); });
    useEffect(function () {
      var t = setInterval(function () { st[1](new Date()); }, 1000);
      return function () { clearInterval(t); };
    }, []);
    var opts = { timeZone: timeZone, hour: '2-digit', minute: '2-digit', hour12: false };
    if (!short) opts.second = '2-digit';
    try {
      return new Intl.DateTimeFormat('en-GB', opts).format(st[0]);
    } catch (e) {
      return st[0].toTimeString().slice(0, short ? 5 : 8);
    }
  }

  function NowCard(props) {
    var time = useClock(props.timeZone || 'Asia/Tashkent');
    function row(k, icon, main, sub) {
      return h('div', { className: 'at-now__row', key: k },
        h('span', { className: 'at-now__k' }, h(Icon, { name: icon, size: 14 }), k),
        h('span', { className: 'at-now__v' }, main, sub ? h('span', { className: 'at-now__sub' }, sub) : null));
    }
    return h(Window, { className: 'at-now', label: props.label || 'Now', title: props.title || 'now.app', active: props.active },
      h('div', { className: 'at-now__head' },
        h('span', { className: 'at-now__clock' }, time),
        props.status ? h(Badge, { tone: props.status.tone || 'live', dot: true, pulse: props.status.pulse }, props.status.label) : null),
      props.location ? row('Based in', 'pin', props.location, props.utc) : null,
      props.coding ? row('Coding', 'code', props.coding.project, props.coding.detail) : null,
      props.listening ? row('Listening', 'music', props.listening.track, props.listening.artist) : null);
  }

  var STATUS = {
    connected: { tone: 'live', label: 'Connected', dot: true },
    syncing: { tone: 'accent', label: 'Syncing', dot: true, pulse: true },
    error: { tone: 'danger', label: 'Needs attention', icon: 'alert' },
    off: { tone: 'neutral', label: 'Not connected' }
  };

  function IntegrationCard(props) {
    var status = STATUS[props.status] ? props.status : 'off';
    var s = STATUS[status];
    var scopes = props.scopes || [];
    var facts = [];
    if (props.account) facts.push(h('dt', { key: 'a' }, 'Account'), h('dd', { key: 'b' }, props.account));
    if (props.lastSync) facts.push(h('dt', { key: 'c' }, 'Last sync'), h('dd', { key: 'd' }, props.lastSync));
    if (scopes.length) facts.push(h('dt', { key: 'e' }, 'Access'), h('dd', { key: 'f' }, scopes.join(', ')));
    return h(Window, { className: cx('at-integ', 'is-' + status), title: 'connections/' + String(props.name || '').toLowerCase(), label: props.name },
      h('header', { className: 'at-integ__head' },
        h(ServiceCode, { code: props.code, size: 'lg' }),
        h('div', { className: 'at-integ__title' },
          h('h3', null, props.name),
          props.description ? h('p', null, props.description) : null),
        h(Badge, { tone: s.tone, dot: s.dot, pulse: s.pulse },
          s.icon ? h(Icon, { name: s.icon, size: 12 }) : null, s.label)),
      status !== 'off' && facts.length ? h('dl', { className: 'at-integ__facts' }, facts) : null,
      status === 'error' && props.error ? h('p', { className: 'at-integ__error', role: 'alert' },
        h(Icon, { name: 'alert', size: 16 }), h('span', null, props.error)) : null,
      h('footer', { className: 'at-integ__actions' },
        status === 'off' ? h(Button, { variant: 'primary', size: 'sm', icon: 'link', onClick: props.onConnect }, 'Connect') : null,
        status === 'error' ? h(Button, { variant: 'primary', size: 'sm', icon: 'refresh', onClick: props.onConnect }, 'Reconnect') : null,
        status === 'connected' ? h(Button, { size: 'sm', icon: 'refresh', onClick: props.onSync }, 'Sync now') : null,
        status === 'syncing' ? h(Button, { size: 'sm', icon: 'refresh', disabled: true }, 'Syncing…') : null,
        status !== 'off' ? h(Button, { variant: 'ghost', size: 'sm', onClick: props.onDisconnect }, 'Disconnect') : null));
  }

  function RuleStep(props) {
    var step = props.step || {};
    return h('div', { className: 'at-rule__step' },
      h('span', { className: 'at-rule__word' }, props.word),
      h('div', { className: 'at-rule__body' },
        h(ServiceCode, { code: step.code, label: step.service, size: 'sm' }),
        h('div', null,
          h('div', { className: 'at-rule__label' }, step.label),
          step.detail ? h('div', { className: 'at-rule__detail' }, step.detail) : null)));
  }

  function AutomationRule(props) {
    var stats = [];
    if (props.runs != null) stats.push(props.runs + (props.runs === 1 ? ' run' : ' runs'));
    if (props.lastRun) stats.push('last ' + props.lastRun);
    var tc = (props.trigger && props.trigger.code) || '';
    var ac = (props.action && props.action.code) || '';
    return h(Window, { className: 'at-rule', title: props.title || ('rules/' + tc + '-to-' + ac).toLowerCase(), label: props.label || 'Automation rule' },
      h('div', { className: 'at-rule__flow' },
        h(RuleStep, { word: 'When', step: props.trigger }),
        h('span', { className: 'at-rule__arrow', 'aria-hidden': true }, h(Icon, { name: 'arrow-right', size: 16 })),
        h(RuleStep, { word: 'Then', step: props.action })),
      h('footer', { className: 'at-rule__foot' },
        h('span', { className: 'at-rule__stats' }, stats.join(' · ')),
        h(Switch, { checked: props.enabled, defaultChecked: props.defaultEnabled != null ? props.defaultEnabled : true, onChange: props.onToggle, label: 'Enabled' })));
  }

  var api = {
    Icon: Icon, Button: Button, Kbd: Kbd, TextField: TextField, Switch: Switch, Badge: Badge,
    ServiceCode: ServiceCode, Window: Window, Desktop: Desktop, Dock: Dock, SiteHeader: SiteHeader, CommandPalette: CommandPalette,
    SectionHeader: SectionHeader, ProjectRow: ProjectRow, Stat: Stat, ContributionGraph: ContributionGraph,
    RepoCard: RepoCard, ActivityFeed: ActivityFeed, NowCard: NowCard, IntegrationCard: IntegrationCard,
    AutomationRule: AutomationRule
  };
  window.Atlas = Object.assign(window.Atlas || {}, api);
})();
