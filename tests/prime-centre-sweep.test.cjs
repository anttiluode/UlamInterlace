"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const source = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(source, "the single-file page must contain its JavaScript");
new vm.Script(source[1]); // Syntax-check the full browser script.

function page() {
  const elements = new Map();
  const timers = new Map();
  let timerId = 0;
  const frames = [];
  const docEvents = {};
  const get = id => {
    if (!elements.has(id)) {
      const events = {};
      const attributes = {};
      const el = {
        id, events, attributes, value: "", innerHTML: "", textContent: "",
        clientWidth: 650, width: 0, height: 0,
        getContext() { return {}; },
        addEventListener(type, cb) { events[type] = cb; },
        setAttribute(key, value) { attributes[key] = value; },
      };
      elements.set(id, el);
    }
    return elements.get(id);
  };
  const document = {
    hidden: false,
    documentElement: {},
    getElementById: get,
    querySelectorAll() { return []; },
    addEventListener(type, cb) { docEvents[type] = cb; }
  };
  const css = key => {
    if (key === "--blend") return "multiply";
    if (key === "--plate") return "#ffffff";
    if (key === "--plate-fg") return "#000000";
    return "#2266aa";
  };
  vm.runInNewContext(source[1], {
    document,
    ResizeObserver: class { observe() {} },
    MutationObserver: class { observe() {} },
    getComputedStyle: () => ({getPropertyValue: css}),
    matchMedia: () => ({addEventListener() {}}),
    requestAnimationFrame: cb => { frames.push(cb); },
    performance: {now: () => 0},
    setTimeout: (cb, delay) => {
      const id = ++timerId;
      timers.set(id, {cb, delay});
      return id;
    },
    clearTimeout: id => {timers.delete(id);},
  }, {timeout: 10000});
  function fire(id, type = "click", target) {
    const cb = get(id).events[type];
    assert.equal(typeof cb, "function", id + " missing " + type + " event");
    cb({target: target || get(id)});
  }
  function advanceClock() {
    assert.equal(timers.size, 1, "a playing prime sweep has exactly one timer");
    const [id, timer] = timers.entries().next().value;
    timers.delete(id);
    timer.cb();
    return timer.delay;
  }
  return {get, fire, timers, frames, document, docEvents, advanceClock};
}

test("Prime centre controls are in the original Spiral section", () => {
  assert.match(html, /id="primePlay"/);
  assert.match(html, /id="primePrev"/);
  assert.match(html, /id="primeNext"/);
  assert.match(html, /id="primeSpeed"/);
  assert.match(html, /data-s="1"/);
  assert.match(html, /data-s="17"/);
  assert.match(html, /data-s="41"/);
});

test("Auto sweep starts at the next prime and follows true prime numbers", () => {
  const p = page();
  assert.equal(p.get("start").value, 1);
  p.fire("primePlay");
  assert.equal(p.get("primePlay").attributes["aria-pressed"], true);
  assert.equal(p.advanceClock(), 800);
  assert.equal(p.get("start").value, 2);
  p.advanceClock(); assert.equal(p.get("start").value, 3);
  p.advanceClock(); assert.equal(p.get("start").value, 5);
  p.advanceClock(); assert.equal(p.get("start").value, 7);
  p.fire("primePlay");
  assert.equal(p.timers.size, 0);
  assert.equal(p.get("primePlay").attributes["aria-pressed"], false);
});

test("Presets, manual centres, and stepping select strict neighbouring primes", () => {
  const p = page();
  p.fire("startPresets", "click", {closest: () => ({dataset: {s: "41"}})});
  assert.equal(p.get("start").value, 41);
  p.fire("primeNext"); assert.equal(p.get("start").value, 43);
  p.fire("primePrev"); assert.equal(p.get("start").value, 41);
  p.fire("primePrev"); assert.equal(p.get("start").value, 37);
  p.fire("start", "change", {value: "17"});
  p.fire("primeNext"); assert.equal(p.get("start").value, 19);
  p.fire("start", "change", {value: "1000000"});
  p.fire("primeNext"); assert.equal(p.get("start").value, 2);
  p.fire("primePrev"); assert.equal(p.get("start").value, 999983);
});

test("Changing playback speed reschedules without spawning parallel timers", () => {
  const p = page();
  p.fire("primePlay");
  assert.equal(p.timers.size, 1);
  p.fire("primeSpeed", "input", {value: "300"});
  assert.equal(p.timers.size, 1);
  assert.equal(p.get("primeSpeedV").textContent, "0.30 s");
  assert.equal(p.advanceClock(), 300);
  assert.equal(p.get("start").value, 2);
  assert.equal(p.timers.size, 1);
});

test("Manual centre input, presets, visibility, zoom and reset stop the prime clock", () => {
  const p = page();
  p.fire("primePlay");
  p.fire("startPresets", "click", {closest: () => ({dataset: {s: "17"}})});
  assert.equal(p.get("start").value, 17);
  assert.equal(p.timers.size, 0);

  p.fire("primePlay");
  p.fire("start", "change", {value: "41"});
  assert.equal(p.timers.size, 0);

  p.fire("primePlay");
  p.fire("play"); // zoom sweep takes ownership
  assert.equal(p.timers.size, 0);
  assert.equal(p.get("primePlay").attributes["aria-pressed"], false);
  assert.equal(p.get("play").attributes["aria-pressed"], true);

  p.fire("primePlay"); // prime sweep takes ownership back
  assert.equal(p.get("play").attributes["aria-pressed"], false);
  assert.equal(p.timers.size, 1);
  p.document.hidden = true;
  p.docEvents.visibilitychange();
  assert.equal(p.timers.size, 0);
  p.document.hidden = false;

  p.fire("primePlay");
  p.fire("reset");
  assert.equal(p.timers.size, 0);
  assert.equal(p.get("start").value, 1);
  assert.equal(p.get("primeSpeedV").textContent, "0.80 s");
  assert.equal(p.get("primePlay").attributes["aria-pressed"], false);
});
