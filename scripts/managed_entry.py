"""Assemble post-loader orchestration; leave upstream exploit code unchanged."""
import ast
import base64
import io
from pathlib import Path
import shutil
import zipfile

PAYLOADS = ['klogsrv-ps5.elf', 'kstuff.elf', 'shadowmountplus.elf', 'ftpsrv-ps5.elf', 'pldmgr.elf']

def assemble(output: Path, host: Path):
    # Read the pinned release's embedded archive without executing its Python host.
    tree = ast.parse(host.read_text())
    encoded = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                   and target.id == 'EMBEDDED_ZIP_B64' for target in node.targets))
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as archive:
        transport = archive.read('relapse/src/kexp.js').decode()
    # These upstream routines send raw ELF to the existing loopback loader.
    begin = transport.index('async function connectToElfldr(')
    end = transport.index('export async function loadOptionalPayloads(', begin)
    routines = transport[begin:end]
    managed = output / 'managed'
    shutil.copytree(output / 'relapse', managed)
    module = managed / 'src' / 'kexp.js'
    module.write_text(module.read_text() + '\n// Transfer routines from pinned WebKit Autoloader v0.5.2, MIT.\n' + routines + '''
export async function sendManagedPayload(p, chain, name, log) {
  const payload = await mapElf(name, p, chain);
  await sendElf(name, payload, p, chain);
  log(name + " transferred to the ELF loader", "info");
}
''')
    (managed / 'src' / 'managed-payloads.js').write_text('''import { sendManagedPayload } from "./kexp.js";
export const payloads = ''' + repr(PAYLOADS) + ''';
export async function runManagedPayloads(p, chain, log) {
  log("Starting the myfl payload set", "info");
  for (const name of payloads) {
    await sendManagedPayload(p, chain, name, log);
    // Upstream's optional payload routine waits 3 seconds after kstuff.
    if (name === "kstuff.elf") await new Promise(resolve => setTimeout(resolve, 3000));
  }
  log("Payload set transferred. Check the console notifications and service output.", "info");
}
''')
    main = managed / 'src' / 'main.js'
    original = main.read_text()
    marker = '    log("elfldr is listening on port 9021", "info");'
    if original.count(marker) != 1:
        raise ValueError('Relapse startup changed; review integration before assembling')
    main.write_text(original.replace(marker, marker + '''
    const { runManagedPayloads } = await import("./managed-payloads.js");
    await runManagedPayloads(p, chain, log);'''))
