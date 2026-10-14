// Dependency-free regressions: node --test tests/test_engine.js
// The DOM/timeline doubles exercise loading and state contracts; they do not
// measure browser typography or render pixels.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const assets = path.join(__dirname, '../skills/vid-studio/assets/scenes');
const engineSource = fs.readFileSync(path.join(assets, 'engine.js'), 'utf8');
const playerSource = fs.readFileSync(path.join(assets, 'player.html'), 'utf8')
  .match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const flush = () => new Promise(resolve => setImmediate(resolve));
const json = value => JSON.parse(JSON.stringify(value));

class Element {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.children = [];
    this.attributes = {};
    this.style = { setProperty(k, v) { this[k] = v; }, getPropertyValue(k) { return this[k] || ''; } };
    this.className = '';
    this.classList = { add: name => { this.className += ' ' + name; }, toggle() {} };
    this.offsetWidth = this.clientWidth = 1080;
    this.offsetHeight = this.clientHeight = 1920;
    this.scrollWidth = this.scrollHeight = 0;
    this.textContent = '';
  }
  set innerHTML(value) { this.html = value; this.children = []; }
  get innerHTML() { return this.html || ''; }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k] || null; }
  appendChild(node) { this.children.push(node); node.parentNode = this; return node; }
  removeChild(node) { this.children.splice(this.children.indexOf(node), 1); node.parentNode = null; }
  querySelectorAll(selector) {
    if (selector === ':scope > .vid-stage') return this.children.filter(n => n.className.split(/\s+/).includes('vid-stage'));
    const found = [];
    const walk = node => node.children.forEach(child => {
      if (selector.startsWith('.') && child.className.split(/\s+/).includes(selector.slice(1))) found.push(child);
      walk(child);
    });
    walk(this);
    return found;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
}

function engineHarness(fonts) {
  const timers = new Map();
  let nextTimer = 0;
  const document = { head: new Element('head'), body: new Element('body'), fonts,
    createElement: tag => new Element(tag) };
  const timelines = [];
  const gsap = {
    config() {}, set() {}, timeline() {
      const tl = { tweens: [], killed: false, fromTo(target, from, to, at) { this.tweens.push({ to, at }); return this; },
        set(target, props, at) { this.tweens.push({ to: { duration: 0 }, at }); return this; },
        time() { return this; }, kill() { this.killed = true; } };
      timelines.push(tl);
      return tl;
    }
  };
  const context = vm.createContext({ document, gsap,
    setTimeout(fn, ms) { const id = ++nextTimer; timers.set(id, { fn, ms }); return id; },
    clearTimeout(id) { timers.delete(id); } });
  context.window = context;
  vm.runInContext(engineSource, context);
  return { api: context.VidScenes, document, timers, timelines,
    expire() { for (const timer of [...timers.values()]) if (timer.ms === 5000) timer.fn(); } };
}

test('malformed design groups default safely without mutating the input', () => {
  const { api } = engineHarness();
  const defaults = json(api.DEFAULT_DESIGN);
  for (const group of ['colors', 'fonts', 'type', 'motion', 'captions', 'background', 'images', 'sources', 'progress', 'logo']) {
    for (const bad of ['bad', false, 4, [], null]) {
      const input = { [group]: bad };
      assert.deepEqual(json(api.normalizeDesign(input))[group], defaults[group], `${group}: ${JSON.stringify(bad)}`);
      assert.deepEqual(input, { [group]: bad });
      assert.doesNotThrow(() => api.fontsFor(input));
      assert.doesNotThrow(() => api.layout(input));
    }
  }
  assert.equal(api.normalizeDesign({ colors: { accent: '#abc' }, type: { scale: 99 } }).type.scale, 1.6);
  assert.equal(api.normalizeDesign({ colors: { accent: '#abc' } }).colors.accent, '#abc');
});

test('photo, source, and caption-size settings normalize to safe values', () => {
  const { api } = engineHarness();
  const d = api.normalizeDesign({ images: { treatment: 'sepia' }, sources: { show: 0 }, captions: { size: 'huge' } });
  assert.deepEqual([d.images.treatment, d.sources.show, d.captions.size], ['dim', true, 'medium']);
  assert.equal(api.normalizeDesign({ sources: { show: false } }).sources.show, false);
  assert.equal(api.normalizeDesign({ progress: { show: false } }).progress.show, false);
  assert.equal(api.normalizeDesign({}).captions.style, 'highlight');
  assert.equal(api.normalizeDesign({ captions: { style: 'shimmer' } }).captions.style, 'plain');
  // small print and captions are reserved at the bottom of the safe area, below the content
  const L = api.layout({});
  assert.equal(L.meta.top + L.meta.height, 1920 - 28);
  assert.ok(L.captions.top + L.captions.height <= L.meta.top);
  assert.ok(L.content.top + L.content.height <= L.captions.top);
  assert.equal(L.captions.left + L.captions.width, 1080 - L.captions.left, 'captions are centred on the canvas');
  assert.equal(api.layout({ progress: { show: false } }).progress, null);
  const [a, b, c] = json(api.normalizeScenes([
    { type: 'stat', data: {}, image: 'media/x.jpg', source: ' RBI ' },
    { type: 'text', data: {}, image: { src: 'https://e.com/y.png', credit: 'Photo: Y' } },
    { type: 'image', data: { description: 'd', src: 'media/z.jpg' }, image: { src: '' } }]));
  assert.deepEqual([a.image, a.source], [{ src: 'media/x.jpg', credit: '' }, 'RBI']);
  assert.deepEqual([b.image, b.source], [{ src: 'https://e.com/y.png', credit: 'Photo: Y' }, '']);
  assert.deepEqual([c.image, c.data.url], [null, 'media/z.jpg']);
  const base = '/api/p/one/scripts/s/';
  assert.equal(api.resolveMedia('media/x.jpg', base), base + 'media/x.jpg');
  assert.equal(api.resolveMedia('./media/x.jpg', base), base + 'media/x.jpg');
  assert.equal(api.resolveMedia('https://e.com/y.png', base), 'https://e.com/y.png');
  for (const bad of ['javascript:alert(1)', 'file:///etc/passwd', 'JaVaScRiPt:x', '']) assert.equal(api.resolveMedia(bad, base), '');
});

test('photo placement, underline captions and message scenes normalize to safe values', () => {
  const { api } = engineHarness();
  const d = api.normalizeDesign({});
  assert.equal(d.images.layout, 'auto');
  assert.equal(api.normalizeDesign({ images: { layout: 'collage' } }).images.layout, 'auto');
  assert.equal(api.normalizeDesign({ images: { layout: 'full' } }).images.layout, 'full');
  assert.equal(api.normalizeDesign({ captions: { style: 'underline' } }).captions.style, 'underline');
  assert.equal(api.normalizeDesign({ background: { style: 'ambient' } }).background.style, 'solid', 'no ambient light: flat colour only');
  assert.ok(api.TYPES.includes('message'));
  const [m, top, full, odd] = json(api.normalizeScenes([
    { type: 'message', data: { title: 'Unknown number', items: ['Sir, refund ready', 'you: Which refund?'] } },
    { type: 'stat', data: {}, image: { src: 'media/a.jpg', credit: 'Photo: A', layout: 'top' } },
    { type: 'bars', data: {}, image: { src: 'media/b.jpg', layout: 'full' } },
    { type: 'text', data: {}, image: { src: 'media/c.jpg', layout: 'card' } }]));
  assert.equal(m.type, 'message');
  assert.deepEqual(m.data.items, ['Sir, refund ready', 'you: Which refund?']);
  assert.deepEqual(top.image, { src: 'media/a.jpg', credit: 'Photo: A', layout: 'top' });
  assert.equal(full.image.layout, 'full');
  assert.deepEqual(odd.image, { src: 'media/c.jpg', credit: '' }, 'an unknown placement is dropped, so the look decides');
  // cards: glass by default, flat or solid on request, anything else falls back to glass
  assert.equal(api.normalizeDesign({}).cards.style, 'glass');
  assert.equal(api.normalizeDesign({ cards: { style: 'flat' } }).cards.style, 'flat');
  assert.equal(api.normalizeDesign({ cards: { style: 'chrome' } }).cards.style, 'glass');
  assert.equal(api.normalizeDesign({ cards: 'glass' }).cards.style, 'glass');
  // the progress line leaves room for the folio at its end
  const L = api.layout({});
  assert.ok(L.progress.left + L.progress.width < L.content.left + L.content.width - 100);
  assert.ok(api.FONTS['Inter Tight'], 'the Swiss look\'s font is in the font table');
});

test('empty compositions build static backgrounds with zero duration and replace the old timeline', async () => {
  const h = engineHarness();
  for (const style of ['solid', 'gradient', 'grain', 'paper']) {
    for (const pattern of ['none', 'grid', 'dots', 'lines']) {
      const prior = h.document.body.__vidCurrent;
      const result = await h.api.build(h.document.body, { background: { style, pattern } }, []);
      assert.equal(result.duration, 0);
      assert.deepEqual(json(result.scenes), []);
      assert.equal(result.stage.getAttribute('data-duration'), '0');
      assert.equal(result.timeline.tweens.length, 0);
      assert.equal(h.document.head.children.length, 0, 'blank scripts do not wait for fonts');
      assert.equal(h.document.body.children.length, 1);
      if (prior) assert.equal(prior.timeline.killed, true);
    }
  }
});

const titleScenes = [{ type: 'title', duration: 3, data: { title: 'Font metrics: Å Ω नमस्ते' } }];

test('font loading success waits for every face and includes the composition glyphs', async () => {
  const samples = [];
  const h = engineHarness({ load(spec, sample) { samples.push(sample); return Promise.resolve([{ status: 'loaded' }]); } });
  const build = h.api.build(h.document.body, {}, titleScenes);
  h.document.head.children[0].onload();
  const result = await build;
  assert.equal(result.stage.getAttribute('data-fonts'), 'loaded');
  assert.match(result.stage.style['--font-display'], /Bricolage Grotesque/);
  assert.ok(samples.length > 1);
  assert.ok(samples.every(sample => sample.includes(titleScenes[0].data.title)));
  assert.equal(h.timers.size, 0, 'loading clears the deadline');
});

for (const latePhase of ['stylesheet', 'font']) {
  test(`late ${latePhase} completion cannot change a fitted fallback stage`, async () => {
    let completeFonts;
    const fontPromise = new Promise(resolve => { completeFonts = resolve; });
    const h = engineHarness({ load() { return fontPromise; } });
    const build = h.api.build(h.document.body, {}, titleScenes);
    const link = h.document.head.children[0];
    if (latePhase === 'font') { link.onload(); await flush(); }
    h.expire();
    const result = await build;
    assert.equal(result.stage.getAttribute('data-fonts'), 'system');
    const frozen = ['--font-display', '--font-body', '--font-mono'].map(k => result.stage.style[k]);
    assert.deepEqual(frozen, ['sans-serif', 'sans-serif', 'monospace']);
    if (latePhase === 'stylesheet') link.onload();
    completeFonts([{ status: 'loaded' }]);
    await flush();
    assert.deepEqual(['--font-display', '--font-body', '--font-mono'].map(k => result.stage.style[k]), frozen);
    assert.equal(h.document.body.__vidCurrent, result);
    assert.equal(h.timers.size, 0);
  });
}

test('failed or unavailable font faces freeze to system fonts, and earlier sheets stay attached', async () => {
  const h = engineHarness({ load() { return Promise.resolve([]); } });
  const first = h.api.build(h.document.body, {}, titleScenes);
  h.document.head.children[0].onerror();
  assert.equal((await first).stage.getAttribute('data-fonts'), 'system');
  const second = h.api.build(h.document.body, { fonts: { display: 'Oswald' } }, titleScenes);
  h.document.head.children[1].onload();
  assert.equal((await second).stage.getAttribute('data-fonts'), 'system');
  assert.equal(h.document.head.children.length, 2);
});

function playerHarness({ standalone = false, search = '' } = {}) {
  const elements = Object.fromEntries(['scaler', 'viewport', 'msg', 'play', 'scrub', 'time', 'chips'].map(id => [id, new Element()]));
  const handlers = {}, messages = [], builds = [];
  const parent = { postMessage(message, origin) { messages.push({ message: json(message), origin }); } };
  const context = vm.createContext({ URLSearchParams,
    location: { search, origin: 'https://studio.test' },
    document: { body: new Element('body'), getElementById: id => elements[id], addEventListener() {}, createElement: tag => new Element(tag) },
    performance: { now: () => 1000 }, requestAnimationFrame() {},
    addEventListener(type, fn) { handlers[type] = fn; },
    fetch: url => Promise.resolve({ json: () => Promise.resolve(url === 'sample.json' ? { en: titleScenes } : { design: {} }) }),
    VidScenes: { build(container, design, scenes, options) {
      builds.push({ design, scenes, options });
      return Promise.resolve({ timeline: { time() {} }, duration: scenes.length * 3, stage: new Element(),
        scenes: scenes.map((s, i) => ({ start: i * 3, duration: 3, type: s.type })) });
    } } });
  context.window = context;
  context.parent = standalone ? context : parent;
  vm.runInContext(playerSource, context);
  return { context, elements, builds, messages, parent,
    resize() { handlers.resize(); },
    message(data, source = parent, origin = context.location.origin) { handlers.message({ data, source, origin }); } };
}

test('player accepts only its same-origin parent and targets replies to that origin', async () => {
  const h = playerHarness();
  h.message({ type: 'load', scenes: titleScenes }, {}, 'https://studio.test');
  h.message({ type: 'load', scenes: titleScenes }, h.parent, 'https://evil.test');
  h.message({ type: 'load', scenes: titleScenes }, null, 'https://studio.test');
  assert.equal(h.builds.length, 0);
  h.message({ type: 'load', scenes: titleScenes });
  await flush();
  assert.equal(h.builds.length, 1);
  for (const source of [{}, h.parent]) {
    const origin = source === h.parent ? 'https://evil.test' : 'https://studio.test';
    for (const command of [{ type: 'play' }, { type: 'seek', time: 2 }, { type: 'seekScene', index: 0 }]) h.message(command, source, origin);
  }
  assert.equal(h.context.__player.state.playing, false);
  assert.equal(h.context.__player.state.time, 0);
  h.message({ type: 'play' });
  assert.equal(h.context.__player.state.playing, true);
  h.message({ type: 'pause' }, {}, 'https://studio.test');
  assert.equal(h.context.__player.state.playing, true);
  h.message({ type: 'pause' });
  assert.equal(h.context.__player.state.playing, false);
  assert.ok(h.messages.every(m => m.origin === 'https://studio.test'));
});

test('player transitions to and from an empty state without autoplay or invalid scaling', async () => {
  const h = playerHarness();
  h.message({ type: 'load', scenes: titleScenes, options: { autoplay: true } });
  await flush();
  assert.equal(h.context.__player.state.playing, true);
  h.message({ type: 'load', scenes: [], options: { autoplay: true } });
  await flush();
  assert.equal(h.context.__player.state.duration, 0);
  assert.equal(h.context.__player.state.playing, false);
  assert.equal(h.elements.msg.textContent, 'No scenes yet');
  assert.equal(h.elements.scaler.style.display, 'none');
  assert.equal(h.elements.play.disabled, true);
  assert.equal(h.elements.scrub.disabled, true);
  assert.equal(h.elements.chips.children.length, 0);
  assert.equal(h.messages.at(-1).message.scene, -1);
  const transform = h.elements.scaler.style.transform;
  h.context.__player.state.stage.offsetWidth = h.context.__player.state.stage.offsetHeight = 0;
  h.resize();
  assert.equal(h.elements.scaler.style.transform, transform, 'resize must not fit the hidden empty stage');
  h.message({ type: 'play' });
  assert.equal(h.context.__player.state.playing, false);
  h.message({ type: 'load', scenes: titleScenes });
  await flush();
  assert.equal(h.elements.msg.style.display, 'none');
  assert.equal(h.elements.scaler.style.display, '');
  assert.equal(h.elements.play.disabled, false);
  assert.equal(h.elements.chips.children.length, 1);
  assert.doesNotMatch(h.elements.scaler.style.transform, /NaN|Infinity/);
});

test('standalone query parameters still load a sample and local controls work', async () => {
  const h = playerHarness({ standalone: true, search: '?sample=1&controls=1&autoplay=1' });
  await flush();
  assert.equal(h.builds.length, 1);
  assert.equal(h.context.__player.state.playing, true);
  h.elements.play.onclick();
  assert.equal(h.context.__player.state.playing, false);
  h.message({ type: 'play' }, h.context);
  assert.equal(h.context.__player.state.playing, false);
  assert.equal(h.messages.length, 0);
});
