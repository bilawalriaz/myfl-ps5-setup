import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const read = name => fs.readFileSync(new URL('../dist/managed/src/' + name, import.meta.url), 'utf8');
const selectionSource = read('selection.js').replaceAll('export ', '');
const payloadSource = read('managed-payloads.js')
  .replace(/^import .*;\n/gm, '')
  .replaceAll('export ', '');

function harness(search, failAt) {
  const sent = [], waits = [];
  const context = vm.createContext({
    location: { search },
    URLSearchParams,
    sendManagedPayload: async (_p, _chain, name) => {
      sent.push(name);
      if (name === failAt) throw Error('transfer failed');
    },
    setTimeout: (resolve, milliseconds) => { waits.push(milliseconds); resolve(); },
  });
  const { selection, runManagedPayloads } = vm.runInContext(
    selectionSource + '\n' + payloadSource + '\n({ selection, runManagedPayloads });', context);
  return { sent, waits, selection, run: () => runManagedPayloads({}, {}, () => {}) };
}

test('a bare launch keeps the automatic PS5 set', async () => {
  const h = harness('');
  assert.equal(h.selection.profile, 'ps5');
  await h.run();
  assert.deepEqual(h.sent, ['klogsrv-ps5.elf', 'kstuff.elf', 'shadowmountplus.elf', 'ftpsrv-ps5.elf', 'orbit-torbox.elf', 'OnionHEN.elf']);
  assert.deepEqual(h.waits, [3000]);
});

test('the Linux profile transfers nothing', async () => {
  const h = harness('?profile=linux&load=');
  assert.deepEqual(Array.from(h.selection.payloads), []);
  await h.run();
  assert.deepEqual(h.sent, []);
  assert.deepEqual(h.waits, []);
});

test('an explicit selection keeps the canonical order and drops unknown names', async () => {
  const h = harness('?profile=ps5&load=OnionHEN.elf,../../etc/passwd,kstuff.elf');
  assert.deepEqual(Array.from(h.selection.payloads), ['kstuff.elf', 'OnionHEN.elf']);
  await h.run();
  assert.deepEqual(h.sent, ['kstuff.elf', 'OnionHEN.elf']);
  assert.deepEqual(h.waits, [3000]);
});

test('only kstuff waits for its loader hand-off', async () => {
  const h = harness('?load=orbit-torbox.elf,ftpsrv-ps5.elf');
  await h.run();
  assert.deepEqual(h.sent, ['ftpsrv-ps5.elf', 'orbit-torbox.elf']);
  assert.deepEqual(h.waits, []);
});

test('a transfer failure stops dependent services', async () => {
  const h = harness('', 'kstuff.elf');
  await assert.rejects(h.run(), /transfer failed/);
  assert.deepEqual(h.sent, ['klogsrv-ps5.elf', 'kstuff.elf']);
  assert.deepEqual(h.waits, []);
});
