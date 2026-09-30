const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { drawingProgress } = require('./site.js');
let checks = 0;
function equal(a, b) { assert.equal(a, b); checks++; }
function setup({ reduced = false, saveData = false, mobile = false, rejected = false } = {}) {
  const events = {}, pageEvents = {}, classes = new Set();
  const motion = { matches: reduced, addEventListener: (_, fn) => { motion.change = fn; } };
  const phone = { matches: mobile, addEventListener: (_, fn) => { phone.change = fn; } };
  const film = {
    dataset: { mobileSrc: 'mobile.mp4', desktopSrc: 'laptop.mp4' }, paused: true, src: '', plays: 0,
    classList: { add: x => classes.add(x), remove: x => classes.delete(x) },
    getAttribute: () => film.src, removeAttribute: () => { film.src = ''; }, load() {},
    addEventListener: (name, fn) => { events[name] = fn; },
    play() { film.plays++; if (rejected) return Promise.reject(new Error('Blocked')); film.paused = false; events.playing?.(); return Promise.resolve(); },
    pause() { film.paused = true; }
  };
  const document = { hidden: false, querySelector: s => s === '[data-hero-film]' ? film : null, querySelectorAll: () => [], addEventListener: (n, fn) => { pageEvents[n] = fn; } };
  vm.runInNewContext(fs.readFileSync(__dirname + '/site.js', 'utf8'), { document, window: { matchMedia: q => q.includes('reduced-motion') ? motion : phone }, navigator: { connection: { saveData } }, Element: { prototype: {} } });
  return { film, document, pageEvents, motion, phone, events, classes };
}
(async () => {
  for (const option of [{ reduced: true }, { saveData: true }]) { const s = setup(option); equal(s.film.src, ''); equal(s.film.plays, 0); }
  const s = setup(); equal(s.film.src, 'laptop.mp4'); equal(s.film.loop, true);
  equal(setup({ mobile: true }).film.src, 'mobile.mp4');
  s.phone.matches = true; s.phone.change(); equal(s.film.src, 'mobile.mp4');
  s.document.hidden = true; s.pageEvents.visibilitychange(); equal(s.film.paused, true);
  s.document.hidden = false; s.pageEvents.visibilitychange(); equal(s.film.paused, false);
  s.motion.matches = true; s.motion.change(); equal(s.film.src, '');
  const blocked = setup({ rejected: true }); await Promise.resolve(); equal(blocked.classes.has('is-ready'), false);
  const failed = setup(); failed.events.error(); equal(failed.classes.has('is-ready'), false);
  equal(drawingProgress(1000, 800), 0); equal(drawingProgress(160, 800), 1); equal(drawingProgress(460, 800), .5); equal(drawingProgress(1000, 800, true), 1);
  const home = fs.readFileSync(__dirname + '/templates/home.html', 'utf8'); equal(home.includes('data-hero-film-control'), false); equal(home.includes('muted loop playsinline'), true);
  console.log(`Continuous media and scroll drawings: ${checks} checks PASS`);
})().catch(error => { console.error(error); process.exitCode = 1; });
