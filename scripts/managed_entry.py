"""Assemble post-loader orchestration; leave upstream exploit code unchanged."""
import ast
import base64
import io
import json
from pathlib import Path
import shutil
import zipfile

# Canonical transfer order. The start page can only select from this list.
PAYLOADS = ['klogsrv-ps5.elf', 'kstuff.elf', 'shadowmountplus.elf', 'ftpsrv-ps5.elf', 'orbit-torbox.elf', 'OnionHEN.elf']
LABELS = {
    'klogsrv-ps5.elf': 'Kernel log server',
    'kstuff.elf': 'kstuff-lite kernel patches',
    'shadowmountplus.elf': 'ShadowMountPlus',
    'ftpsrv-ps5.elf': 'FTP server',
    'orbit-torbox.elf': 'Orbit with TorBox',
    'OnionHEN.elf': 'OnionHEN',
}
# The Linux loader needs the ELF loader alone: kstuff and a HEN stop the console
# from entering rest mode, which is how the loader hands over to Linux.
LINUX_WARNINGS = {
    'kstuff.elf': 'Keep off for Linux: the console freezes instead of entering rest mode.',
    'OnionHEN.elf': 'Keep off for Linux: the console freezes instead of entering rest mode.',
}
PROFILES = {'ps5': PAYLOADS, 'linux': []}

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
    (managed / 'src' / 'selection.js').write_text('''// Generated from the pinned payload list; the start page selects within it.
export const PAYLOADS = ''' + json.dumps(PAYLOADS) + ''';
export const PROFILES = ''' + json.dumps(PROFILES) + ''';
export function selectPayloads(search) {
  const params = new URLSearchParams(search || "");
  const explicit = params.has("load");
  const profile = params.get("profile") || (explicit ? "custom" : "ps5");
  if (!explicit) {
    const fallback = Object.prototype.hasOwnProperty.call(PROFILES, profile) ? PROFILES[profile] : PAYLOADS;
    return { profile, payloads: fallback.slice() };
  }
  const wanted = new Set(params.get("load").split(",").map(name => name.trim()));
  return { profile, payloads: PAYLOADS.filter(name => wanted.has(name)) };
}
''')
    (managed / 'src' / 'managed-payloads.js').write_text('''import { sendManagedPayload } from "./kexp.js";
import { selectPayloads } from "./selection.js";
// The start page passes the chosen files in ?load=; nothing else is transferable.
export const selection = selectPayloads(location.search);
export async function runManagedPayloads(p, chain, log) {
  if (!selection.payloads.length) {
    log("No extra payloads selected: Relapse only, ELF loader on port 9021.", "info");
    return;
  }
  log("Starting the myfl payload set (" + selection.payloads.length + " files, " + selection.profile + ")", "info");
  for (const name of selection.payloads) {
    await sendManagedPayload(p, chain, name, log);
    // Upstream's optional payload routine waits 3 seconds after kstuff.
    if (name === "kstuff.elf") await new Promise(resolve => setTimeout(resolve, 3000));
  }
  log("Payload set transferred. Check the console notifications and service output.", "info");
}
''')
    page = managed / 'index.html'
    html = page.read_text()
    banner = '''<div id="myfl-profile"></div>
<script>
(function () {
  var params = new URLSearchParams(location.search);
  var raw = params.get("load");
  var names = raw === null ? null : raw.split(",").filter(Boolean);
  var box = document.getElementById("myfl-profile");
  if (!box) return;
  box.style.cssText = "padding:10px 14px;font:14px/1.4 system-ui,-apple-system,'Segoe UI',sans-serif;background:#111418;color:#a7adb8;border-bottom:1px solid #2a2f36";
  if (params.get("profile") === "linux" || (names && !names.length))
    box.textContent = "Linux profile: Relapse only, no kstuff or HEN. When the exploit finishes, send ps5-linux-loader.elf to port 9021 from your computer, then let the console enter rest mode.";
  else if (names)
    box.textContent = "PS5 profile: Relapse, then " + names.length + " selected payload(s).";
  else
    box.textContent = "PS5 profile: Relapse, then the default payload set.";
})();
</script>
'''
    if html.count('<body>') != 1:
        raise ValueError('Relapse page changed; review integration before assembling')
    page.write_text(html.replace('<body>', '<body>\n' + banner, 1))
    main = managed / 'src' / 'main.js'
    original = main.read_text()
    marker = '    log("elfldr is listening on port 9021", "info");'
    if original.count(marker) != 1:
        raise ValueError('Relapse startup changed; review integration before assembling')
    main.write_text(original.replace(marker, marker + '''
    const { runManagedPayloads } = await import("./managed-payloads.js");
    await runManagedPayloads(p, chain, log);'''))
