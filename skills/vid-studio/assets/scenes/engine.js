/* Vid Studio scene engine.
 * Builds a HyperFrames-compatible motion-graphics composition (DOM + one paused GSAP timeline)
 * from a channel look (design.json) and a list of scenes (references/scenes.md).
 * Plain browser JS, no build step. Requires window.gsap (3.x).
 *
 * Public API (window.VidScenes):
 *   build(container, design, scenes, options) -> Promise<{timeline, duration, stage, scenes:[{start,duration,type,beat}], layout}>
 *   normalizeDesign(design) -> design with every key filled
 *   fontsFor(design, {devanagari}) -> Google Fonts CSS2 URL
 *   normalizeScenes(scenes), layout(design), dimensions(aspect), totalDuration(scenes)
 *   parseValue(str), formatValue(number, parsed), FONTS, DEFAULT_DESIGN, version
 */
(function (root) {
  'use strict';

  var VERSION = '1.0.0';
  var COMPOSITION_ID = 'vid';

  // family -> [weights available on Google Fonts, devanagari (1/0), category]
  var FONT_TABLE = {"Anton":[[400],0,"display"],"Bebas Neue":[[400],0,"display"],"Archivo Black":[[400],0,"display"],"Oswald":[[200,300,400,500,600,700],0,"display"],"Unbounded":[[200,300,400,500,600,700,800,900],0,"display"],"Syne":[[400,500,600,700,800],0,"display"],"Teko":[[300,400,500,600,700],1,"display"],"Rajdhani":[[300,400,500,600,700],1,"display"],"Khand":[[300,400,500,600,700],1,"display"],"Yatra One":[[400],1,"display"],"Rozha One":[[400],1,"display"],"Baloo 2":[[400,500,600,700,800],1,"display"],"Gotu":[[400],1,"display"],"DM Serif Display":[[400],0,"serif"],"Fraunces":[[100,200,300,400,500,600,700,800,900],0,"serif"],"Playfair Display":[[400,500,600,700,800,900],0,"serif"],"Instrument Serif":[[400],0,"serif"],"Tiro Devanagari Hindi":[[400],1,"serif"],"Noto Serif Devanagari":[[100,200,300,400,500,600,700,800,900],1,"serif"],"Martel":[[200,300,400,600,700,800,900],1,"serif"],"Eczar":[[400,500,600,700,800],1,"serif"],"Laila":[[300,400,500,600,700],1,"serif"],"Karma":[[300,400,500,600,700],1,"serif"],"Kurale":[[400],1,"serif"],"Inter":[[100,200,300,400,500,600,700,800,900],0,"sans"],"Space Grotesk":[[300,400,500,600,700],0,"sans"],"Sora":[[100,200,300,400,500,600,700,800],0,"sans"],"Manrope":[[200,300,400,500,600,700,800],0,"sans"],"Bricolage Grotesque":[[200,300,400,500,600,700,800],0,"sans"],"Mukta":[[200,300,400,500,600,700,800],1,"sans"],"Hind":[[300,400,500,600,700],1,"sans"],"Poppins":[[100,200,300,400,500,600,700,800,900],1,"sans"],"Noto Sans Devanagari":[[100,200,300,400,500,600,700,800,900],1,"sans"],"Anek Devanagari":[[100,200,300,400,500,600,700,800],1,"sans"],"Palanquin":[[100,200,300,400,500,600,700],1,"sans"],"Sarala":[[400,700],1,"sans"],"Martel Sans":[[200,300,400,600,700,800,900],1,"sans"],"Yantramanav":[[100,300,400,500,700,900],1,"sans"],"JetBrains Mono":[[100,200,300,400,500,600,700,800],0,"mono"],"IBM Plex Mono":[[100,200,300,400,500,600,700],0,"mono"],"Space Mono":[[400,700],0,"mono"],"DM Mono":[[300,400,500],0,"mono"],"Caveat":[[400,500,600,700],0,"hand"],"Kalam":[[300,400,700],1,"hand"],"Amita":[[400,700],1,"hand"]};

  var DEFAULT_DESIGN = {
    aspect: '9:16',
    colors: { background: '#121212', surface: '#1E1E1E', text: '#F7F3EA', muted: '#9C978D', accent: '#FFC233', accent2: '#FF7A45', negative: '#FF5D5D' },
    fonts: { display: 'Bricolage Grotesque', body: 'Mukta', mono: 'JetBrains Mono' },
    type: { scale: 1.0, display_case: 'none', display_weight: 800, tracking: -0.03 },
    motion: { energy: 'high', easing: 'snappy', transition: 'slide' },
    captions: { style: 'highlight', position: 'lower', highlight: 'accent', max_words: 4, size: 'medium' },
    background: { style: 'grain', pattern: 'none' },
    images: { treatment: 'dim' },
    sources: { show: true },
    progress: { show: true },
    radius: 12,
    logo: { text: '', position: 'top-left' },
    custom_css: ''
  };

  var ASPECTS = { '9:16': [1080, 1920], '16:9': [1920, 1080], '1:1': [1080, 1080], '4:5': [1080, 1350] };
  // Platform-safe margins in px (9:16: Shorts/Reels UI covers the top ~10%, bottom ~20%, right-edge buttons).
  var SAFE = {
    '9:16': { top: 192, bottom: 384, left: 84, right: 128 },
    '16:9': { top: 72, bottom: 72, left: 120, right: 120 },
    '1:1': { top: 80, bottom: 96, left: 84, right: 84 },
    '4:5': { top: 88, bottom: 120, left: 84, right: 84 }
  };
  var ENUM = {
    display_case: ['upper', 'title', 'none'],
    energy: ['calm', 'medium', 'high'],
    easing: ['smooth', 'snappy', 'bouncy'],
    transition: ['cut', 'fade', 'slide', 'zoom', 'wipe'],
    capStyle: ['none', 'plain', 'boxed', 'karaoke', 'highlight', 'pop'],
    capPos: ['lower', 'middle', 'upper'],
    bgStyle: ['solid', 'gradient', 'grain', 'paper'],
    pattern: ['none', 'grid', 'dots', 'lines'],
    logoPos: ['top-left', 'top-right', 'bottom-left', 'bottom-right'],
    capSize: ['small', 'medium', 'large'],
    treatment: ['natural', 'dim', 'mono', 'duotone']
  };
  var CAP_SIZE = { small: 0.88, medium: 1.08, large: 1.3 };
  var TYPES = ['title', 'stat', 'bars', 'compare', 'list', 'quote', 'timeline', 'text', 'image', 'end'];

  var MOTION = {
    calm: { dur: 1.3, dist: 0.6, st: 1.35, tx: 0.9 },
    medium: { dur: 1.0, dist: 1.0, st: 1.0, tx: 0.7 },
    high: { dur: 0.8, dist: 1.35, st: 0.72, tx: 0.56 }
  };
  var EASES = {
    smooth: { out: 'power3.out', inOut: 'power2.inOut', pop: 'power3.out', num: 'power2.out', in: 'power2.in', bar: 'power3.out' },
    snappy: { out: 'expo.out', inOut: 'expo.inOut', pop: 'back.out(2)', num: 'expo.out', in: 'power3.in', bar: 'expo.out' },
    bouncy: { out: 'back.out(1.5)', inOut: 'back.inOut(1.3)', pop: 'elastic.out(1, 0.55)', num: 'power3.out', in: 'back.in(1.3)', bar: 'back.out(1.2)' }
  };

  // ---------------------------------------------------------------- utils
  function isObj(o) { return !!o && typeof o === 'object' && !Array.isArray(o); }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function merge(base, over) {
    var out = clone(base);
    if (!isObj(over)) return out;
    Object.keys(over).forEach(function (k) {
      var v = over[k];
      if (v === undefined || v === null) return;
      if (isObj(out[k]) && isObj(v)) out[k] = merge(out[k], v);
      else out[k] = isObj(v) || Array.isArray(v) ? clone(v) : v;
    });
    return out;
  }
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function num(v, d) { var n = Number(v); return isFinite(n) ? n : d; }
  function pick(v, list, d) { return list.indexOf(v) >= 0 ? v : d; }
  function isHex(c) { return typeof c === 'string' && /^#([0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(c.trim()); }
  function rgb(hex) {
    var h = String(hex).trim().replace('#', '');
    if (h.length === 3) h = h.split('').map(function (c) { return c + c; }).join('');
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }
  function rgba(hex, a) { var c = rgb(hex); return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; }
  function lum(hex) {
    var c = rgb(hex).map(function (v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function contrast(a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  function mulberry32(seed) {
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function r3(x) { return Math.round(x * 1000) / 1000; }
  function delay(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }
  function withTimeout(p, ms) { return Promise.race([Promise.resolve(p).catch(function () {}), delay(ms)]); }

  // ---------------------------------------------------------------- text
  var DV_CLASS = '\\u0900-\\u097F\\uA8E0-\\uA8FF\\u1CD0-\\u1CFF';
  var DV_RE = new RegExp('[' + DV_CLASS + ']');
  var DV_RUN = new RegExp('[' + DV_CLASS + '\\u200C\\u200D]+(?:[\\s\\u00A0]+[' + DV_CLASS + '\\u200C\\u200D]+)*', 'g');
  function hasDv(s) { return DV_RE.test(String(s == null ? '' : s)); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function wrapDv(html) { return html.replace(DV_RUN, function (m) { return '<span class="dv" lang="hi">' + m + '</span>'; }); }
  function plain(s) { return String(s == null ? '' : s).replace(/\*/g, '').trim(); }
  // escaped HTML, Devanagari runs tagged, *emphasis* in accent
  function rich(s) {
    var parts = String(s == null ? '' : s).split(/\*([^*]+)\*/);
    return parts.map(function (p, i) {
      var h = wrapDv(esc(p.replace(/\*/g, '')));
      return i % 2 ? '<span class="em">' + h + '</span>' : h;
    }).join('');
  }
  // word spans (optionally masked) with *emphasis* across words; autoEm(word) can force emphasis
  function wordsHTML(s, opts) {
    opts = opts || {};
    var tokens = String(s == null ? '' : s).trim().split(/\s+/).filter(Boolean);
    var on = false;
    return tokens.map(function (tok) {
      var starts = tok.charAt(0) === '*';
      var ends = tok.length > 1 && /\*[^\w\u0900-\u097F]*$/.test(tok);
      if (starts) on = true;
      var em = on || (opts.autoEm && opts.autoEm(tok));
      if (ends || (starts && tok.length > 1 && tok.slice(1).indexOf('*') >= 0)) on = false;
      var clean = tok.replace(/\*/g, '');
      if (!clean) return '';
      var inner = '<span class="w' + (em ? ' em' : '') + '">' + wrapDv(esc(clean)) + '' + '</span>';
      return opts.mask === false ? inner : '<span class="wm">' + inner + '</span>';
    }).filter(Boolean).join(' ');
  }
  function tagLang(el, s) {
    if (hasDv(s)) {
      el.classList.add('has-dv');
      var t = plain(s), dv = (t.match(new RegExp('[' + DV_CLASS + ']', 'g')) || []).length;
      if (dv > t.replace(/\s/g, '').length * 0.5) el.setAttribute('lang', 'hi');
    }
    return el;
  }

  // ---------------------------------------------------------------- numbers
  var UNITS = [
    ['lakhs', 1e5], ['lakh', 1e5], ['lacs', 1e5], ['lac', 1e5], ['\u0932\u093E\u0916', 1e5], ['crores', 1e7], ['crore', 1e7], ['cr', 1e7], ['\u0915\u0930\u094B\u0921\u093C', 1e7], ['\u0915\u0930\u094B\u0921', 1e7],
    ['thousand', 1e3], ['\u0939\u091C\u093C\u093E\u0930', 1e3], ['\u0939\u091C\u093E\u0930', 1e3], ['k', 1e3], ['million', 1e6], ['mn', 1e6], ['billion', 1e9], ['bn', 1e9], ['trillion', 1e12], ['tn', 1e12]
  ];
  var CASE_UNITS = [['L', 1e5], ['M', 1e6], ['B', 1e9], ['T', 1e12], ['K', 1e3]];
  function unitMult(suffix) {
    var s = String(suffix || '').replace(/^[\s\u00A0]+/, '');
    var notLetter = function (ch) { return !ch || !/[A-Za-z\u0900-\u097F]/.test(ch); };
    for (var i = 0; i < CASE_UNITS.length; i++) if (s.charAt(0) === CASE_UNITS[i][0] && notLetter(s.charAt(1))) return CASE_UNITS[i][1];
    var low = s.toLowerCase();
    for (var j = 0; j < UNITS.length; j++) {
      var u = UNITS[j][0];
      if (low.indexOf(u) === 0 && (DV_RE.test(u) || notLetter(low.charAt(u.length)))) return UNITS[j][1];
    }
    return 1;
  }
  function parseValue(raw) {
    var s = plain(raw);
    var norm = s.replace(/[\u0966-\u096F]/g, function (c) { return String(c.charCodeAt(0) - 0x966); });
    var m = /\d[\d,]*(?:\.\d+)?/.exec(norm);
    if (!m) return null;
    var numStr = m[0].replace(/,+$/, '');
    var idx = m.index;
    var parts = numStr.split('.');
    var ip = parts[0], dec = parts[1] || '';
    var grouping = 'none';
    if (ip.indexOf(',') >= 0) {
      var g = ip.split(',');
      grouping = (g.length >= 3 && g.slice(1, -1).every(function (x) { return x.length === 2; }) && g[g.length - 1].length === 3) ? 'indian' : 'intl';
    }
    var prefix = s.slice(0, idx), suffix = s.slice(idx + numStr.length);
    var value = parseFloat(ip.replace(/,/g, '') + (dec ? '.' + dec : ''));
    var negative = /[-\u2212]\s*$/.test(prefix);
    var mult = unitMult(suffix);
    var year = !prefix.trim() && !suffix.trim() && !dec && grouping === 'none' && value >= 1800 && value <= 2100;
    return {
      value: value, decimals: dec.length, grouping: grouping, prefix: prefix, suffix: suffix,
      devanagari: /[\u0966-\u096F]/.test(s.slice(idx, idx + numStr.length)), negative: negative,
      magnitude: (negative ? -1 : 1) * value * mult, year: year, raw: s
    };
  }
  function groupIndian(ip) {
    if (ip.length <= 3) return ip;
    return ip.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + ip.slice(-3);
  }
  function formatValue(n, p) {
    var str = Math.abs(n).toFixed(p.decimals);
    var bits = str.split('.');
    var ip = bits[0];
    if (p.grouping === 'indian') ip = groupIndian(ip);
    else if (p.grouping === 'intl') ip = ip.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    var out = ip + (bits[1] ? '.' + bits[1] : '');
    if (p.devanagari) out = out.replace(/\d/g, function (d) { return String.fromCharCode(0x966 + Number(d)); });
    return out;
  }
  function valueHTML(raw, p, cls) {
    if (!p) return '<span class="txt">' + rich(raw) + '</span>';
    var suf = p.suffix;
    var sufCls = 'suf' + (/^\s*%/.test(suf) ? ' pct' : '');
    return (p.prefix ? '<span class="pre">' + rich(p.prefix.trim()) + '</span>' : '') +
      '<span class="num tnum' + (cls ? ' ' + cls : '') + '">' + formatValue(p.value, p) + '</span>' +
      (suf ? '<span class="' + sufCls + '">' + rich(suf.replace(/^\s+/, '\u2009')) + '</span>' : '');
  }

  // ---------------------------------------------------------------- design
  function normalizeDesign(input) {
    var d = merge(DEFAULT_DESIGN, isObj(input) ? input : {});
    Object.keys(DEFAULT_DESIGN).forEach(function (k) {
      if (isObj(DEFAULT_DESIGN[k]) && !isObj(d[k])) d[k] = clone(DEFAULT_DESIGN[k]);
    });
    if (!ASPECTS[d.aspect]) d.aspect = '9:16';
    Object.keys(DEFAULT_DESIGN.colors).forEach(function (k) { if (!isHex(d.colors[k])) d.colors[k] = DEFAULT_DESIGN.colors[k]; else d.colors[k] = d.colors[k].trim(); });
    Object.keys(DEFAULT_DESIGN.fonts).forEach(function (k) { if (typeof d.fonts[k] !== 'string' || !d.fonts[k].trim()) d.fonts[k] = DEFAULT_DESIGN.fonts[k]; else d.fonts[k] = d.fonts[k].trim(); });
    d.type.scale = clamp(num(d.type.scale, 1), 0.6, 1.6);
    d.type.display_case = pick(d.type.display_case, ENUM.display_case, 'upper');
    d.type.display_weight = clamp(Math.round(num(d.type.display_weight, 800) / 100) * 100, 100, 900);
    d.type.tracking = clamp(num(d.type.tracking, 0), -0.1, 0.2);
    d.motion.energy = pick(d.motion.energy, ENUM.energy, 'medium');
    d.motion.easing = pick(d.motion.easing, ENUM.easing, 'smooth');
    d.motion.transition = pick(d.motion.transition, ENUM.transition, 'fade');
    d.captions.style = pick(d.captions.style, ENUM.capStyle, 'plain');
    d.captions.position = pick(d.captions.position, ENUM.capPos, 'lower');
    if (!isHex(d.captions.highlight)) d.captions.highlight = pick(d.captions.highlight, ['accent', 'accent2', 'text'], 'accent');
    d.captions.max_words = clamp(Math.round(num(d.captions.max_words, 4)), 1, 8);
    d.captions.size = pick(d.captions.size, ENUM.capSize, 'medium');
    d.images.treatment = pick(d.images.treatment, ENUM.treatment, 'dim');
    d.sources.show = d.sources.show !== false;
    d.progress.show = d.progress.show !== false;
    d.background.style = pick(d.background.style, ENUM.bgStyle, 'solid');
    d.background.pattern = pick(d.background.pattern, ENUM.pattern, 'none');
    d.radius = clamp(num(d.radius, 18), 0, 64);
    if (!isObj(d.logo)) d.logo = clone(DEFAULT_DESIGN.logo);
    d.logo.text = typeof d.logo.text === 'string' ? d.logo.text : '';
    d.logo.position = pick(d.logo.position, ENUM.logoPos, 'top-left');
    d.custom_css = typeof d.custom_css === 'string' ? d.custom_css : '';
    return d;
  }

  function fontInfo(family) { return FONT_TABLE[family] || null; }
  function nearest(weights, w) {
    return weights.reduce(function (best, x) { return Math.abs(x - w) < Math.abs(best - w) ? x : best; }, weights[0]);
  }
  function fontPlan(design, needDv) {
    var f = design.fonts, plan = {};
    function add(fam, ws) {
      var info = fontInfo(fam);
      plan[fam] = plan[fam] || [];
      ws.forEach(function (w) {
        var x = info ? nearest(info[0], w) : 400;
        if (plan[fam].indexOf(x) < 0) plan[fam].push(x);
      });
    }
    add(f.display, [design.type.display_weight, 700, 900]);
    add(f.body, [400, 500, 600, 700, 800]);
    add(f.mono, [400, 500, 600, 700]);
    var fallback = null;
    if (needDv) {
      var dvBody = isDvFont(f.body), dvDisp = isDvFont(f.display), dvMono = isDvFont(f.mono);
      if (!dvBody && !(dvDisp && dvMono)) fallback = 'Noto Sans Devanagari';
      if (!dvBody && dvDisp && !dvMono) fallback = 'Noto Sans Devanagari';
      if (fallback) add(fallback, [400, 500, 600, 700, 800, design.type.display_weight]);
    }
    Object.keys(plan).forEach(function (k) { plan[k].sort(function (a, b) { return a - b; }); });
    return { families: plan, fallback: fallback };
  }
  function isDvFont(fam) { var i = fontInfo(fam); return !!(i && i[1]); }
  function fontsFor(design, opts) {
    design = normalizeDesign(design);
    var plan = fontPlan(design, !!(opts && opts.devanagari));
    var q = Object.keys(plan.families).map(function (fam) {
      var ws = plan.families[fam];
      var name = encodeURIComponent(fam).replace(/%20/g, '+');
      if (!fontInfo(fam) || (ws.length === 1 && ws[0] === 400)) return 'family=' + name;
      return 'family=' + name + ':wght@' + ws.join(';');
    });
    return 'https://fonts.googleapis.com/css2?' + q.join('&') + '&display=block';
  }
  function generic(fam) {
    var i = fontInfo(fam), c = i ? i[2] : 'sans';
    return c === 'serif' ? 'serif' : c === 'mono' ? 'monospace' : c === 'hand' ? 'cursive' : 'sans-serif';
  }
  function stack(primary, design, fallback) {
    var list = [primary];
    if (!isDvFont(primary)) {
      if (isDvFont(design.fonts.body) && design.fonts.body !== primary) list.push(design.fonts.body);
      else if (isDvFont(design.fonts.display) && design.fonts.display !== primary) list.push(design.fonts.display);
    }
    if (fallback) list.push(fallback);
    return list.map(function (f) { return '"' + f.replace(/"/g, '') + '"'; }).join(', ') + ', ' + generic(primary);
  }

  var fontJobs = {};
  function ensureFonts(design, needDv, text) {
    var href = fontsFor(design, { devanagari: needDv });
    var plan = fontPlan(design, needDv);
    if (typeof document === 'undefined' || !document.fonts || !document.fonts.load) {
      plan.useSystem = true;
      return Promise.resolve(plan);
    }
    // Load every glyph used by this composition, including unicode-range subsets.
    var sample = 'AaBbGg0123456789\u20B9$% ' + (text || '');
    var linkReady;
    if (fontJobs[href]) linkReady = fontJobs[href];
    else {
      var link = document.createElement('link');
      link.rel = 'stylesheet'; link.href = href; link.setAttribute('data-vid-fonts', '');
      linkReady = new Promise(function (res) {
        link.onload = function () { res(true); };
        link.onerror = function () { res(false); };
      });
      document.head.appendChild(link);
      // Keep earlier sheets: other fitted stages may still use their font faces.
      fontJobs[href] = linkReady;
    }
    var loaded = linkReady.then(function (ok) {
      if (!ok) return false;
      var loads = [];
      Object.keys(plan.families).forEach(function (fam) {
        plan.families[fam].forEach(function (w) {
          loads.push(document.fonts.load(w + ' 100px "' + fam + '"', sample));
        });
      });
      return Promise.all(loads).then(function (results) {
        return results.every(function (faces) { return faces.length > 0 && faces.every(function (face) { return face.status === 'loaded'; }); });
      });
    }).catch(function () { return false; });
    // Resolve once. A timed-out stage uses only system families before fitting;
    // a late stylesheet/font completion can never swap its measured fonts.
    return new Promise(function (res) {
      var settled = false;
      var timer = setTimeout(function () { finish(false); }, 5000);
      function finish(ok) {
        if (settled) return;
        settled = true; clearTimeout(timer);
        plan.useSystem = !ok;
        res(plan);
      }
      loaded.then(finish);
    });
  }

  // ---------------------------------------------------------------- scenes + layout
  function normalizeScenes(list) {
    var arr = Array.isArray(list) ? list : (isObj(list) && Array.isArray(list.scenes) ? list.scenes : []);
    return arr.filter(isObj).map(function (sc) {
      var type = String(sc.type || '').toLowerCase().trim();
      var data = isObj(sc.data) ? clone(sc.data) : {};
      if (TYPES.indexOf(type) < 0) {
        var desc = data.description || [type].concat(Object.keys(data).map(function (k) { return typeof data[k] === 'string' ? data[k] : ''; })).filter(Boolean).join(' | ');
        data = { description: desc, url: data.url || '' };
        type = 'image';
      }
      if (type === 'image' && !data.url && data.src) data.url = data.src;
      return {
        beat: String(sc.beat || ''), type: type,
        duration: clamp(num(sc.duration, 3), 1, 600),
        vo: String(sc.vo || ''), text: String(sc.text || ''), data: data,
        image: normalizeImage(sc.image), source: String(sc.source || '').trim()
      };
    });
  }
  // A beat's photo: "media/x.jpg" or {src, credit}; null when there is none.
  function normalizeImage(img) {
    if (typeof img === 'string') img = { src: img };
    if (!isObj(img) || typeof img.src !== 'string' || !img.src.trim()) return null;
    return { src: img.src.trim(), credit: String(img.credit || '').trim() };
  }
  // Relative media paths ("media/x.jpg") resolve against options.mediaBase; absolute URLs pass through.
  function resolveMedia(src, base) {
    src = String(src || '').trim();
    if (!src) return '';
    if (/^(https?:|data:|blob:|\/)/i.test(src)) return src;
    if (/^[a-z][a-z0-9+.-]*:/i.test(src)) return '';   // no javascript:, file:, ...
    return (base || '') + src.replace(/^\.\//, '');
  }
  function totalDuration(scenes) {
    return r3(normalizeScenes(scenes).reduce(function (a, s) { return a + s.duration; }, 0));
  }
  function dimensions(aspect) { var d = ASPECTS[aspect] || ASPECTS['9:16']; return { width: d[0], height: d[1] }; }

  // The frame, top to bottom: progress line, logo, content (header row + visual), captions, then one line of
  // small print (source and photo credit) on the bottom edge of the safe area, the same place in every scene.
  function layout(design) {
    design = normalizeDesign(design);
    var W = ASPECTS[design.aspect][0], H = ASPECTS[design.aspect][1];
    var s = SAFE[design.aspect], landscape = W > H;
    var top = s.top, bottom = H - s.bottom, left = s.left, right = W - s.right;
    var ts = design.type.scale;
    var progress = null;
    if (design.progress.show) {
      progress = { top: top, height: 6, left: left, width: right - left };
      top += 6 + (landscape ? 36 : 52);
    }
    var meta = { top: bottom - 36, height: 36, left: left, width: right - left };
    bottom = meta.top - (landscape ? 20 : 28);
    var logo = null;
    if (design.logo.text.trim()) {
      var lp = design.logo.position, isTop = lp.indexOf('top') === 0, lh = 40, lg = landscape ? 28 : 44;
      logo = { top: isTop ? top : bottom - lh, height: lh, side: /left$/.test(lp) ? 'left' : 'right', left: left, right: W - right, isTop: isTop };
      if (isTop) top += lh + lg; else bottom -= lh + lg;
    }
    var cap = null, cs = design.captions.style;
    if (cs !== 'none') {
      var ch = Math.round((cs === 'pop' ? (landscape ? 170 : 240) : (landscape ? 150 : 210)) * clamp(ts, 0.85, 1.2) * Math.max(1, CAP_SIZE[design.captions.size]));
      var gap = landscape ? 36 : 56, pos = design.captions.position;
      if (pos === 'upper') { cap = { top: top, height: ch }; top += ch + gap; }
      else if (pos === 'middle') {
        var ct = Math.min(Math.round(H * (landscape ? 0.6 : 0.56)), bottom - ch);
        cap = { top: ct, height: ch }; bottom = ct - gap;
      } else { cap = { top: bottom - ch, height: ch }; bottom = cap.top - gap; }
      // captions are centred on the canvas, clear of the side buttons on either edge
      var side = Math.max(s.left, s.right);
      cap.left = side; cap.width = W - 2 * side;
    }
    return {
      width: W, height: H, landscape: landscape, safe: s,
      content: { left: left, top: top, width: right - left, height: bottom - top },
      captions: cap, logo: logo, meta: meta, progress: progress
    };
  }

  // ---------------------------------------------------------------- DOM helpers
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function q(scope, sel) { return scope.querySelector(sel); }
  function qa(scope, sel) { return Array.prototype.slice.call(scope.querySelectorAll(sel)); }

  // Tween helper: first tween on a target renders its from-state immediately (so seeks to earlier times are correct);
  // later tweens on the same props pass first=false.
  function tw(tl, target, from, to, at, first) {
    var t = Object.assign({}, to);
    if (first === false) t.immediateRender = false;
    tl.fromTo(target, from, t, Math.max(0, at));
    return tl;
  }
  function countUp(tl, node, p, at, dur, ease) {
    if (!node || !p) return;
    var from = p.year ? p.value : 0;
    var proxy = { v: from };
    node.textContent = formatValue(from, p);
    if (p.year) { node.textContent = formatValue(p.value, p); return; }
    // A modifier (not onUpdate) writes the text: modifiers run on every render, even when the
    // renderer seeks with suppressEvents=true, so the number is always correct for the seeked time.
    tl.fromTo(proxy, { v: from }, {
      v: p.value, duration: dur, ease: ease, immediateRender: false,
      modifiers: { v: function (v) { node.textContent = formatValue(parseFloat(v), p); return v; } }
    }, Math.max(0, at));
  }
  function revealWords(tl, scope, at, a, opts) {
    opts = opts || {};
    var ws = qa(scope, '.w');
    if (!ws.length) return at;
    var stagger = a.st(opts.stagger || 0.07);
    var maxSpan = opts.maxSpan || 1.2 * a.f;
    if (stagger * ws.length > maxSpan) stagger = maxSpan / ws.length;
    tw(tl, ws, { yPercent: opts.y || 100, opacity: 0 },
      { yPercent: 0, opacity: 1, duration: a.dur(opts.dur || 0.8), ease: a.E.out, stagger: stagger }, at);
    return at + stagger * ws.length;
  }

  // ---------------------------------------------------------------- scene builders
  // Each returns {head?, stack, anim(tl, a), post?()} ; a = per-scene animation context.
  // `head` (a chart's title) is pinned to the top of the content area, so it sits on the same line in every
  // scene. Charts, lists and timelines fill the space below it; single statements are centred in it.
  // Holds are still: motion lives in the entrances.
  var BUILD = {};

  function headingEl(text) {
    if (!plain(text)) return null;
    var h = el('h2', 'heading disp fit', wordsHTML(text));
    tagLang(h, text);
    return h;
  }
  function fadeUp(tl, a, target, at, dist) {
    tw(tl, target, { y: a.dist(dist || 24), opacity: 0 }, { y: 0, opacity: 1, duration: a.dur(0.7), ease: a.E.out }, at);
  }
  function revealHead(tl, a, head, at) {
    return head ? revealWords(tl, head, at, a, { stagger: 0.06 }) + a.st(0.08) : at;
  }
  function pairs(list, max, keys) {
    return (Array.isArray(list) ? list : []).slice(0, max).map(function (it) {
      if (typeof it === 'string') { var m = it.split(':'); it = {}; it[keys[0]] = m[0]; it[keys[1]] = m.slice(1).join(':'); }
      var o = {}; o[keys[0]] = String(it[keys[0]] == null ? '' : it[keys[0]]).trim(); o[keys[1]] = String(it[keys[1]] == null ? '' : it[keys[1]]).trim();
      return o;
    });
  }
  function drawLine(tl, a, line, at) {
    tw(tl, line, { scaleX: 0 }, { scaleX: 1, duration: a.dur(0.8), ease: a.E.inOut }, at);
  }

  BUILD.title = function (sc) {
    var d = sc.data, st = el('div', 'stack');
    var kick = null, sub = null;
    if (plain(d.kicker)) { kick = el('div', 'kicker', rich(d.kicker)); tagLang(kick, d.kicker); st.appendChild(kick); }
    var title = el('h1', 'title disp fit', wordsHTML(d.title || d.text || ''));
    tagLang(title, d.title); st.appendChild(title);
    var rule = el('div', 'rule'); st.appendChild(rule);
    if (plain(d.subtitle)) { sub = el('p', 'subtitle fit', rich(d.subtitle)); tagLang(sub, d.subtitle); st.appendChild(sub); }
    return {
      stack: st,
      anim: function (tl, a) {
        var at = a.t0;
        if (kick) { fadeUp(tl, a, kick, at, 16); at += a.st(0.2); }
        var end = revealWords(tl, title, at, a, { stagger: 0.08 });
        tw(tl, rule, { scaleX: 0 }, { scaleX: 1, duration: a.dur(0.7), ease: a.E.inOut }, end);
        if (sub) fadeUp(tl, a, sub, end + a.st(0.15));
      }
    };
  };

  BUILD.stat = function (sc) {
    var d = sc.data, st = el('div', 'stack');
    var label = null, ctx = null, line = null;
    if (plain(d.label)) { label = el('div', 'stat-label fit', rich(d.label)); tagLang(label, d.label); st.appendChild(label); }
    var p = parseValue(d.value);
    var val = el('div', 'value disp fit', valueHTML(d.value || '', p));
    tagLang(val, d.value); st.appendChild(val);
    if (plain(d.context)) {
      line = el('div', 'stat-line'); st.appendChild(line);
      ctx = el('div', 'context fit', rich(d.context)); tagLang(ctx, d.context); st.appendChild(ctx);
    }
    return {
      stack: st,
      anim: function (tl, a) {
        var at = a.t0;
        if (label) { fadeUp(tl, a, label, at, 18); at += a.st(0.15); }
        tw(tl, val, { yPercent: 8, opacity: 0 }, { yPercent: 0, opacity: 1, duration: a.dur(0.8), ease: a.E.out }, at);
        countUp(tl, q(val, '.num'), p, at, a.dur(1.3), a.E.num);
        if (line) drawLine(tl, a, line, at + a.st(0.35));
        if (ctx) fadeUp(tl, a, ctx, at + a.st(0.5), 16);
      }
    };
  };

  // Short labels draw columns that fill the frame (a series: years, steps); long labels or negative values
  // draw horizontal rows (a ranking). The largest value takes the accent.
  BUILD.bars = function (sc) {
    var d = sc.data, st = el('div', 'stack fill');
    var head = headingEl(d.title);
    var items = pairs(d.items, 8, ['label', 'value']).map(function (it) { it.p = parseValue(it.value); return it; });
    var mags = items.map(function (it) { return it.p ? Math.abs(it.p.magnitude) : 0; });
    var max = Math.max.apply(null, mags.concat([0])) || 1;
    var maxI = mags.indexOf(Math.max.apply(null, mags.concat([0])));
    var columns = items.length >= 2 && items.length <= 7 && items.every(function (it) { return plain(it.label).length <= 12 && !(it.p && it.p.negative); });
    var rows;
    if (columns) {
      var chart = el('div', 'colchart');
      chart.style.setProperty('--n', String(items.length));
      rows = items.map(function (it, i) {
        var col = el('div', 'cc' + (i === maxI ? ' max' : ''));
        var area = el('div', 'cc-area'), zone = el('div', 'cc-zone');
        var h = Math.max(1.5, mags[i] / max * 100);
        var bar = el('div', 'cc-bar'); bar.style.height = h.toFixed(2) + '%';
        var v = el('div', 'cc-value', valueHTML(it.value, it.p)); tagLang(v, it.value);
        v.style.bottom = 'calc(' + h.toFixed(2) + '% + calc(var(--k) * 16px))';
        zone.appendChild(bar); zone.appendChild(v); area.appendChild(zone);
        var lab = el('div', 'cc-label', rich(it.label)); tagLang(lab, it.label);
        col.appendChild(area); col.appendChild(lab); chart.appendChild(col);
        return { bar: bar, value: v, label: lab, zone: zone, h: h, val: q(v, '.num'), p: it.p };
      });
      var base = el('div', 'cc-base'); chart.appendChild(base);
      st.appendChild(chart);
      return {
        head: head, stack: st,
        post: function () {
          var area = rows[0].zone.parentNode;
          base.style.top = (area.offsetTop + area.offsetHeight) + 'px';
          // one shared size for every value, small enough for the widest
          var over = 1;
          rows.forEach(function (r) { var room = r.zone.offsetWidth * 1.15; if (room > 0) over = Math.max(over, contentWidth(r.value) / room); });
          if (over > 1) chart.style.setProperty('--vk', (1 / over).toFixed(3));
        },
        anim: function (tl, a) {
          var at = revealHead(tl, a, head, a.t0);
          drawLine(tl, a, base, at);
          var gap = a.st(Math.min(0.18, 0.9 / rows.length)), bd = a.dur(1.0);
          rows.forEach(function (r, i) {
            var t = at + 0.1 + i * gap;
            tw(tl, r.label, { opacity: 0 }, { opacity: 1, duration: a.dur(0.4), ease: 'power2.out' }, t);
            tw(tl, r.bar, { scaleY: 0 }, { scaleY: 1, duration: bd, ease: a.E.bar }, t);
            tw(tl, r.value, { y: r.zone.offsetHeight * r.h / 100, opacity: 0 }, { y: 0, opacity: 1, duration: bd, ease: a.E.bar }, t);
            countUp(tl, r.val, r.p, t, bd, a.E.num);
          });
        }
      };
    }
    var bars = el('div', 'bars');
    rows = items.map(function (it, i) {
      var row = el('div', 'bar-row' + (i === maxI ? ' max' : '') + (it.p && it.p.negative ? ' neg' : ''));
      var hd = el('div', 'bar-head');
      var lab = el('span', 'bar-label', rich(it.label)); tagLang(lab, it.label);
      var v = el('span', 'bar-value', valueHTML(it.value, it.p)); tagLang(v, it.value);
      hd.appendChild(lab); hd.appendChild(v);
      var track = el('div', 'bar-track');
      var fill = el('div', 'bar-fill');
      fill.style.width = Math.max(1.5, mags[i] / max * 100).toFixed(2) + '%';
      track.appendChild(fill);
      row.appendChild(hd); row.appendChild(track); bars.appendChild(row);
      return { head: hd, fill: fill, val: q(v, '.num'), p: it.p };
    });
    st.appendChild(bars);
    return {
      head: head, stack: st,
      anim: function (tl, a) {
        var at = revealHead(tl, a, head, a.t0);
        var gap = a.st(Math.min(0.2, 1.0 / Math.max(1, rows.length)));
        var bd = a.dur(1.0);
        rows.forEach(function (r, i) {
          var t = at + i * gap;
          tw(tl, r.head, { opacity: 0 }, { opacity: 1, duration: a.dur(0.5), ease: 'power2.out' }, t);
          tw(tl, r.fill, { scaleX: 0 }, { scaleX: 1, duration: bd, ease: a.E.bar }, t + 0.05);
          countUp(tl, r.val, r.p, t + 0.05, bd, a.E.num);
        });
      }
    };
  };

  // Two values side by side. The second item is the subject (the "after", the "new", the thing the
  // story is about), so it takes the accent whichever is larger. A dashed line carries the first value
  // across, so the gap between them is something you can see.
  BUILD.compare = function (sc) {
    var d = sc.data, st = el('div', 'stack fill');
    var head = headingEl(d.title);
    var items = pairs(d.items, 2, ['label', 'value']).map(function (it) { it.p = parseValue(it.value); return it; });
    while (items.length < 2) items.push({ label: '', value: '', p: null });
    var numeric = !!(items[0].p && items[1].p);
    var cols = el('div', 'cols' + (numeric ? '' : ' cols-text'));
    var parts, ref = null, base = null;
    if (numeric) {
      var mA = Math.abs(items[0].p.magnitude), mB = Math.abs(items[1].p.magnitude), mx = Math.max(mA, mB) || 1;
      var heights = [Math.max(3, mA / mx * 100), Math.max(3, mB / mx * 100)];
      var delta = null;
      if (mA > 0 && mB > 0 && mA !== mB) {
        var ratio = mB / mA;
        if (ratio >= 2) delta = (Math.round(ratio * 10) / 10) + '×';
        else if (ratio > 1) delta = '+' + Math.round((ratio - 1) * 100) + '%';
        else delta = '−' + Math.round((1 - ratio) * 100) + '%';
      }
      parts = items.map(function (it, i) {
        var col = el('div', 'col' + (i === 1 ? ' subject' : ''));
        var area = el('div', 'col-bar-area');
        var zone = el('div', 'col-zone');   // leaves room above the tallest bar for its value
        var barEl = el('div', 'col-bar'); barEl.style.height = heights[i].toFixed(2) + '%';
        var top = el('div', 'col-top');
        top.style.bottom = 'calc(' + heights[i].toFixed(2) + '% + calc(var(--k) * 18px))';
        var badge = null;
        if (delta && i === 1) { badge = el('div', 'delta', esc(delta)); top.appendChild(badge); }
        var v = el('div', 'col-value fit', valueHTML(it.value, it.p)); tagLang(v, it.value);
        top.appendChild(v);
        zone.appendChild(barEl); zone.appendChild(top); area.appendChild(zone);
        var lab = el('div', 'col-label', rich(it.label)); tagLang(lab, it.label);
        col.appendChild(area); col.appendChild(lab); cols.appendChild(col);
        return { bar: barEl, top: top, val: q(v, '.num'), p: it.p, label: lab, badge: badge, zone: zone, area: area, h: heights[i] };
      });
      if (delta) { ref = el('div', 'ref-line'); cols.appendChild(ref); }
      base = el('div', 'cc-base'); cols.appendChild(base);
    } else {
      // words, not numbers: two labelled panels
      parts = items.map(function (it, i) {
        var col = el('div', 'col panel' + (i === 1 ? ' subject' : ''));
        var lab = el('div', 'col-label', rich(it.label)); tagLang(lab, it.label);
        var v = el('div', 'panel-value fit', rich(it.value)); tagLang(v, it.value);
        col.appendChild(lab); col.appendChild(v); cols.appendChild(col);
        return { col: col };
      });
      st.className = 'stack';   // panels are centred like any other statement
    }
    st.appendChild(cols);
    return {
      head: head, stack: st,
      post: function () {
        if (!numeric) return;
        base.style.top = (parts[0].area.offsetTop + parts[0].area.offsetHeight) + 'px';
        if (!ref) return;
        var z = parts[0].zone, ar = parts[0].area;
        ref.style.top = (ar.offsetTop + z.offsetTop + z.offsetHeight * (1 - parts[0].h / 100)).toFixed(1) + 'px';
      },
      anim: function (tl, a) {
        var at = revealHead(tl, a, head, a.t0);
        var bd = a.dur(1.1);
        if (base) drawLine(tl, a, base, at);
        parts.forEach(function (pt, i) {
          var t = at + 0.1 + i * a.st(0.4);
          if (!numeric) { fadeUp(tl, a, pt.col, t, 24); return; }
          var px = pt.zone.offsetHeight * pt.h / 100;
          tw(tl, pt.label, { opacity: 0 }, { opacity: 1, duration: a.dur(0.5), ease: 'power2.out' }, t);
          tw(tl, pt.bar, { scaleY: 0 }, { scaleY: 1, duration: bd, ease: a.E.bar }, t);
          tw(tl, pt.top, { y: px, opacity: 0 }, { y: 0, opacity: 1, duration: bd, ease: a.E.bar }, t);
          countUp(tl, pt.val, pt.p, t, bd, a.E.num);
          if (pt.badge) tw(tl, pt.badge, { opacity: 0, y: a.dist(10) }, { opacity: 1, y: 0, duration: a.dur(0.5), ease: a.E.out }, t + bd * 0.85);
        });
        if (ref) tw(tl, ref, { scaleX: 0 }, { scaleX: 1, duration: a.dur(0.7), ease: a.E.inOut }, at + 0.1 + a.st(0.4) + bd * 0.7);
      }
    };
  };

  BUILD.list = function (sc) {
    var d = sc.data, st = el('div', 'stack fill');
    var head = headingEl(d.title);
    var ol = el('ol', 'items');
    var items = (Array.isArray(d.items) ? d.items : []).slice(0, 6).map(function (txt, i) {
      txt = typeof txt === 'string' ? txt : (txt && (txt.label || txt.text)) || '';
      var li = el('li', 'item');
      var line = el('span', 'item-line');
      var idx = el('span', 'idx tnum', String(i + 1));
      var t = el('span', 'item-text fit', rich(txt)); tagLang(t, txt);
      li.appendChild(line); li.appendChild(idx); li.appendChild(t); ol.appendChild(li);
      return { line: line, idx: idx, text: t };
    });
    ol.style.setProperty('--n', String(Math.max(1, items.length)));
    var end = el('span', 'item-line end'); ol.appendChild(end);
    st.appendChild(ol);
    return {
      head: head, stack: st,
      anim: function (tl, a) {
        var at = revealHead(tl, a, head, a.t0);
        var n = Math.max(1, items.length);
        var gap = clamp(Math.max(0.3, (a.e - at) * 0.55) / n, 0.18 * a.f, 1.2);
        items.forEach(function (it, i) {
          var t = at + i * gap;
          drawLine(tl, a, it.line, t);
          tw(tl, it.idx, { opacity: 0, y: a.dist(16) }, { opacity: 1, y: 0, duration: a.dur(0.5), ease: a.E.out }, t + 0.05);
          tw(tl, it.text, { x: -a.dist(24), opacity: 0 }, { x: 0, opacity: 1, duration: a.dur(0.6), ease: a.E.out }, t + 0.1);
        });
        drawLine(tl, a, end, at + (n - 1) * gap + 0.2);
      }
    };
  };

  BUILD.quote = function (sc) {
    var d = sc.data, st = el('div', 'stack');
    var wrap = el('div', 'quote');
    var bar = el('span', 'quote-bar'); wrap.appendChild(bar);
    var qt = el('blockquote', 'quote-text fit', wordsHTML('“' + plain(d.quote || d.text || '') + '”', { mask: false }));
    tagLang(qt, d.quote); wrap.appendChild(qt); st.appendChild(wrap);
    var src = null;
    if (plain(d.source)) { src = el('div', 'source', rich(d.source)); tagLang(src, d.source); st.appendChild(src); }
    return {
      stack: st,
      anim: function (tl, a) {
        var at = a.t0;
        tw(tl, bar, { scaleY: 0 }, { scaleY: 1, duration: a.dur(0.7), ease: a.E.inOut }, at);
        var ws = qa(qt, '.w');
        var span = Math.min((a.e - at) * 0.45, ws.length * 0.1 * a.f + 0.2);
        tw(tl, ws, { opacity: 0.12 }, { opacity: 1, duration: a.dur(0.4), ease: 'power1.out', stagger: span / Math.max(1, ws.length) }, at + a.st(0.15));
        if (src) fadeUp(tl, a, src, at + a.st(0.15) + span, 14);
      }
    };
  };

  BUILD.timeline = function (sc) {
    var d = sc.data, st = el('div', 'stack fill');
    var head = headingEl(d.title);
    var wrap = el('div', 'tl');
    var line = el('div', 'tl-line', '<i></i>'); wrap.appendChild(line);
    var items = pairs(d.items, 6, ['date', 'label']).map(function (it) {
      var node = el('div', 'tl-item');
      var dot = el('div', 'tl-dot');
      var date = el('div', 'tl-date', rich(it.date)); tagLang(date, it.date);
      var lab = el('div', 'tl-label fit', rich(it.label)); tagLang(lab, it.label);
      var txt = el('div', 'tl-text'); txt.appendChild(date); txt.appendChild(lab);
      node.appendChild(dot); node.appendChild(txt); wrap.appendChild(node);
      return { node: node, dot: dot, date: date, label: lab };
    });
    wrap.style.setProperty('--n', String(Math.max(1, items.length)));
    st.appendChild(wrap);
    var stops = [];
    return {
      head: head, stack: st,
      post: function (landscape) {
        // fit the line exactly between first and last dot centres
        if (!items.length) return;
        var centers = items.map(function (it) {
          return landscape ? it.node.offsetLeft + it.dot.offsetLeft + it.dot.offsetWidth / 2 : it.node.offsetTop + it.dot.offsetTop + it.dot.offsetHeight / 2;
        });
        var a0 = centers[0], a1 = centers[centers.length - 1], len = Math.max(1, a1 - a0);
        if (landscape) { line.style.left = a0 + 'px'; line.style.right = 'auto'; line.style.width = len + 'px'; }
        else { line.style.top = a0 + 'px'; line.style.bottom = 'auto'; line.style.height = len + 'px'; }
        stops = centers.map(function (c) { return (c - a0) / len; });
      },
      anim: function (tl, a) {
        var at = revealHead(tl, a, head, a.t0);
        var n = Math.max(1, items.length);
        var gap = clamp(Math.max(0.3, (a.e - at) * 0.55) / n, 0.2 * a.f, 1.2);
        var fill = q(line, 'i'), prop = a.landscape ? 'scaleX' : 'scaleY';
        tw(tl, line, { opacity: 0 }, { opacity: 1, duration: a.dur(0.4), ease: 'power1.out' }, at);
        var prev = 0;
        items.forEach(function (it, i) {
          var t = at + i * gap;
          var to = stops[i] || 0;
          if (i > 0) { var f0 = {}, f1 = { duration: gap * 0.9, ease: a.E.inOut }; f0[prop] = prev; f1[prop] = to; tw(tl, fill, f0, f1, t - gap * 0.9, i === 1 ? undefined : false); }
          else { var z = {}; z[prop] = 0; gsap.set(fill, z); }
          prev = to;
          tw(tl, it.dot, { scale: 0 }, { scale: 1, duration: a.dur(0.4), ease: a.E.out }, t);
          fadeUp(tl, a, it.date, t + 0.05, 16);
          fadeUp(tl, a, it.label, t + 0.12, 16);
        });
      }
    };
  };

  BUILD.text = function (sc) {
    var d = sc.data, st = el('div', 'stack');
    var txt = d.text || d.title || sc.text || '';
    var hasStar = /\*/.test(txt);
    var p = el('p', 'punch disp fit', wordsHTML(txt, { autoEm: hasStar ? null : function (w) { return /[0-9०-९₹$%]/.test(w); } }));
    tagLang(p, txt); st.appendChild(p);
    if (plain(txt).length <= 14) p.classList.add('short');   // a figure or a few words: set it like a poster
    return {
      stack: st,
      anim: function (tl, a) {
        var ws = qa(p, '.w');
        var span = Math.min((a.e - a.t0) * 0.45, ws.length * 0.12 * a.f + 0.1);
        var stg = span / Math.max(1, ws.length);
        revealWords(tl, p, a.t0, a, { stagger: stg / Math.max(0.01, a.M.st), maxSpan: span + 0.01, dur: 0.7 });
      }
    };
  };

  // With a photo, the image scene is the photo itself, full-bleed (the backdrop layer draws it).
  // Without one, it is an editor placeholder that says what to find.
  BUILD.image = function (sc, ctx) {
    var d = sc.data, st = el('div', 'stack fill');
    if (ctx.photo) {
      st.className = 'stack photo-only';
      return { stack: st, anim: function () {} };
    }
    var card = el('div', 'img-card');
    var inner = el('div', 'ph');
    inner.innerHTML = '<div class="ph-tag">Image needed</div>';
    var desc = el('div', 'ph-desc fit', rich(d.description || ''));
    tagLang(desc, d.description);
    inner.appendChild(desc); card.appendChild(inner);
    st.appendChild(card);
    return {
      stack: st,
      anim: function (tl, a) {
        tw(tl, card, { opacity: 0 }, { opacity: 1, duration: a.dur(0.6), ease: 'power2.out' }, a.t0);
        fadeUp(tl, a, inner, a.t0 + 0.15, 16);
      }
    };
  };

  // Full-bleed photo behind a scene: decoded before fitting, slow Ken Burns across the clip.
  function buildBackdrop(photo, sc, ctx) {
    var wrap = el('div', 'backdrop' + (sc.type === 'image' ? ' is-hero' : ''));
    var img = el('img');
    img.alt = plain(sc.data.description || sc.beat || '');
    img.decoding = 'sync';
    img.src = photo.url;
    wrap.appendChild(img);
    if (ctx.design.images.treatment === 'duotone') wrap.appendChild(el('div', 'tint'));
    wrap.appendChild(el('div', 'scrim'));
    var ok = true;
    ctx.waits.push(withTimeout(img.decode ? img.decode().catch(function () { ok = false; }) :
      new Promise(function (res) { img.onload = res; img.onerror = function () { ok = false; res(); }; }), 8000).then(function () {
      if (!ok || !img.naturalWidth) { wrap.style.display = 'none'; wrap.setAttribute('data-failed', '1'); }
    }));
    return {
      el: wrap, img: img,
      anim: function (tl, a) {
        if (wrap.style.display === 'none') return;
        // drift direction varies per scene but is fixed for a given script, so renders repeat exactly
        var dx = (a.rand() - 0.5) * 3, dy = (a.rand() - 0.5) * 2, zoomIn = a.rand() > 0.35;
        var s0 = zoomIn ? 1.02 : 1.08, s1 = zoomIn ? 1.08 : 1.02;
        tw(tl, img, { scale: s0, xPercent: -dx / 2, yPercent: -dy / 2 }, { scale: s1, xPercent: dx / 2, yPercent: dy / 2, duration: Math.max(0.1, a.clipEnd - a.clipStart), ease: 'none' }, a.clipStart);
      }
    };
  }

  // One line of small print on the bottom edge of the safe area: where a fact comes from, and who took the photo.
  function buildMeta(sc, photo, design, L) {
    var src = design.sources.show ? sc.source : '';
    var credit = photo && photo.credit ? photo.credit : '';
    if (!src && !credit) return null;
    var row = el('div', 'meta-row');
    row.style.cssText = 'left:' + L.meta.left + 'px;top:' + L.meta.top + 'px;width:' + L.meta.width + 'px;height:' + L.meta.height + 'px';
    if (src) { var t = el('div', 'src-tag', '<span class="src-k">Source</span><span class="src-v">' + rich(src) + '</span>'); tagLang(t, src); row.appendChild(t); }
    else row.appendChild(el('span'));
    if (credit) { var c = el('div', 'credit', rich(credit)); tagLang(c, credit); row.appendChild(c); }
    return row;
  }

  BUILD.end = function (sc, ctx) {
    var d = sc.data, st = el('div', 'stack');
    var logoText = ctx.design.logo.text.trim();
    var lg = null;
    if (logoText) { lg = el('div', 'end-logo', '<span class="logo-mark"></span><span>' + rich(logoText) + '</span>'); tagLang(lg, logoText); st.appendChild(lg); }
    var title = el('h1', 'end-title disp fit', wordsHTML(d.title || ''));
    tagLang(title, d.title); st.appendChild(title);
    var cta = null;
    if (plain(d.cta)) {
      cta = el('div', 'cta fit', '<span>' + rich(d.cta) + '</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>');
      tagLang(cta, d.cta);
      st.appendChild(cta);
    }
    return {
      stack: st,
      anim: function (tl, a) {
        var at = a.t0;
        if (lg) { fadeUp(tl, a, lg, at, 14); at += a.st(0.2); }
        var end = revealWords(tl, title, at, a, { stagger: 0.07 });
        if (cta) fadeUp(tl, a, cta, end + 0.05, 20);
      }
    };
  };

  // ---------------------------------------------------------------- fitting
  function fitWidths(scope) {
    qa(scope, '.fit').forEach(function (n) {
      var kw = 1;
      n.style.setProperty('--kw', '1');
      // elements that grow during their hold (data-fitm < 1) are fitted narrower so they never leave the safe box
      var m = parseFloat(n.getAttribute('data-fitm')) || 1;
      var need = function () { return m < 1 ? contentWidth(n) : n.scrollWidth; };
      for (var j = 0; j < 30 && need() > n.clientWidth * m + 1 && n.clientWidth > 0; j++) {
        kw *= clamp(n.clientWidth * m / need(), 0.7, 0.97);
        n.style.setProperty('--kw', kw.toFixed(4));
      }
    });
  }
  // natural width of an element's content, in layout px (independent of any CSS transform on the way up)
  function contentWidth(n) {
    var r = document.createRange();
    r.selectNodeContents(n);
    var box = n.getBoundingClientRect();
    var ratio = box.width ? n.offsetWidth / box.width : 1;
    return r.getBoundingClientRect().width * ratio;
  }
  function fitScene(sceneEl) {
    var body = q(sceneEl, '.body'), st = q(sceneEl, '.stack');
    if (!body || !st) return;
    var k = 1;
    for (var i = 0; i < 20; i++) {
      sceneEl.style.setProperty('--k', k.toFixed(4));
      fitWidths(sceneEl);
      var need = st.scrollHeight, have = body.clientHeight;
      if (need <= have + 16 || k < 0.35) break;
      k *= clamp(Math.sqrt(have / need), 0.8, 0.97);
    }
    fitWidths(sceneEl);
  }
  function fitCaption(capEl, w, h) {
    var inner = capEl.firstChild, kc = 1;
    for (var i = 0; i < 20; i++) {
      inner.style.setProperty('--kc', kc.toFixed(4));
      if ((inner.scrollWidth <= w + 1) && inner.offsetHeight <= h + 1) break;
      kc *= 0.93;
      if (kc < 0.4) break;
    }
  }

  // ---------------------------------------------------------------- captions
  function splitCaptions(vo, per) {
    var clean = String(vo || '').replace(/\[\s*\d+(?:\s*[,\-\u2013]\s*\d+)*\s*\]/g, '').replace(/[*_`#>]/g, '').replace(/\s+/g, ' ').trim();
    if (!clean) return [];
    var words = clean.split(' ');
    var chunks = [], cur = [];
    var ends = function (w) { return /[.,!?;:\u0964\u2026\u2014]["'\u201D\u2019)]*$/.test(w); };
    words.forEach(function (w, i) {
      var prev = chunks[chunks.length - 1];
      // a clause's last word never opens the next caption: it joins the one before, if that has room
      if (!cur.length && ends(w) && prev && prev.length < per + 1 && !ends(words[prev[prev.length - 1]])) { prev.push(i); return; }
      cur.push(i);
      // break at clause ends; otherwise at the word limit, but not just before a clause's final word
      if (ends(w) && cur.length >= Math.min(2, per)) { chunks.push(cur); cur = []; return; }
      if (cur.length >= per && !(words[i + 1] && ends(words[i + 1]) && cur.length < per + 1 && per > 1)) { chunks.push(cur); cur = []; }
    });
    if (cur.length) {
      var prev = chunks[chunks.length - 1];
      if (cur.length === 1 && prev && per >= 3 && prev.length + 1 <= per + 1) prev.push(cur[0]);
      else chunks.push(cur);
    }
    return { words: words, chunks: chunks };
  }

  // Captions read as captions, not as part of the graphic: centred, heavy, and in `highlight` style a pill
  // slides behind the word being spoken.
  function buildCaptions(stage, scenes, timing, design, L, colors, tl, E, enabled) {
    var style = design.captions.style;
    if (!enabled || style === 'none' || !L.captions) return;
    var layer = el('div', 'captions cap-' + style);
    stage.appendChild(layer);
    var per = style === 'pop' ? Math.min(design.captions.max_words, 2) : design.captions.max_words;
    var hl = colors.highlight;
    var made = [];
    scenes.forEach(function (sc, si) {
      var sp = splitCaptions(sc.vo, per);
      if (!sp.words || !sp.words.length) return;
      var s = timing[si].start, e = timing[si].start + timing[si].duration;
      var ws = s + Math.min(0.1, sc.duration * 0.05), we = e - Math.min(0.15, sc.duration * 0.06);
      var weights = sp.words.map(function (w, i) {
        var letters = w.replace(/[^\p{L}\p{N}]/gu, '').length;
        var pause = i === sp.words.length - 1 ? 0 : /[.!?।]["'”’)]*$/.test(w) ? 1.3 : /[,;:—]["'”’)]*$/.test(w) ? 0.7 : 0;
        return 1 + 0.09 * letters + pause;
      });
      var tot = weights.reduce(function (a, b) { return a + b; }, 0);
      var acc = 0;
      var times = weights.map(function (w) { var t0 = ws + (we - ws) * acc / tot; acc += w; return [t0, ws + (we - ws) * acc / tot]; });
      sp.chunks.forEach(function (ch, ci) {
        var start = times[ch[0]][0];
        var end = ci < sp.chunks.length - 1 ? times[sp.chunks[ci + 1][0]][0] : e;
        if (ci === 0) start = s;
        var cap = el('div', 'cap clip');
        cap.id = 'cap-' + si + '-' + ci;
        cap.setAttribute('data-start', r3(start));
        cap.setAttribute('data-duration', r3(end - start));
        cap.setAttribute('data-track-index', '2');
        var text = ch.map(function (i) { return sp.words[i]; }).join(' ');
        var inner = el('div', 'cap-inner');
        var wordsH = ch.map(function (i) { return '<span class="w">' + wrapDv(esc(sp.words[i])) + '</span>'; }).join(' ');
        inner.innerHTML = style === 'boxed' ? '<span class="line">' + wordsH + '</span>' : wordsH;
        var pill = null;
        if (style === 'highlight') { pill = el('span', 'cap-hl'); inner.insertBefore(pill, inner.firstChild); }
        tagLang(inner, text);
        cap.appendChild(inner);
        layer.appendChild(cap);
        made.push({ cap: cap, inner: inner, pill: pill, start: start, end: end, ch: ch, times: times, ci: ci });
      });
    });
    // measure
    made.forEach(function (m) { fitCaption(m.cap, L.captions.width, L.captions.height); });
    // animate
    made.forEach(function (m) {
      gsap.set(m.inner, { visibility: m.start <= 0 ? 'visible' : 'hidden' });
      if (m.start > 0) tl.set(m.inner, { visibility: 'visible' }, m.start);
      tl.set(m.inner, { visibility: 'hidden' }, m.end);
      if (style === 'pop') {
        tw(tl, m.inner, { scale: 0.9, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.2, ease: 'power3.out' }, m.start);
        qa(m.inner, '.w').forEach(function (w) { if (/[0-9०-९₹$%]/.test(w.textContent)) w.style.color = hl; });
      } else {
        tw(tl, m.inner, { opacity: 0 }, { opacity: 1, duration: 0.12, ease: 'power1.out' }, m.start);
      }
      var spans = qa(m.inner, '.w');
      if (style === 'karaoke') {
        spans.forEach(function (w, j) {
          var tt = m.times[m.ch[j]];
          gsap.set(w, { color: colors.capDim });
          // colour only: scaling the spoken word would eat the spaces beside it
          tl.set(w, { color: hl }, tt[0]);
          if (j < spans.length - 1) tl.set(w, { color: colors.text }, tt[1]);
        });
      }
      if (m.pill && spans.length) {
        var fs = parseFloat((root.getComputedStyle ? root.getComputedStyle(m.inner).fontSize : '') || '64') || 64;
        var px = fs * 0.12, py = fs * 0.02;
        var box = function (w) { return { x: w.offsetLeft - px, y: w.offsetTop - py, width: w.offsetWidth + 2 * px, height: w.offsetHeight + 2 * py }; };
        var boxes = spans.map(box);
        gsap.set(m.pill, boxes[0]);
        // a set (not a tween) per word keeps every frame consistent: no frame shows the pill between words
        // the pill jumps to each word as it is spoken, and that word flips to the pill's text colour in the same frame
        spans.forEach(function (w, j) {
          var at = m.times[m.ch[j]][0];
          if (j > 0) { tl.set(m.pill, boxes[j], at); tl.set(w, { color: colors.onHighlight }, at); }
          else gsap.set(w, { color: colors.onHighlight });
          if (j < spans.length - 1) tl.set(w, { color: colors.capText }, m.times[m.ch[j + 1]][0]);
        });
      }
    });
  }

  // ---------------------------------------------------------------- background
  // Grain is white (dark looks) or black (light looks) with noise in the alpha channel, so it needs no
  // blend mode: blend modes and masks on full-frame layers are among the slowest things to rasterize.
  function noiseURI(kind, dark) {
    var svg;
    if (kind === 'paper') {
      svg = "<svg xmlns='http://www.w3.org/2000/svg' width='420' height='420'><filter id='p'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' seed='4' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .35  0 0 0 0 .25  0 0 0 0 .12  0 0 0 .38 -.08'/></filter><filter id='m'><feTurbulence type='fractalNoise' baseFrequency='.008 .02' numOctaves='3' seed='9' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .45  0 0 0 0 .32  0 0 0 0 .15  0 0 0 .26 -.08'/></filter><rect width='100%' height='100%' filter='url(%23m)'/><rect width='100%' height='100%' filter='url(%23p)'/></svg>";
    } else {
      var c = dark ? 1 : 0;
      svg = "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' seed='7' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 " + c + "  0 0 0 0 " + c + "  0 0 0 0 " + c + "  1.6 0 0 0 -.62'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>";
    }
    return 'url("data:image/svg+xml;utf8,' + svg.replace(/"/g, "'").replace(/#/g, '%23').replace(/</g, '%3C').replace(/>/g, '%3E') + '")';
  }
  function buildBackground(stage, design, colors) {
    var bg = el('div', 'bg');
    bg.setAttribute('data-track-index', '0');
    var style = design.background.style, pat = design.background.pattern;
    // flat colour by default; `gradient` is a barely-there tonal step from the top, never a glow
    if (style === 'gradient') bg.appendChild(el('div', 'bg-tone'));
    var patEl = null;
    if (pat !== 'none') {
      patEl = el('div', 'bg-pattern bg-' + pat);
      var c = colors.pattern, cs;
      if (pat === 'grid') { cs = 'background-image:linear-gradient(' + c + ' 2px, transparent 2px),linear-gradient(90deg,' + c + ' 2px, transparent 2px);background-size:96px 96px'; }
      else if (pat === 'dots') { cs = 'background-image:radial-gradient(' + colors.patternDots + ' 3px, transparent 3.6px);background-size:48px 48px'; }
      else { cs = 'background-image:linear-gradient(' + c + ' 2px, transparent 2px);background-size:100% 72px'; }
      patEl.style.cssText = cs;
      bg.appendChild(patEl);
    }
    var noise = null;
    if (style === 'grain' || style === 'paper') {
      noise = el('div', 'bg-noise');
      noise.style.backgroundImage = noiseURI(style, colors.dark);
      noise.style.opacity = style === 'grain' ? (colors.dark ? '0.07' : '0.06') : '1';
      if (style === 'paper') noise.style.mixBlendMode = 'multiply';
      bg.appendChild(noise);
    }
    stage.appendChild(bg);
  }

  // ---------------------------------------------------------------- build
  var buildSeq = 0;
  function build(container, designIn, scenesIn, options) {
    options = Object.assign({ captions: true, safeArea: false }, options || {});
    if (!root.gsap) return Promise.reject(new Error('GSAP is not loaded'));
    var gsap = root.gsap;
    var design = normalizeDesign(designIn);
    var scenes = normalizeScenes(scenesIn);
    var L = layout(design);
    var W = L.width, H = L.height;
    var needDv = hasDv(JSON.stringify(scenes)) || hasDv(design.logo.text);
    var my = ++buildSeq;
    container = container || document.body;
    container.__vidSeq = my;

    var fontReady = scenes.length ? ensureFonts(design, needDv, JSON.stringify(scenes) + design.logo.text) : Promise.resolve({ useSystem: true });
    return fontReady.then(function (plan) {
      if (container.__vidSeq !== my) throw Object.assign(new Error('superseded'), { cancelled: true });
      // ---- colors & vars
      var C = design.colors;
      var dark = lum(C.background) < 0.3;
      var onAccent = contrast('#0B0B0C', C.accent) >= contrast('#FFFFFF', C.accent) ? '#0B0B0C' : '#FFFFFF';
      var hlKey = design.captions.highlight;
      var hlColor = isHex(hlKey) ? hlKey : (C[hlKey] || C.accent);
      var colors = {
        dark: dark, onAccent: onAccent, accent: C.accent, text: C.text,
        highlight: hlColor,
        onHighlight: contrast('#0B0B0C', hlColor) >= contrast('#FFFFFF', hlColor) ? '#0B0B0C' : '#FFFFFF',
        capDim: rgba(C.text, 0.5),
        capText: C.text,
        pattern: rgba(C.text, dark ? 0.035 : 0.045),
        patternDots: rgba(C.text, dark ? 0.08 : 0.1)
      };
      var fb = plan ? plan.fallback : null;
      var vars = {
        '--bg': C.background, '--surface': C.surface, '--text': C.text, '--muted': C.muted,
        '--accent': C.accent, '--accent2': C.accent2, '--negative': C.negative, '--on-accent': onAccent,
        '--radius': design.radius + 'px',
        '--font-display': plan.useSystem ? generic(design.fonts.display) : stack(design.fonts.display, design, fb),
        '--font-body': plan.useSystem ? generic(design.fonts.body) : stack(design.fonts.body, design, fb),
        '--font-mono': plan.useSystem ? generic(design.fonts.mono) : stack(design.fonts.mono, design, fb),
        '--display-weight': String(design.type.display_weight),
        '--display-case': design.type.display_case === 'upper' ? 'uppercase' : design.type.display_case === 'title' ? 'capitalize' : 'none',
        '--tracking': design.type.tracking + 'em',
        '--ts': String(design.type.scale),
        '--line': rgba(C.text, 0.14), '--line-strong': rgba(C.text, 0.32), '--track-strong': rgba(C.text, dark ? 0.16 : 0.13), '--track': rgba(C.text, dark ? 0.08 : 0.07), '--bar-dim': rgba(C.text, dark ? 0.3 : 0.24),
        '--shadow': dark ? 'rgba(0,0,0,.45)' : rgba(C.text, 0.16),
        '--tone': rgba(C.text, dark ? 0.05 : 0.04),
        '--cap-hl': hlColor, '--on-hl': colors.onHighlight,
        '--cap-shadow': dark ? '0 2px 12px rgba(0,0,0,.55)' : 'none',
        '--cap-box': dark ? 'rgba(0,0,0,.72)' : C.text,
        '--cap-box-text': dark ? C.text : C.background,
        '--cap-dim': rgba(C.text, 0.55),
        '--cap-k': String(CAP_SIZE[design.captions.size]),
        '--scrim': rgba(C.background, 0.62), '--scrim-hero': rgba(C.background, 0.2),
        '--photo-shadow': dark ? '0 2px 28px rgba(0,0,0,.55)' : 'none',
        '--cl': L.content.left + 'px', '--ct': L.content.top + 'px', '--cw': L.content.width + 'px', '--ch': L.content.height + 'px'
      };
      if (L.captions) {
        vars['--capl'] = L.captions.left + 'px'; vars['--capt'] = L.captions.top + 'px';
        vars['--capw'] = L.captions.width + 'px'; vars['--caph'] = L.captions.height + 'px';
      }

      // ---- stage
      var stage = options.stage || el('div');
      var reuse = !!options.stage;
      if (reuse) stage.innerHTML = '';
      stage.className = 'vid-stage ar-' + (L.landscape ? 'landscape' : 'portrait') + ' aspect-' + design.aspect.replace(':', 'x') +
        ' energy-' + design.motion.energy + ' tx-' + design.motion.transition + ' bg-' + design.background.style + (dark ? ' is-dark' : ' is-light') +
        ' img-' + design.images.treatment + ' cap-size-' + design.captions.size;
      stage.setAttribute('data-composition-id', COMPOSITION_ID);
      stage.setAttribute('data-start', '0');
      stage.setAttribute('data-width', String(W));
      stage.setAttribute('data-height', String(H));
      stage.setAttribute('data-fonts', plan.useSystem ? 'system' : 'loaded');
      stage.setAttribute('lang', needDv && !scenes.some(function (s) { return /[A-Za-z]{4,}/.test(plain(s.vo)); }) ? 'hi' : 'en');
      stage.style.cssText = 'width:' + W + 'px;height:' + H + 'px;';
      Object.keys(vars).forEach(function (k) { stage.style.setProperty(k, vars[k]); });
      if (!reuse) {
        stage.style.position = 'absolute'; stage.style.left = '0'; stage.style.top = '0';
        stage.style.visibility = 'hidden';
        container.appendChild(stage);
      }
      if (design.custom_css.trim()) { var cssEl = el('style'); cssEl.className = 'vid-custom-css'; cssEl.textContent = design.custom_css; stage.appendChild(cssEl); }

      // ---- timing
      var timing = [], acc = 0;
      scenes.forEach(function (sc) { timing.push({ start: r3(acc), duration: sc.duration, type: sc.type, beat: sc.beat }); acc += sc.duration; });
      var total = r3(acc);
      stage.setAttribute('data-duration', String(total));
      var M = MOTION[design.motion.energy], E = EASES[design.motion.easing];
      var trans = design.motion.transition;
      var minDur = scenes.reduce(function (m, s) { return Math.min(m, s.duration); }, 99);
      var o = trans === 'cut' ? 0 : Math.min(M.tx / 2, minDur / 4);   // half transition length
      var overlap = (trans === 'fade' || trans === 'slide' || trans === 'zoom') ? o : 0;
      var rand = mulberry32(1337 + scenes.length * 7);

      gsap.config({ force3D: false });   // 2D transforms only: identical rasterization whichever way a frame is reached
      var tl = gsap.timeline({ paused: true });

      buildBackground(stage, design, colors);

      // ---- scenes
      var waits = [];
      var built = scenes.map(function (sc, i) {
        var t = timing[i];
        var clipStart = Math.max(0, t.start - (i > 0 ? overlap : 0));
        var clipEnd = Math.min(total, t.start + t.duration + (i < scenes.length - 1 ? overlap : 0));
        var sEl = el('div', 'scene scene-' + sc.type + ' clip');
        sEl.id = 'scene-' + i;
        sEl.setAttribute('data-start', String(r3(clipStart)));
        sEl.setAttribute('data-duration', String(r3(clipEnd - clipStart)));
        sEl.setAttribute('data-track-index', '1');
        sEl.setAttribute('data-scene-index', String(i));
        sEl.setAttribute('data-type', sc.type);
        if (sc.beat) sEl.setAttribute('data-beat', sc.beat);
        var inner = el('div', 'scene-inner'), drift = el('div', 'scene-drift'), frame = el('div', 'frame');
        var chip = null;
        if (plain(sc.text)) { chip = el('div', 'chip fit', rich(sc.text)); tagLang(chip, sc.text); }
        var body = el('div', 'body');
        var pic = sc.type === 'image' ? (sc.data.url ? { src: sc.data.url, credit: sc.data.credit || (sc.image && sc.image.credit) || '' } : sc.image) : sc.image;
        var photo = pic ? { url: resolveMedia(pic.src, options.mediaBase), credit: pic.credit || '' } : null;
        if (photo && !photo.url) photo = null;
        var ctx = { design: design, waits: waits, photo: photo };
        var b = BUILD[sc.type](sc, ctx);
        // the overlay label and a chart's title share a header row pinned to the top of the content area
        if (chip || b.head) {
          var head = el('div', 'head');
          if (chip) head.appendChild(chip);
          if (b.head) head.appendChild(b.head);
          frame.appendChild(head);
        }
        body.appendChild(b.stack);
        frame.appendChild(body);
        var meta = buildMeta(sc, photo, design, L);
        var backdrop = photo ? buildBackdrop(photo, sc, ctx) : null;
        if (backdrop) { inner.appendChild(backdrop.el); sEl.classList.add('has-photo'); }
        drift.appendChild(frame); if (meta) drift.appendChild(meta); inner.appendChild(drift); sEl.appendChild(inner);
        stage.appendChild(sEl);
        return { sc: sc, el: sEl, inner: inner, drift: drift, chip: chip, b: b, backdrop: backdrop, meta: meta, clipStart: clipStart, clipEnd: clipEnd, t: t };
      });

      // ---- logo, wipe, guides
      var logoEl = null;
      if (L.logo) {
        logoEl = el('div', 'logo', '<span class="logo-mark"></span><span class="logo-text">' + rich(design.logo.text.trim()) + '</span>');
        tagLang(logoEl, design.logo.text);
        logoEl.style.top = L.logo.top + 'px';
        logoEl.style.height = L.logo.height + 'px';
        if (L.logo.side === 'left') logoEl.style.left = L.logo.left + 'px'; else { logoEl.style.right = L.logo.right + 'px'; logoEl.style.flexDirection = 'row-reverse'; }
        stage.appendChild(logoEl);
      }
      var progFills = [];
      if (L.progress && scenes.length > 1) {
        var prog = el('div', 'progress');
        prog.style.cssText = 'left:' + L.progress.left + 'px;top:' + L.progress.top + 'px;width:' + L.progress.width + 'px;height:' + L.progress.height + 'px';
        scenes.forEach(function () { var seg = el('span', 'seg', '<i></i>'); prog.appendChild(seg); progFills.push(q(seg, 'i')); });
        stage.appendChild(prog);
      }
      var wipe = null;
      if (trans === 'wipe' && scenes.length > 1 && o > 0) {
        var wl = el('div', 'wipe-layer');
        wl.style.cssText = 'position:absolute;inset:0;overflow:hidden;pointer-events:none';
        wipe = el('div', 'wipe', '<i></i>');
        wl.appendChild(wipe); stage.appendChild(wl);
      }

      return Promise.all(waits).then(function () {
        if (container.__vidSeq !== my) throw Object.assign(new Error('superseded'), { cancelled: true });
        built.forEach(function (x) {
          if (x.backdrop && x.backdrop.el.hasAttribute('data-failed')) {
            x.el.classList.remove('has-photo');
            if (x.sc.type === 'image') {
              var fallback = BUILD.image(x.sc, { design: design, waits: [] });
              x.b.stack.replaceWith(fallback.stack);
              x.b = fallback;
            }
          }
        });
        // ---- fit (fonts are loaded or frozen to system fallbacks)
        built.forEach(function (x) {
          fitScene(x.el);
          if (x.b.post) x.b.post(L.landscape);
        });

        // ---- scene animation
        built.forEach(function (x, i) {
          var s = x.t.start, d = x.t.duration, e = s + d;
          var enterDelay = i === 0 ? 0.15 : trans === 'cut' ? 0.05 : trans === 'wipe' ? o * 0.6 : o * 0.4;
          var a = {
            design: design, E: E, M: M, colors: colors, landscape: L.landscape, rand: rand,
            s: s, d: d, e: e, t0: s + enterDelay, clipStart: x.clipStart, clipEnd: x.clipEnd,
            f: clamp(d / 4.5, 0.45, 1)
          };
          a.dur = function (v) { return v * M.dur * Math.max(0.6, a.f); };
          a.st = function (v) { return v * M.st * a.f; };
          a.dist = function (v) { return v * M.dist; };

          // visibility window (on the inner wrapper, never on the clip element)
          gsap.set(x.inner, { visibility: x.clipStart <= 0 ? 'visible' : 'hidden' });
          if (x.clipStart > 0) tl.set(x.inner, { visibility: 'visible' }, x.clipStart);
          tl.set(x.inner, { visibility: 'hidden' }, x.clipEnd >= total ? total : x.clipEnd);

          // transitions
          var first = true;
          if (i > 0 && trans !== 'cut' && trans !== 'wipe') {
            var dur = 2 * o, at = x.clipStart;
            if (trans === 'fade') tw(tl, x.inner, { opacity: 0 }, { opacity: 1, duration: dur * 0.7, ease: 'power2.out' }, at + dur * 0.3);
            else if (trans === 'slide') tw(tl, x.inner, { xPercent: 8 * M.dist, opacity: 0 }, { xPercent: 0, opacity: 1, duration: dur * 0.65, ease: E.out }, at + dur * 0.35);
            else if (trans === 'zoom') tw(tl, x.inner, { scale: 0.97, opacity: 0 }, { scale: 1, opacity: 1, duration: dur * 0.65, ease: E.out }, at + dur * 0.35);
            first = false;
          }
          if (i < built.length - 1 && trans !== 'cut' && trans !== 'wipe') {
            var dur2 = 2 * o, at2 = e - o;
            if (trans === 'fade') tw(tl, x.inner, { opacity: 1 }, { opacity: 0, duration: dur2 * 0.55, ease: 'power2.in' }, at2, first ? undefined : false);
            else if (trans === 'slide') tw(tl, x.inner, { xPercent: 0, opacity: 1 }, { xPercent: -8 * M.dist, opacity: 0, duration: dur2 * 0.6, ease: 'power2.in' }, at2, first ? undefined : false);
            else if (trans === 'zoom') tw(tl, x.inner, { scale: 1, opacity: 1 }, { scale: 1.03, opacity: 0, duration: dur2 * 0.6, ease: 'power2.in' }, at2, first ? undefined : false);
          }
          // Holds stay still: text that drifts or grows moves off the grid it shares with the other scenes.

          // overlay label
          if (x.chip) tw(tl, x.chip, { x: -a.dist(16), opacity: 0 }, { x: 0, opacity: 1, duration: a.dur(0.6), ease: E.out }, a.t0);
          if (x.backdrop) x.backdrop.anim(tl, a);
          if (x.meta) tw(tl, x.meta, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }, a.t0 + Math.min(0.7, d * 0.2));
          x.b.anim(tl, a);
        });

        // the progress line fills one segment per beat, at the pace of the voiceover
        progFills.forEach(function (f, i) {
          tw(tl, f, { scaleX: 0 }, { scaleX: 1, duration: Math.max(0.1, timing[i].duration), ease: 'none' }, timing[i].start);
        });
        if (wipe) {
          gsap.set(wipe, { x: 0, xPercent: -125, skewX: -8 });
          for (var i = 1; i < built.length; i++) {
            var bnd = built[i].t.start;
            tw(tl, wipe, { xPercent: -125 }, { xPercent: 0, duration: o, ease: 'power3.in' }, bnd - o, i === 1 ? undefined : false);
            tw(tl, wipe, { xPercent: 0 }, { xPercent: 125, duration: o, ease: 'power3.out' }, bnd, false);
          }
        }
        if (logoEl && total > 0) {
          tw(tl, logoEl, { opacity: 0, y: -10 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' }, 0.1);
          // the end card shows the wordmark big, so the corner mark steps aside
          built.forEach(function (x, i) {
            if (x.sc.type !== 'end' || i === 0) return;
            tw(tl, logoEl, { opacity: 1 }, { opacity: 0, duration: 0.35, ease: 'power2.out' }, x.t.start, false);
            if (i < built.length - 1) tw(tl, logoEl, { opacity: 0 }, { opacity: 1, duration: 0.35, ease: 'power2.out' }, x.t.start + x.t.duration - 0.2, false);
          });
        }

        buildCaptions(stage, scenes, timing, design, L, colors, tl, E, options.captions !== false);

        if (options.safeArea) stage.appendChild(guides(L));

        // ---- swap in (flicker-free) and register
        var prev = container.__vidCurrent;
        if (!reuse) {
          qa(container, ':scope > .vid-stage').forEach(function (n) { if (n !== stage) n.parentNode.removeChild(n); });
          stage.style.visibility = '';
          stage.id = 'stage';
        }
        if (prev && prev.timeline && prev.timeline !== tl) prev.timeline.kill();
        tl.time(0, false);
        root.__timelines = root.__timelines || {};
        root.__timelines[COMPOSITION_ID] = tl;
        if (typeof root.__hfForceTimelineRebind === 'function') { try { root.__hfForceTimelineRebind(); } catch (err) { /* ignore */ } }
        var result = { timeline: tl, duration: total, stage: stage, scenes: timing, layout: L, design: design };
        container.__vidCurrent = result;
        return result;
      });
    }).catch(function (err) {
      if (err && err.cancelled) {
        // remove orphan stage of a superseded build
        qa(container, ':scope > .vid-stage').forEach(function (n) { if (n.style.visibility === 'hidden' && n !== (container.__vidCurrent || {}).stage) n.parentNode.removeChild(n); });
      }
      throw err;
    });
  }

  function guides(L) {
    var g = el('div', 'safe-guides');
    var W = L.width, H = L.height, s = L.safe;
    function box(cls, x, y, w, h, label) {
      var b = el('div', cls);
      b.style.cssText = 'left:' + x + 'px;top:' + y + 'px;width:' + w + 'px;height:' + h + 'px';
      if (label) b.appendChild(el('span', 'lbl', esc(label)));
      g.appendChild(b);
    }
    box('unsafe', 0, 0, W, s.top);
    box('unsafe', 0, H - s.bottom, W, s.bottom);
    box('unsafe', 0, s.top, s.left, H - s.top - s.bottom);
    box('unsafe', W - s.right, s.top, s.right, H - s.top - s.bottom);
    box('box', L.content.left, L.content.top, L.content.width, L.content.height, 'content');
    if (L.captions) box('box cap', L.captions.left, L.captions.top, L.captions.width, L.captions.height, 'captions');
    return g;
  }

  root.VidScenes = {
    version: VERSION,
    compositionId: COMPOSITION_ID,
    build: build,
    normalizeDesign: normalizeDesign,
    normalizeScenes: normalizeScenes,
    fontsFor: fontsFor,
    layout: layout,
    dimensions: dimensions,
    totalDuration: totalDuration,
    parseValue: parseValue,
    resolveMedia: resolveMedia,
    formatValue: formatValue,
    FONTS: FONT_TABLE,
    DEFAULT_DESIGN: clone(DEFAULT_DESIGN),
    TYPES: TYPES.slice()
  };
})(typeof window !== 'undefined' ? window : this);
