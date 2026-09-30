const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function setup({ reduced = false, saveData = false, mobile = false, rejected = false } = {}) {
  const events = {};
  const pageEvents = {};
  const classes = new Set();
  const motion = { matches: reduced, addEventListener: (_, callback) => { motion.change = callback; } };
  const phone = { matches: mobile, addEventListener: (_, callback) => { phone.change = callback; } };
  const film = {
    dataset: { mobileSrc: 'mobile.mp4', desktopSrc: 'laptop.mp4' },
    paused: true, ended: false, currentTime: 0, src: '', plays: 0,
    classList: { add: name => classes.add(name), remove: name => classes.delete(name) },
    getAttribute: () => film.src,
    removeAttribute: () => { film.src = ''; },
    load() {},
    addEventListener: (name, callback) => { events[name] = callback; },
    play() {
      film.plays++;
      if (rejected) return Promise.reject(new Error('Autoplay blocked'));
      film.paused = false;
      events.play?.();
      return Promise.resolve();
    },
    pause() { film.paused = true; events.pause?.(); }
  };
  const control = { hidden: true, addEventListener: (_, callback) => { control.click = callback; } };
  const document = {
    hidden: false,
    querySelector: selector => selector === '[data-hero-film]' ? film : selector === '[data-hero-film-control]' ? control : null,
    querySelectorAll: () => [],
    addEventListener: (name, callback) => { pageEvents[name] = callback; }
  };
  const window = { matchMedia: query => query.includes('reduced-motion') ? motion : phone };
  vm.runInNewContext(fs.readFileSync(__dirname + '/site.js', 'utf8'), {
    window, document, navigator: { connection: { saveData } }, Element: { prototype: {} }
  });
  return { film, control, events, document, pageEvents, motion, phone, classes };
}

(async () => {
  for (const setting of [{ reduced: true }, { saveData: true }]) {
    const { film, control } = setup(setting);
    assert.equal(film.src, '');
    assert.equal(film.plays, 0);
    assert.equal(control.hidden, true);
  }
  const desktop = setup();
  assert.equal(desktop.film.src, 'laptop.mp4');
  assert.equal(desktop.control.textContent, 'Pause film');
  assert.equal(setup({ mobile: true }).film.src, 'mobile.mp4');
  desktop.phone.matches = true;
  desktop.phone.change();
  assert.equal(desktop.film.src, 'mobile.mp4', 'Crossing the breakpoint selects the portrait film');
  desktop.control.click();
  assert.equal(desktop.film.paused, true);
  desktop.pageEvents.visibilitychange();
  assert.equal(desktop.film.paused, true, 'Returning to page must respect manual pause');
  desktop.control.click();
  assert.equal(desktop.film.paused, false);
  desktop.film.ended = true;
  desktop.film.paused = true;
  desktop.events.ended();
  assert.equal(desktop.control.textContent, 'Replay film');
  desktop.control.click();
  assert.equal(desktop.film.currentTime, 0);
  desktop.motion.matches = true;
  desktop.motion.change();
  assert.equal(desktop.film.src, '');
  assert.equal(desktop.control.hidden, true);
  const blocked = setup({ rejected: true });
  await Promise.resolve();
  assert.equal(blocked.control.textContent, 'Play film');
  const failed = setup();
  failed.events.error();
  assert.equal(failed.control.hidden, true);
  assert.equal(failed.classes.has('is-ready'), false);
  console.log('Hero media: 20 playback, responsive-source, reduced-motion, save-data and failure checks PASS');
})().catch(error => { console.error(error); process.exitCode = 1; });
