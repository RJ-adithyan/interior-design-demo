const assert = require('node:assert/strict');
const { nextShowcasePosition } = require('./site.js');

// A phone's first Next must reach the second card, not skip to the third.
assert.equal(nextShowcasePosition([-14, 312, 637, 963], 0, 1, 947), 312);
// Manual swipe positions must determine navigation without a stale active index.
assert.equal(nextShowcasePosition([-14, 312, 637, 963], 320, 1, 947), 637);
assert.equal(nextShowcasePosition([-14, 312, 637, 963], 947, -1, 947), 637);
assert.equal(nextShowcasePosition([-14, 312, 637, 963], 637, 1, 947), 947);
assert.equal(nextShowcasePosition([0, 53, 523, 920], 53, 1, 800), 523);
assert.equal(nextShowcasePosition([0, 53, 523, 920], 800, 1, 800), 800);
assert.equal(nextShowcasePosition([0], 0, -1, 0), 0);
console.log('Carousel navigation: 7 checks PASS');
