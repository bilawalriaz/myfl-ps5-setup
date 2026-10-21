# myfl.uk PS5 setup

A tracked assembly of the original Relapse entry and selected payloads for a
retail PS5 on firmware **13.60**, with a separate WebKit Autoloader setup.

- Resource site and beginner guide: https://myfl.uk
- Hosted setup: https://exploit.myfl.uk (also http://130.162.174.95)
- DNS endpoint: **130.162.174.95** (`dns.myfl.uk`)

## First use

1. Read the beginner guide and confirm firmware 13.60. Fully boot the console.
2. Use the direct hosted Relapse link if you already have a console-browser entry.
   For a User’s Guide trial, set the console DNS to the endpoint above and open
   the User’s Guide from Settings. Set both DNS fields to the endpoint. This redirects both guide hostnames,
   resolves PlayStation and myfl.uk names, and resolves other domains normally.
   The known update.playstation.net branch returns NXDOMAIN.  Restore your
   original DNS when finished.
3. Opening the User’s Guide shows the start page, not the exploit. Pick
   **Normal PS5** (Relapse plus the ticked payloads) or **PS5 Linux** (Relapse
   only, for the loader on port 9021), clear any payload you do not want, then
   press Start. Nothing runs until Start is pressed. `/managed/` without a query
   keeps the reviewed PS5 set; `/relapse/` stays Relapse-only.
4. To install the homescreen WebKit Autoloader, send the pinned installer ELF
   after the first jailbreak and follow its upstream reboot instructions. Its
   cached entry, local payload files and default console-only loader are distinct
   from the hosted direct Relapse setup.

## What the assembly produces

`deps.lock.json` identifies the upstream Relapse commit, loader-containing source
archive, separate payload release assets and pinned source archives.
Checksums for source archives are locally recorded; binary asset digests were
reported by GitHub and verified after downloading.

- `dist/start/index.html` is the User’s Guide chooser, rendered from the pinned
  payload list. It is a classic page with no external assets, and it only builds
  the `/managed/?profile=…&load=…` link. The selection is an allowlist: an
  unknown or foreign file name is dropped and the canonical transfer order is
  kept. An empty `load` list is the Linux profile and transfers nothing.
- `dist/relapse/` preserves original exploit code, MIT notice and loader.
  Curated kstuff, ShadowMountPlus, FTP, klog, Payload Manager and WebKit Autoloader
  installer ELF files are copied into its **payloads/** folder.
- `dist/autoloader/ps5_autoloader/` contains the same selected routine payloads.
  Its autoload.txt starts the same six services. Download autoloader.zip,
  extract the folder and launch the homescreen app after full boot.
- `dist/downloads/` contains original selected release downloads/PC host.
- `dist/sources/` contains release source archives and pinned submodule archives.
- `dist/manifest.json` and `SHA256SUMS` record exact candidate bytes for rollback.

Payload Manager is named `pldmgr.elf` in the runtime payload folders to match
upstream autoload conventions. The installer is never part of a boot list.
The Relapse snapshot also contains historical helper files; their embedded release
identity is not established by its README. Only the curated landing-page entries
are selected candidates. See [third-party notices](THIRD_PARTY.md).

## Build and verify on a computer

Python 3, Git and `gh` are needed; the PS5 SDK and a console are not needed:

```sh
python3 scripts/test_build.py
python3 scripts/track.py
python3 scripts/build.py
```

The builder verifies each digest, rejects traversal/symlinks/special archive files
and validates x86-64 ELF section bounds. It refuses an existing `dist/`: move your
previous candidate aside explicitly and keep it for rollback. Generated artifacts,
private config, raw logs and secrets are ignored. No Sony runtime, game data,
saves or console dumps belong in this project.

## Updates

The daily GitHub workflow reports upstream changes. A new upstream Relapse commit
or newer stable payload release creates a **candidate pull request** with verified
asset digests and refreshed source archive pins. Ambiguous asset matches fail for
manual review; new prereleases and same-tag mutations are reported separately.
Nothing is auto-merged, promoted or deployed. GitHub must allow Actions to create
pull requests for that workflow step to succeed.

Review release notes and load order, build the candidate, then test both entry paths
on fresh 13.60 boots before promoting a stable version. Record firmware/model,
exploit/loader/SDK/patch/HEN/helper versions, hashes, commands, expected/observed
results, logs and recovery. Keep a complete previous release and promote the whole
new directory atomically instead of changing individual serving files.

Offline autoloader users must run the updated installer and replace their payload
files separately. The upstream installer preserves `autoload.txt` and payloads;
it does not update them. An installed-manifest updater is not implemented here.

## Hosting

See [Oracle operation and rollback](oracle/README.md). Application containers run
without root, capabilities, host/Docker sockets or writable source mounts. Scoped
firewall rules allow DNS traffic to the two fixed upstreams and block other new
container connections. DNS and HTTP request rates are limited.

Access logs omit client IPs, query strings, cookies and user agents. DNS query
logging is disabled. Private daily HTTP aggregates and DNS response counters are
retained seven days; raw operational logs are size-capped and rotate. Counts are
requests, not unique people or successful jailbreaks.

The User’s Guide paths serve the `dist/start/` chooser; the exploit tree is only
served, never started by the guide entry. Micro hosts the same tree for the LAN and
serves its guide page from `/opt/ps5-host/redirect`, rendered with the LAN origin:

```sh
python3 scripts/start_page.py --origin http://192.168.1.152 \
  --output /opt/ps5-host/redirect/index.html
```

## Upstream sources reviewed 21 October 2026

[MAINTAINER-DOC] Relapse documents 7.00–13.60 and loader port 9021. The WebKit
Autoloader documents initial PC/User’s Guide setup, cached updates, USB priority,
Payload Manager and its console-only loader. Full source commits, tags, archive
URLs and hashes are in the manifest; original maintainer links appear on the host.

This repository’s MIT license applies only to its own code. Third-party terms
and source/build provenance limitations are recorded in THIRD_PARTY.md.

## Payload Manager catalogue

In Settings > Manage Sources > Add Source, add
https://exploit.myfl.uk/payloads.json . The catalogue is generated from the pinned
asset manifest and includes SHA-256 download verification. Choose myfl.uk PS5
essentials to browse/download. Autoload is a separate list of installed payloads
to launch; clearing it does not delete the hosted pack.

## Orbit and TorBox

Both Micro and Oracle start Orbit with TorBox after the core payloads. Open the installed Orbit TV app once startup finishes. The hosted payload does not install the TV app.

The payload catalogue offers official Orbit 1.3.5 with TorBox support. Run one Orbit service per boot. The automatic list uses that upstream service. Open Orbit in a browser, then App settings > TorBox to enter your own key. Keys stay in `/data/orbit-store/debrid.json` on the console; hosted payloads and sources contain no account settings.

[orbit.lock.json](orbit.lock.json) pins the service, TV app 1.7.0 and full upstream source bundle. Builder downloads verify the GitHub release asset SHA-256 values.

WebKit Autoloader v0.6.1 is available as a separate installer download. The hosted entry keeps its v0.5.2 transfer routines. Installers update the homescreen entry; they do not replace saved payload files.

The `orbit-torbox.elf` filename is retained for existing autoload lists; its bytes are the official Orbit 1.3.5 release. Download `/downloads/PPSA99177.ffpkg` for the matching TV app.

After updating the download service, choose Stop Orbit in App settings, then close and reopen the TV app. The replacement starts after the old service exits. To restart manually, load `/data/orbit-store/orbit_store.elf` from your payload manager.

## ProsperoStore

Download the ProsperoStore ZIP from the install page, extract `PPSA99000`, and copy that folder to `/data/homebrew/PPSA99000`. ShadowMountPlus registers the home-screen icon during its scan. ProsperoStore needs ShadowMountPlus 1.7beta4 or newer and the local ELF loader on TCP 9021. This native app is a separate download; it is not part of the automatic ELF list.

[prosperostore.lock.json](prosperostore.lock.json) pins the v1.000.070 release ZIP and source archive. The builder checks both SHA-256 values.

## ProsperoEden

The hosted downloads include the pinned ProsperoEden v1.003.000 app ZIP. Extract it and copy its `PPSA99008` folder to `/data/homebrew/PPSA99008`; ShadowMountPlus scans and registers the app. The managed exploit starts the payload services, then return to the home screen and open ProsperoEden. Its bundled Lapy helper runs when the app needs it, so it is not part of the automatic ELF list. The console's ELF loader on TCP 9021 must be available for the app's update feature.


## OnionHEN

Managed startup loads OnionHEN v0.9.0 once, after Orbit. Open Settings when
startup finishes to use its toolbox, cheats and overlay. The earlier kstuff
step supplies kernel patches; OnionHEN detects it and skips its bundled copy.
The autoloader ZIP uses the same order. Do not load etaHEN alongside OnionHEN.
Restart before switching HEN setups. Keep FTP and ShadowMountPlus as the
separate services supplied in this bundle.
