import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';
const source = fs.readFileSync(new URL('../dist/managed/src/managed-payloads.js', import.meta.url), 'utf8')
  .replace(/^import .*;\n/, '').replaceAll('export ', '');
function harness(failAt) {
  const sent = [], waits = [];
  const context = vm.createContext({
    sendManagedPayload: async (_p, _chain, name) => { sent.push(name); if (name === failAt) throw Error('transfer failed'); },
    setTimeout: (resolve, milliseconds) => { waits.push(milliseconds); resolve(); },
  });
  vm.runInContext(source, context);
  return { sent, waits, run: () => context.runManagedPayloads({}, {}, () => {}) };
}
test('managed startup loads only Payload Manager', async () => {
  const h = harness(); await h.run();
  assert.deepEqual(h.sent, ['pldmgr.elf']);
  assert.deepEqual(h.waits, []);
});
test('a transfer failure stops dependent services', async () => {
  const h = harness('pldmgr.elf');
  await assert.rejects(h.run(), /transfer failed/);
  assert.deepEqual(h.sent, ['pldmgr.elf']);
  assert.deepEqual(h.waits, []);
});
