# Third-party software

This assembly preserves the Relapse entry code and its MIT LICENSE, author credits
and firmware-specific loader. Curated downloads replace only independently pinned
payload files; upstream assets are unmodified. Orbit is the unmodified upstream GPL-3.0-or-later release with TorBox support. myfl.uk is not their
original maintainer. The MIT license for this repository applies only to its own
assembly, hosting and tracking code, not to third-party payloads or archives.

The manifest identifies original release tags, full source commits and locally
recorded source-archive checksums. Source archives are served under `/sources/`
from the same host as the payloads. Autoloader submodule source commits are included
as separate archives; use its `.gitmodules` to restore them. Original license and
copyright notices are retained inside those archives.

| Component | Source / terms |
|---|---|
| Relapse | ntfargo/Relapse-Exploit, MIT, source commit in manifest |
| WebKit Autoloader | itsPLK/ps5-webkit-autoloader, GPL-3.0; release source and submodules included |
| LiveShell Engine | ZiZc3/LiveShell, GPL-3.0; unmodified v1.7.0 release and pinned source archive included |
| OnionHEN | aydencharles/onionHEN, GPL-3.0; unmodified v0.9.0 release, pinned corresponding source archive included |
| Payload Manager | itsPLK/ps5-payload-manager, GPL-3.0; release source included |
| ShadowMountPlus | drakmor/ShadowMountPlus, GPL-3.0; release source included |
| FTP and kernel log servers | ps5-payload-dev/ftpsrv and klogsrv, GPL-3.0-or-later; source included |
| kstuff-lite | EchoStretch/kstuff-lite; upstream has no top-level LICENSE; do not represent it as MIT or GPL without component evidence. The served 1.15-dr-test2a build is an operator-supplied test binary with 13.60 fpkg patches and no upstream release; its SHA-256 was computed locally. Source and pinned crypto submodules included for the upstream release line. |
| BearSSL | Official pinned source snapshot, MIT license inside archive |
| libtomcrypt, isa-l_crypto | Their pinned upstream source and notices inside archives |
| Orbit Store | saawant12/orbit-store-ps5, GPL-3.0-or-later; upstream 1.9.7 full source and dependency bundle included |
| ProsperoEden | originally Swordpdf/ProsperoEden then blackbearreloaded/ProsperoEden, GPL-3.0; unmodified v1.005.000 release ZIP, served bytes pinned by hash (see note below) |
| ProsperoStore | darkxex/ProsperoStore, GPL-3.0-or-later; unmodified v1.000.120 release ZIP, source at the pinned upstream commit |
| PS5 payload SDK | ps5-payload-dev/sdk, GPL-3.0-or-later; pinned rebuild-reference source included |

ProsperoEden has no upstream repository left to point at. Both `Swordpdf/ProsperoEden`
and `blackbearreloaded/ProsperoEden` returned HTTP 404 on 2026-11-26, so no tag, source
archive or upstream digest can be cited for it any more. The served
`ProsperoEden-v1.005.000.zip` is byte-identical to the copy published here on
2026-11-09; its SHA-256 was computed locally from those served bytes and is the pin in
`deps.lock.json`, and the download URL now points at this host's own mirror under
`/downloads/`. Treat that hash as an integrity check on a previously published copy,
not as upstream provenance or as a signature from the original author. The v1.003.000
ZIP and the archived source tarball from the removed repository remain published under
`/downloads/` and `/sources/` for reference.

Upstream release binaries do not provide a complete compiler/SDK build receipt.
The included SDK snapshot is a rebuild reference from this project's recorded
SDK pin; it is not a claim to identify the SDK used for each third-party binary.
Do not claim reproducible upstream binaries or a console-tested stack from this
source collection. Archive hashes are recorded locally, not signatures published
by the original maintainers.

The Relapse snapshot also contains upstream bundled helper files with historical
release identities that are not established by its README. Only the curated files
listed on the landing page are recommended as candidates. No ROMs, saves, Sony
runtime files or console dumps are part of this assembly.
