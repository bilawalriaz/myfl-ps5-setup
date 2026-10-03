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
test('automatic startup respects patch dependency order without launching Payload Manager', async () => {
  const h = harness(); await h.run();
  assert.deepEqual(h.sent, ['klogsrv-ps5.elf', 'kstuff.elf', 'shadowmountplus.elf', 'ftpsrv-ps5.elf']);
  assert.deepEqual(h.waits, [3000]);
});
test('a transfer failure stops dependent services', async () => {
  const h = harness('kstuff.elf');
  await assert.rejects(h.run(), /transfer failed/);
  assert.deepEqual(h.sent, ['klogsrv-ps5.elf', 'kstuff.elf']);
  assert.deepEqual(h.waits, []);
});
