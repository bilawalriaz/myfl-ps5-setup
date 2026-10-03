# myfl.uk PS5 setup

A tracked assembly of the original Relapse entry and selected payloads for a
retail PS5 on firmware **13.60**, with a separate WebKit Autoloader setup.

- Resource site and beginner guide: https://myfl.uk
- Hosted setup: https://exploit.myfl.uk (also http://130.162.174.95)
- Restricted DNS endpoint: **130.162.174.95** (`dns.myfl.uk`)

## First use

1. Read the beginner guide and confirm firmware 13.60. Fully boot the console.
2. Use the direct hosted Relapse link if you already have a console-browser entry.
   For a User’s Guide trial, set the console DNS to the endpoint above and open
   the User’s Guide from Settings. Set both DNS fields to the endpoint. This redirects both guide hostnames,
   resolves PlayStation and myfl.uk names, and refuses unrelated domains.
   The known update.playstation.net branch returns NXDOMAIN. Some apps may fail to resolve. Restore your
   original DNS when finished.
3. After the chain runs, load only the payloads your app needs. The hosted Relapse
   code is unchanged and does not automatically run all curated extras.
4. To install the homescreen WebKit Autoloader, send the pinned installer ELF
   after the first jailbreak and follow its upstream reboot instructions. Its
   cached entry, local payload files and default console-only loader are distinct
   from the hosted direct Relapse setup.

## What the assembly produces

`deps.lock.json` identifies the upstream Relapse commit, loader-containing source
archive, separate payload release assets and sixteen pinned source archives.
Checksums for source archives are locally recorded; binary asset digests were
reported by GitHub and verified after downloading.

- `dist/relapse/` preserves original exploit code, MIT notice and loader.
  Curated kstuff, ShadowMountPlus, FTP, klog, Payload Manager and WebKit Autoloader
  installer ELF files are copied into its **payloads/** folder.
- `dist/autoloader/ps5_autoloader/` contains the same selected routine payloads.
  No heavy boot list is shipped: Payload Manager remains the initial default.
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

## Upstream sources reviewed 3 October 2026

[MAINTAINER-DOC] Relapse documents 7.00–13.60 and loader port 9021. The WebKit
Autoloader documents initial PC/User’s Guide setup, cached updates, USB priority,
Payload Manager and its console-only loader. Full source commits, tags, archive
URLs and hashes are in the manifest; original maintainer links appear on the host.

This repository’s MIT license applies only to its own code. Third-party terms
and source/build provenance limitations are recorded in THIRD_PARTY.md.
