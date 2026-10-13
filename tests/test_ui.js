// Behavioral regressions for UI persistence and asynchronous navigation. No browser packages required.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { test } = require('node:test');
const html = fs.readFileSync('skills/vid-studio/assets/ui/index.html', 'utf8');
const code = html.slice(html.lastIndexOf('<script>') + 8, html.lastIndexOf('</script>'));
function harness() {
  const timers = new Map(), listeners = {}, nodes = new Map();
  const element = id => nodes.get(id) || (nodes.set(id, { id, dataset: {}, innerHTML: '', textContent: '', insertAdjacentHTML() {}, contains() { return false; }, addEventListener() {}, querySelector() { return null; } }), nodes.get(id));
  const document = { visibilityState: 'visible', body: {}, activeElement: null, getElementById: element, querySelector() { return null; }, querySelectorAll() { return []; }, addEventListener(type, fn) { (listeners[type] ||= []).push(fn); } };
  let timerId = 0;
  const context = vm.createContext({ document, location: { hash: '#/channels/a/look', origin: 'http://localhost' }, history: { replaceState(state, title, hash) { context.location.hash = hash; } }, localStorage: { getItem() { return null; }, setItem() {} }, navigator: {}, window: { addEventListener() {} }, CSS: { escape: x => x }, console, structuredClone,
    setTimeout(fn) { timers.set(++timerId, fn); return timerId; }, clearTimeout(id) { timers.delete(id); } });
  // Avoid booting the server connection; all application functions and event handlers remain active.
  vm.runInContext(code.slice(0, code.indexOf('document.getElementById("settings-btn").insertAdjacentHTML')), context);
  vm.runInContext('PROJECT = "p"; PROJECTS = [{id:"p",name:"Project"}]; toast = () => {};', context);
  return { context, timers, listeners, nodes, run: source => vm.runInContext(source, context), async flush() { const work = [...timers.values()]; timers.clear(); for (const fn of work) fn(); for (let i = 0; i < 10; i++) await Promise.resolve(); } };
}
const view = id => ({ id, design: { color: 'old' }, voice: { persona: 'old' }, fields: { format: 'old' }, savedDesign: '{"color":"old"}', savedVoice: '{"persona":"old"}', savedFields: '{"format":"old"}', ask: {} });

test('debounced writes retain their channel and immutable snapshot when navigating', async () => {
  const h = harness(), writes = [];
  h.context.a = view('a'); h.context.b = view('b'); h.context.write = async (method, path, body) => { writes.push([path, structuredClone(body)]); return body; };
  h.run('api = write; CV = a; a.design.color = "red"; scheduleChannelSave(a, "design"); CV = b; b.design.color = "blue"; scheduleChannelSave(b, "design"); a.design.color = "later"; CV = null;');
  await h.flush();
  assert.deepEqual(writes, [['channels/a/design', { color: 'red' }], ['channels/b/design', { color: 'blue' }]]);
  assert.equal(h.context.a.design.color, 'later');
});

test('writes for the same channel are serialized and cannot overwrite newer edits', async () => {
  const h = harness(), writes = []; let release;
  h.context.a = view('a');
  h.context.write = (method, path, body) => { writes.push(structuredClone(body)); return writes.length === 1 ? new Promise(resolve => { release = () => resolve(body); }) : Promise.resolve(body); };
  h.run('api = write; CV = a; a.design.color = "first"; one = queueChannelSave(a, "design", a.design); a.design.color = "second"; two = queueChannelSave(a, "design", a.design);');
  await Promise.resolve(); await Promise.resolve();
  assert.equal(writes.length, 1); release();
  await h.context.one; await h.context.two;
  assert.deepEqual(writes, [{ color: 'first' }, { color: 'second' }]);
  assert.equal(h.context.a.design.color, 'second');
  assert.equal(h.context.a.savedDesign, '{"color":"second"}');
});

test('format and Ask drafts survive remote refreshes and channels list never reopens detail', async () => {
  const h = harness(); h.context.a = view('a'); h.context.a.fields.format = 'draft'; h.context.a.ask.voice = 'my request';
  h.context.state = { channels: [{ id: 'a', name: 'A', format: 'remote', language: 'English' }], findings: [] };
  h.run('S = state; CV = a; a.tab = "voice"; api = async (method, path) => path.endsWith("design") ? {color:"remote"} : path.endsWith("voice") ? a.voice : state; renderChannel = () => { renders++; }; renders = 0;');
  await h.run('poll()');
  assert.equal(h.context.a.fields.format, 'draft');
  assert.equal(h.context.a.ask.voice, 'my request');
  h.run('location.hash = "#/channels"; renders = 0; lastStateJson = JSON.stringify(state);');
  await h.run('poll()');
  assert.equal(h.run('renders'), 0);
});

test('pending detail requests cannot repaint after leaving the route', async () => {
  const h = harness(); let release;
  h.context.get = () => new Promise(resolve => { release = resolve; });
  h.run('api = get; location.hash = "#/research/p/stories/s"; pending = renderEditor("story", "s"); location.hash = "#/research/p/findings";');
  release({ id: 's', notes: '', title: 'Old page' }); await h.context.pending;
  assert.equal(h.run('editor'), null);
  assert.equal(h.nodes.get('app').innerHTML, '');
});

test('range values, review scores, and Ask subtitles do not inject markup', () => {
  const h = harness(); h.context.bad = '"><img src=x onerror=alert(1)>';
  const slider = h.run('slider("radius", 0, 48, 2, bad, x => x)');
  assert.ok(!slider.includes('<img')); assert.ok(slider.includes('&lt;img'));
  h.run('editor = {data:{review:{scores:{hook:bad}, summary:""}}};');
  assert.ok(!h.run('qualityTab()').includes('<img'));
  h.run('copyText = async () => false; openDialog = options => { captured = options; }; showPrompt("Test", "text", bad);');
  assert.ok(!h.run('captured.sub').includes('<img'));
});

test('global sections stay visible and Research project controls are scoped locally', () => {
  assert.match(html, /aria-label="Studio sections"/);
  for (const section of ['research', 'production', 'channels']) assert.match(html, new RegExp(`data-section="${section}"`));
  const h = harness(); h.context.state = { settings: { name: 'Project', description: '' }, runs: [], sources: [], findings: [], topics: [], stories: [], scripts: [], channels: [] };
  h.run('S = state; topicsPanel = () => ""; location.hash = "#/research/p/topics"; render();');
  assert.equal(h.nodes.get('research-context').hidden, false);
  assert.match(h.nodes.get('app').innerHTML, /aria-label="Sections"/);
  h.run('location.hash = "#/production"; render();');
  assert.equal(h.nodes.get('research-context').hidden, true);
  assert.match(h.nodes.get('app').innerHTML, /<h1>Production<\/h1>/);
  h.run('location.hash = "#/channels"; render();');
  assert.equal(h.nodes.get('research-context').hidden, true);
  assert.match(h.nodes.get('app').innerHTML, /<h1>Channels<\/h1>/);
});

test('Hindi preset changes retain compatible display and body fonts', async () => {
  const h = harness(); h.context.a = view('a');
  h.context.a.design = { fonts: { display: 'Hindi A', body: 'Hindi B', mono: 'Mono' }, logo: { text: 'My brand' } };
  h.run('S = {channels:[{id:"a",language:"Hindi"}]}; CV = a; CATALOG = {fonts:[{family:"Hindi A", devanagari:true},{family:"Hindi B", devanagari:true}], presets:[{id:"latin",name:"Latin",design:{fonts:{display:"Latin",body:"Latin",mono:"Mono"},logo:{text:""}}}]}; api = async (method,path,body) => body; renderChannel = () => {}; undoToast = () => {}; actions["pick-preset"]("latin");');
  assert.equal(h.context.a.design.fonts.display, 'Hindi A'); assert.equal(h.context.a.design.fonts.body, 'Hindi B');
  assert.equal(h.context.a.design.logo.text, 'My brand');
  await h.flush();
});

test('script polling refreshes sidebar and channel timing while preserving a typed draft', async () => {
  const h = harness();
  h.context.state = { channels: [{ id: 'a', kind: 'video' }], findings: [] };
  h.context.remote = { id: 's', version: 'one', text: 'saved', title: 'Title', channel: 'a', comments: [{ id: 'c', body: 'new' }], angles: [], review: null };
  h.context.newVoice = { words_per_minute: 120 };
  h.context.get = async (method, path) => path.endsWith('/scripts/s') ? h.context.remote : path.endsWith('/design') ? { color: 'new' } : path.endsWith('/voice') ? h.context.newVoice : h.context.state;
  h.run('S = state; api = get; location.hash = "#/production/p/s"; editor = {kind:"script", dirty:true, data:{...remote, text:"typed draft", comments:[]}, voice:{words_per_minute:160}, design:{color:"old"}}; document.activeElement = {id:"doc-text"}; renders = 0; renderEditor = () => {renders++;};');
  await h.run('poll()');
  assert.equal(h.run('editor.data.text'), 'typed draft'); assert.equal(h.run('editor.data.comments.length'), 1);
  assert.equal(h.run('editor.voice.words_per_minute'), 120); assert.equal(h.run('renders'), 1);
});

test('choose-angle saves typed text before setting the hook and generating its prompt', async () => {
  const h = harness(), operations = [];
  h.context.operations = operations;
  h.run('S = {default_workspace:true}; editor = {kind:"script", dirty:true, data:{id:"s",title:"Title"}}; saveDoc = async () => { operations.push("save"); editor.dirty = false; return true; }; api = async () => { operations.push("hook"); return {id:"s",title:"Title",angles:[{id:"hook",hook:"New hook"}]}; }; renderEditor = () => {}; showPrompt = () => { operations.push("prompt"); };');
  await h.run('actions["choose-angle"]("hook")');
  assert.deepEqual(operations, ['save', 'hook', 'prompt']);
});

test('saving a document preserves title and text typed while the PUT is in flight', async () => {
  const h = harness(); let release;
  h.context.write = (method, path, body) => new Promise(resolve => { release = () => resolve({ ...body, id: 's', version: 'two' }); });
  h.run('S = {default_workspace:true}; api = write; refresh = async () => false; renderEditor = () => {}; editor = {kind:"script",dirty:true,data:{id:"s",version:"one",title:"Before",text:"Before text"}}; saving = saveDoc(true); editor.data.title = "Later title"; editor.data.text = "Later text";');
  release(); assert.equal(await h.context.saving, false);
  assert.equal(h.run('editor.data.title'), 'Later title'); assert.equal(h.run('editor.data.text'), 'Later text');
  assert.equal(h.run('editor.data.version'), 'two'); assert.equal(h.run('editor.dirty'), true);
  assert.notEqual(h.run('editor.view'), 'preview');
});

test('choosing a hook preserves typing during its PUT and saves it before a rewrite prompt', async () => {
  const h = harness(), writes = []; let releaseHook;
  h.context.write = (method, path, body) => {
    writes.push(structuredClone(body));
    if (body.chosen_angle) return new Promise(resolve => { releaseHook = () => resolve({ id: 's', title: 'Before', text: 'Before text', version: 'hook', angles: [{ id: 'hook', hook: 'New hook' }] }); });
    return Promise.resolve({ ...body, id: 's', version: 'saved', angles: [{ id: 'hook', hook: 'New hook' }] });
  };
  h.run('S = {default_workspace:true}; api = write; refresh = async () => false; renderEditor = () => {}; prompts = 0; showPrompt = () => {prompts++;}; editor = {kind:"script",dirty:false,data:{id:"s",version:"one",title:"Before",text:"Before text"}}; choosing = actions["choose-angle"]("hook"); editor.data.title = "Later title"; editor.data.text = "Later text"; editor.dirty = true;');
  releaseHook(); await h.context.choosing;
  assert.equal(writes.length, 2); assert.equal(writes[1].title, 'Later title'); assert.equal(writes[1].text, 'Later text');
  assert.equal(h.run('editor.data.title'), 'Later title'); assert.equal(h.run('editor.data.text'), 'Later text');
  assert.equal(h.run('editor.dirty'), false); assert.equal(h.run('prompts'), 1);
});

test('continued typing during the follow-up hook save stays dirty and defers its prompt', async () => {
  const h = harness(); let releaseHook, releaseSave;
  h.context.write = (method, path, body) => new Promise(resolve => {
    const result = { ...body, id: 's', title: body.title || 'Before', text: body.text || 'Before text', version: 'two', angles: [{ id: 'hook', hook: 'New hook' }] };
    if (body.chosen_angle) releaseHook = () => resolve(result); else releaseSave = () => resolve(result);
  });
  h.run('S = {default_workspace:true}; api = write; refresh = async () => false; renderEditor = () => {}; prompts = 0; showPrompt = () => {prompts++;}; editor = {kind:"script",dirty:false,data:{id:"s",version:"one",title:"Before",text:"Before text"}}; choosing = actions["choose-angle"]("hook"); editor.data.text = "New draft"; editor.dirty = true;');
  releaseHook(); for (let i = 0; i < 10 && !releaseSave; i++) await Promise.resolve();
  assert.equal(h.run('editor.data.text'), 'New draft');
  h.run('editor.data.title = "Newest title"; editor.data.text = "Newest draft";');
  releaseSave(); await h.context.choosing;
  assert.equal(h.run('editor.data.text'), 'Newest draft'); assert.equal(h.run('editor.data.title'), 'Newest title');
  assert.equal(h.run('editor.dirty'), true); assert.equal(h.run('prompts'), 0);
});

test('Channels starts with zero projects without requesting a project state or redirecting', async () => {
  const h = harness(), calls = [];
  h.context.globalState = { projects: [], channels: [{id:'a',name:'First channel',kind:'video',language:'English',format:''}], scripts: [], stories: [], workspace: '/ws', default_workspace: true };
  h.context.read = async (method, path) => { calls.push(path); return path === 'projects' ? { projects: [] } : h.context.globalState; };
  h.run('PROJECT = null; PROJECTS = []; S = null; api = read; location.hash = "#/channels";');
  await h.run('loadProjects().then(enterProject).then(ok => {if(ok) render();})');
  assert.equal(h.context.location.hash, '#/channels'); assert.equal(h.run('PROJECT'), null); assert.equal(h.run('S'), null);
  assert.deepEqual(calls, ['projects', 'production']);
  assert.match(h.nodes.get('app').innerHTML, /First channel/); assert.match(h.nodes.get('app').innerHTML, /href="#\/channels\/a"/);
  assert.equal(h.nodes.get('research-context').hidden, true);
});

test('Production starts with zero projects and offers independent channel onboarding', async () => {
  const h = harness(); h.context.globalState = { projects: [], channels: [], scripts: [], stories: [], default_workspace: true };
  h.run('PROJECT = null; PROJECTS = []; S = null; api = async () => globalState; location.hash = "#/production";');
  assert.equal(await h.run('enterProject()'), true); h.run('render()');
  assert.equal(h.context.location.hash, '#/production'); assert.match(h.nodes.get('app').innerHTML, /data-action="open-channels"/);
  h.run('actions["open-channels"]()'); assert.equal(h.context.location.hash, '#/channels');
});

test('all-project board distinguishes duplicate script IDs and links their source project, story, and channel', () => {
  const h = harness();
  h.context.globalState = { projects: [{id:'one',name:'One'},{id:'two',name:'Two'}], channels: [{id:'a',name:'A',language:'English'}], stories: [{id:'source',project:'one',title:'Source One'},{id:'source',project:'two',title:'Source Two'}], scripts: [{id:'same',project:'one',project_name:'One',story:'source',channel:'a',title:'Draft One',stage:'script'},{id:'same',project:'two',project_name:'Two',story:'source',channel:'a',title:'Draft Two',stage:'script'}] };
  h.run('GLOBAL = globalState; S = null; PROJECT = null; location.hash = "#/production"; render();');
  const board = h.nodes.get('app').innerHTML;
  for (const project of ['one', 'two']) {
    assert.ok(board.includes(`href="#/production/${project}/same"`)); assert.ok(board.includes(`data-project="${project}"`));
    assert.ok(board.includes(`href="#/research/${project}/stories/source"`));
  }
  assert.ok(board.includes('href="#/channels/a"'));
  h.run('actions["filter-production-project"]("", {value:"two"})');
  assert.ok(!h.nodes.get('app').innerHTML.includes('Draft One')); assert.ok(h.nodes.get('app').innerHTML.includes('Draft Two'));
  h.run('actions["open-script"]("same", {dataset:{project:"two"}})');
  assert.equal(h.context.location.hash, '#/production/two/same');
});

test('duplicate script IDs mutate only the project selected by their canonical production route', async () => {
  const h = harness(), puts = [];
  h.context.globalState = {projects:[{id:'one',name:'One'},{id:'two',name:'Two'}],channels:[],scripts:[],stories:[]};
  h.context.projectState = {settings:{name:'Two'},findings:[],scripts:[{id:'same'}],stories:[],channels:[]};
  h.context.readWrite = async (method,path,body) => {
    if (method === 'PUT') {puts.push(path); return {...body,id:'same',version:'two'};}
    if (path === 'production') return h.context.globalState;
    assert.equal(path, 'p/two/state'); return h.context.projectState;
  };
  h.run('api = readWrite; location.hash = "#/production/two/same";');
  assert.equal(await h.run('enterProject()'), true); assert.equal(h.run('PROJECT'), 'two');
  h.run('renderEditor = () => {}; editor = {kind:"script",dirty:true,data:{id:"same",title:"Two edit",text:"Owner-specific edit",version:"one"}};');
  await h.run('saveDoc()'); assert.deepEqual(puts, ['p/two/scripts/same']);
});

test('source-story, channel-look, and story-to-script links cross the independent sections coherently', () => {
  const h = harness();
  h.context.projectState = {stories:[{id:'source',title:'Research story'}],scripts:[{id:'draft',story:'source',channel:'a',stage:'script'}],topics:[],channels:[{id:'a',name:'A',kind:'video'}]};
  h.run('S = projectState; editor = {kind:"script",data:{id:"draft",story:"source",channel:"a"},design:{aspect:"9:16"},voice:{},sideTab:"preview"};');
  assert.match(h.run('scriptHeader()'), /href="#\/research\/p\/stories\/source"/);
  assert.match(h.run('scriptHeader()'), /href="#\/channels\/a"/);
  assert.match(h.run('previewTab()'), /href="#\/channels\/a\/look"/);
  h.run('editor = {kind:"story",data:{id:"source",topics:[],findings:[]}};');
  assert.match(h.run('storySide()'), /href="#\/production\/p\/draft"/);
});

test('sending a story saves research notes first and keeps its originating project in the draft prompt', async () => {
  const h = harness(), calls = [], prompts = [];
  h.context.globalState = {projects:[{id:'p',name:'Original project'},{id:'other',name:'Other project'}],channels:[{id:'a',name:'A'}],scripts:[],stories:[],default_workspace:true};
  h.context.projectState = {settings:{},findings:[],channels:h.context.globalState.channels,scripts:[],stories:[],default_workspace:true};
  h.context.write = async (method,path,body) => {
    calls.push([method,path,structuredClone(body)]);
    if (method === 'PUT') return { ...body, id:'source', version:'saved' };
    if (method === 'POST') return { id:'created',story:'source',channel:'a' };
    return h.context.projectState;
  };
  h.context.capture = (title,prompt) => prompts.push(prompt);
  h.run('GLOBAL = globalState; PROJECTS = globalState.projects; S = projectState; api = write; renderEditor = () => {}; openDialog = options => { captured = options; }; showPrompt = capture; editor = {kind:"story",dirty:true,data:{id:"source",title:"Story",notes:"New research evidence",version:"one"}};');
  await h.run('actions["send-to-production"]()');
  assert.equal(calls[0][1], 'p/p/stories/source'); assert.equal(calls[0][2].notes, 'New research evidence');
  assert.equal(h.run('editor.dirty'), false);
  await h.run('captured.onSubmit({querySelectorAll:() => [{value:"a"}]})');
  assert.ok(calls.some(([method,path]) => method === 'POST' && path === 'p/p/scripts'));
  assert.equal(h.context.location.hash, '#/production');
  h.run('PROJECT = "other";'); await h.flush();
  assert.equal(prompts.length, 1); assert.match(prompts[0], /project "Original project"/); assert.ok(!prompts[0].includes('Other project'));
});

test('overlapping production-owner navigation ignores the previous project state response', async () => {
  const h = harness(); let releaseFirst;
  h.context.globalState = {projects:[{id:'one',name:'One'},{id:'two',name:'Two'}],channels:[],scripts:[],stories:[]};
  h.context.read = async (method,path) => {
    if (path === 'production') return h.context.globalState;
    if (path === 'p/one/state') return new Promise(resolve => {releaseFirst = () => resolve({settings:{name:'One'},findings:[],channels:[],stories:[],scripts:[]});});
    assert.equal(path, 'p/two/state'); return {settings:{name:'Two'},findings:[],channels:[],stories:[],scripts:[]};
  };
  h.run('api = read; location.hash = "#/production/one/same"; firstNavigation = enterProject();');
  for (let i = 0; i < 10 && !releaseFirst; i++) await Promise.resolve();
  h.run('location.hash = "#/production/two/same"; secondNavigation = enterProject();');
  assert.equal(await h.context.secondNavigation, true);
  releaseFirst(); assert.equal(await h.context.firstNavigation, false);
  assert.equal(h.run('PROJECT'), 'two'); assert.equal(h.run('S.settings.name'), 'Two');
});

test('a story-save conflict blocks sending its unsaved notes to production', async () => {
  const h = harness(), calls = [];
  h.context.rejectSave = async (method,path) => {calls.push(path); const error = new Error('Changed by agent'); error.status = 409; throw error;};
  h.run('api = rejectSave; renderEditor = () => {}; opened = false; openDialog = () => {opened = true;}; editor = {kind:"story",dirty:true,data:{id:"source",title:"Story",notes:"Unsaved evidence",version:"one"}};');
  await h.run('actions["send-to-production"]()');
  assert.deepEqual(calls, ['p/p/stories/source']); assert.equal(h.run('opened'), false);
  assert.equal(h.run('editor.data.notes'), 'Unsaved evidence'); assert.equal(h.run('editor.dirty'), true);
});

test('an invalid production owner never falls back to a valid project with the same script ID', async () => {
  const h = harness(), calls = [];
  h.context.globalState = {projects:[{id:'p',name:'Valid'}],channels:[],scripts:[{id:'same',project:'p'}],stories:[]};
  h.context.read = async (method,path) => {calls.push(path); assert.equal(path,'production'); return h.context.globalState;};
  h.run('GLOBAL = globalState; S = {settings:{name:"Valid"},scripts:[{id:"same"}],findings:[]}; editor = {kind:"script",data:{id:"same",title:"Valid project script"}}; api = read; location.hash = "#/production/missing/same";');
  assert.equal(await h.run('enterProject()'), false);
  assert.equal(h.run('PROJECT'), null); assert.equal(h.run('S'), null); assert.equal(h.run('editor'), null);
  h.context.globalState.scripts.push({id:'new',project:'p'});
  await h.run('poll()');
  assert.match(h.nodes.get('app').innerHTML, /Project not found/);
  assert.ok(!h.nodes.get('app').innerHTML.includes('Valid project script'));
  assert.deepEqual(calls,['production','production']);
  h.run('PROJECT = "p"; S = {settings:{name:"Valid"},findings:[]};');
  await h.run('renderEditor("script","same")');
  assert.match(h.nodes.get('app').innerHTML, /Project not found/);
  assert.deepEqual(calls,['production','production']);
});

test('photos added from the beat list edit only that beat, and parse back as its image', () => {
  const h = harness();
  const text = '# Title\n## Hook\nSpoken.\nVisual: stat | 5% | Rate\nSource: RBI\n\n## Second\nMore words.\n- **Image:** media/old.jpg | Photo: Old\n## Third\nNo visual here.\n\n';
  h.context.text = text;
  const added = h.run('setBeatCue(text, 0, "image", "media/new.jpg")');
  assert.match(added, /Visual: stat \| 5% \| Rate\nImage: media\/new\.jpg\nSource: RBI/);
  assert.deepEqual(JSON.parse(h.run(`JSON.stringify(parseScenes(${JSON.stringify(added)}).map(s => s.image?.src || null))`)), ['media/new.jpg', 'media/old.jpg', null]);
  const replaced = h.run('setBeatCue(text, 1, "image", "media/x.png")');
  assert.ok(replaced.includes('Image: media/x.png') && !replaced.includes('old.jpg'));
  assert.match(h.run('setBeatCue(text, 2, "image", "media/y.png")'), /No visual here\.\nImage: media\/y\.png\n\n$/);
  assert.equal(h.run('setBeatCue(text, 1, "image", null)').includes('Image:'), false);
  assert.equal(h.run('setBeatCue(text, 7, "image", "media/z.png")'), text);
  h.run('editor = { data: { id: "s" } }');
  assert.equal(h.run('mediaUrl("media/a-b.jpg")'), '/api/p/p/scripts/s/media/a-b.jpg');
  assert.equal(h.run('mediaUrl("https://e.com/x.jpg")'), 'https://e.com/x.jpg');
  for (const bad of ['javascript:alert(1)', 'media/../script.json', '/etc/passwd', 'media/x.svg']) assert.equal(h.run(`mediaUrl(${JSON.stringify(bad)})`), '');
});

test('render cannot move to another project while saving a dirty script', async () => {
  const h = harness(), calls = [];
  h.run('editor = { data: { id: "same", video: {} }, project: "p", dirty: true };');
  h.context.write = async (method, path) => { calls.push(path); return {}; };
  h.run('api = write; saveDoc = async () => { PROJECT = "other"; editor = {data:{id:"same"}}; return true; };');
  await h.run('actions["render-video"]()');
  assert.deepEqual(calls, []);
});

test('script preview hides planning comments while keeping comments inside code visible', () => {
  const h = harness();
  h.context.source = '<!--\nPrivate planning notes\n-->\n## Hook\nSpoken line.\n```html\n<!-- literal code -->\n```';
  const rendered = h.run('scriptMarkdown(source)');
  assert.ok(!rendered.includes('Private planning notes'));
  assert.match(rendered, /<h2>Hook<\/h2>/);
  assert.match(rendered, /&lt;!-- literal code --&gt;/);
});

test('narration saves keep their own saved marker and count toward unsaved changes', async () => {
  const h = harness(), writes = [];
  h.context.a = Object.assign(view('a'), { narration: { provider: '' }, savedNarration: '{"provider":""}' });
  h.context.write = async (method, path, body) => { writes.push([path, structuredClone(body)]); return { ...body, pause: 0.3 }; };
  h.run('api = write; CV = a; a.narration.provider = "sarvam";');
  assert.equal(h.run('channelDirty(a)'), true);
  await h.run('queueChannelSave(a, "narration", a.narration)');
  assert.deepEqual(writes, [['channels/a/narration', { provider: 'sarvam' }]]);
  assert.equal(h.context.a.savedNarration, '{"provider":"sarvam","pause":0.3}');
  assert.equal(h.context.a.savedFields, '{"format":"old"}');
  assert.equal(h.run('channelDirty(a)'), false);
});

test('pronunciations parse one "written = said" pair per line', () => {
  const h = harness();
  assert.deepEqual(JSON.parse(h.run('JSON.stringify(parseLexicon("UPI = U P I\\n bad line \\nHDPE=H D P E\\n= x\\nNPCI = N P C I = ok"))')),
    { UPI: 'U P I', HDPE: 'H D P E', NPCI: 'N P C I = ok' });
  assert.equal(h.run('lexiconText({UPI: "U P I", A: "B"})'), 'UPI = U P I\nA = B');
});
