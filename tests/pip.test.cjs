const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(__dirname + '/../extension/pip.js', 'utf8'), context);
const { toggle } = context.FloatTube;
test('Safari native entry and return use the existing video', async () => {
  const calls = [];
  const video = { readyState: 4, webkitPresentationMode: 'inline', webkitSupportsPresentationMode: mode => mode === 'picture-in-picture', webkitSetPresentationMode: mode => calls.push(mode) };
  await toggle(video, {});
  video.webkitPresentationMode = 'picture-in-picture';
  await toggle(video, {});
  assert.deepEqual(calls, ['picture-in-picture', 'inline']);
});
test('standard API fallback enters and exits', async () => {
  let entered = 0, exited = 0;
  const video = { readyState: 1, requestPictureInPicture: async () => entered++ };
  await toggle(video, { pictureInPictureEnabled: true });
  await toggle(video, { pictureInPictureElement: video, exitPictureInPicture: async () => exited++ });
  assert.equal(entered, 1); assert.equal(exited, 1);
});
test('missing or unloaded video gives actionable feedback', async () => {
  await assert.rejects(toggle(null, {}), /Start a YouTube video/);
  await assert.rejects(toggle({ readyState: 0 }, {}), /Start a YouTube video/);
});
test('unsupported playback and denied native requests are surfaced', async () => {
  await assert.rejects(toggle({ readyState: 4 }, {}), /unavailable/);
  await assert.rejects(toggle({ readyState: 4, requestPictureInPicture: async () => { throw new Error('Denied'); } }, { pictureInPictureEnabled: true }), /Denied/);
});
test('manifest confines execution to YouTube and has no background worker', () => {
  const manifest = JSON.parse(fs.readFileSync(__dirname + '/../extension/manifest.json'));
  assert.deepEqual(manifest.content_scripts[0].matches, ['https://www.youtube.com/*', 'https://m.youtube.com/*']);
  assert.equal(manifest.background, undefined);
  for (const script of manifest.content_scripts[0].js) assert.ok(fs.existsSync(__dirname + '/../extension/' + script));
});
