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
| OnionHEN | aydencharles/onionHEN, GPL-3.0; unmodified v0.9.0 release, pinned corresponding source archive included |
| Payload Manager | itsPLK/ps5-payload-manager, GPL-3.0; release source included |
| ShadowMountPlus | drakmor/ShadowMountPlus, GPL-3.0; release source included |
| FTP and kernel log servers | ps5-payload-dev/ftpsrv and klogsrv, GPL-3.0-or-later; source included |
| kstuff-lite | EchoStretch/kstuff-lite; upstream has no top-level LICENSE; do not represent it as MIT or GPL without component evidence. Source and pinned crypto submodules included. |
| BearSSL | Official pinned source snapshot, MIT license inside archive |
| libtomcrypt, isa-l_crypto | Their pinned upstream source and notices inside archives |
| Orbit Store | saawant12/orbit-store-ps5, GPL-3.0-or-later; upstream 1.3.5 full source and dependency bundle included |
| ProsperoEden | blackbearreloaded/ProsperoEden, GPL-3.0; unmodified v1.003.000 release ZIP, source at the pinned upstream tag |
| ProsperoStore | blackbearreloaded/ProsperoStore, GPL-3.0-or-later; unmodified v1.000.070 release ZIP, source at the pinned upstream commit |
| PS5 payload SDK | ps5-payload-dev/sdk, GPL-3.0-or-later; pinned rebuild-reference source included |

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
