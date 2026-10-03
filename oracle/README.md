# Oracle service operation

## Deployed layout — 3 October 2026

The existing public Caddy listener routes only the Oracle public-IP HTTP host,
`exploit.myfl.uk`, and both `manuals.playstation.net` / `manuals.playstation.com` to this project's loopback Nginx
origin. The resource site stays on Cloudflare Pages at myfl.uk. Other Caddy sites
are preserved; the tailnet Caddy and DNS services are separate.

Compose project `myfl-ps5` runs a read-only static origin and a restricted DNS
server. The public DNS binds only the verified primary private interface, mapped
by OCI to the existing public IP. No VNIC, OCI rules or existing domain records
were changed; two DNS-only A records were added for the new subdomains.

The runtime uses pinned upstream image digests. CoreDNS is copied through a plain
`cp` stage into scratch to remove the upstream port-53 file capability: it listens
on container port 1053 and runs with **all capabilities dropped**. Both services
use unprivileged users, no-new-privileges, default seccomp/AppArmor, read-only
roots, bounded memory/CPU/PIDs and bounded local logs. No host/Docker socket,
vault credential or writable host source mount is present.

## Firewall and ingress

`firewall.sh` changes only its own chains plus bridge-scoped jumps. It refuses
fragmented/malformed DNS traffic; UDP has a 600-byte request bound, 20 queries/s
per source and 300/s total limits. TCP has per-source connection/SYN limits and
a total SYN limit. It denies NEW connections from the project bridge to the
host and outside destinations, except TCP port 53 to 1.1.1.1 and 1.0.0.1.
OCI metadata and other workloads remain blocked.
The bridge is not Docker's internal mode because that mode prevented published
ports on this engine. The scoped firewall supplies the egress restriction.

Nginx accepts only GET/HEAD, has no directory listing, serves real 404 responses,
limits connections and per-client/global request rates, and bounds request sizes
and timeouts. Caddy replaces the private client-key header with the socket peer;
the origin is only published on loopback. Caddy TLS termination remains part of
the shared ingress boundary; a separate VM offers stronger kernel isolation.

The DNS redirects both User’s Guide zones. Other names
are forwarded to two fixed upstreams over TCP with 32 concurrent queries,
a bounded cache and a 512-byte EDNS size. The known update.playstation.net
branch returns NXDOMAIN. Ordinary domains resolve through the upstreams. Resource bounds and traffic limits reduce
abuse; they do not guarantee protection from volumetric attacks upstream of OCI.

## TLS/User’s Guide acceptance

The source-confirmed `/document/<language>/ps5/` paths map to the managed Relapse tree,
including its relative source and payload URLs. A locally generated RSA certificate
serves only `manuals.playstation.net`; it is not publicly trusted, and it is not
an upstream shared private key. Console certificate acceptance remains [UNKNOWN].
Normal `exploit.myfl.uk` uses a publicly trusted certificate managed by Caddy.
Do not claim that a host HTTPS request with verification disabled proves PS5
acceptance. Test the actual User’s Guide route on 13.60 and record the full tuple.
The local guide certificate needs renewal before its recorded expiry; keep its
private key in the root/Caddy-only server directory, never in Git or a receipt.

## Server-only configuration

The verified private interface/bind values and loopback origin port live in an
ignored server `.env`. The Caddy fragment template is rendered on the host with
verified deployment addresses. Do not attach that private configuration to a
public issue. Compose and source files live at `/opt/myfl-ps5` on Oracle.

The installation uses `myfl-ps5-firewall.service`, `myfl-ps5.service` and a daily
`myfl-ps5-analytics.timer`. Firewall ordering precedes stack startup. On-failure
container retries are capped; the stack's unit handles boot startup.

```sh
cd /opt/myfl-ps5/oracle
docker compose ps
docker compose logs --tail=30
dig @130.162.174.95 manuals.playstation.net
dig @130.162.174.95 manuals.playstation.net +tcp
dig @130.162.174.95 example.org       # expect REFUSED, recursion unavailable
```

## Private analytics

Nginx emits time, path without query, status, bytes and duration. Access logs omit
client IP, user agent, referrer and cookies; DNS query logging is disabled.
Operational error logs can contain connection details: restrict/sanitize them.
Docker caps each service's raw logs at three 5 MB files; rotation is size-based.
Daily aggregate JSON files in `/var/lib/myfl-ps5-analytics` expire after seven days.
DNS counters cover the current container lifetime, while HTTP summaries cover
available logs from the last 24 hours; size rotation may shorten that coverage.
Counters are requests, not unique users, console identities or jailbreak results.

CoreDNS's metrics listener is available only inside the private container network;
it is not published. The host collector reads it directly. Existing Grafana/Loki
configuration is unchanged; these private JSON snapshots can be integrated later.

## Update and rollback

Review the candidate PR, build and hash-check the full new version, test both console
paths, then stage a new release directory and atomically switch serving content.
Keep the previous directory. Do not mutate a live file tree while publishing a
new candidate. No scheduled job deploys candidates automatically.

For service rollback, disable the three myfl systemd services/timer, then stop
**only** this Compose project, remove only its three
Caddy blocks and validate/reload Caddy, then remove only the two new Cloudflare A
records if retiring the service. Backups of the pre-change Caddy file and firewall
receipt are held privately on Oracle. Preserve unrelated config added since those
backups; do not blindly restore an old whole-server config.
Remove bridge-scoped jumps and MYFL-PS5-IN / MYFL-PS5-OUT chains only after stopping the
containers. Never flush firewall tables, prune Docker broadly or restart other
services. Console users restore original DNS and cached payload files separately.

## Required physical-console test

1. Fully boot a 13.60 console with updates disabled; save original DNS settings.
2. Set DNS to the verified public endpoint and open User’s Guide; record certificate
   result, requested paths, chain result and exact resident loader identity.
3. Verify a small payload notification/response, then each required curated service.
   Load kstuff only after full boot and before dependent registration tools.
4. Install WebKit Autoloader deliberately; reboot once and run its homescreen route
   with network interface active. Verify its console-only loader and payload files.
5. Record full firmware/model/source/loader/SDK/patch/HEN/helper/hash tuples and
   expected/observed results. Test recovery and rollback. A download is not execution.

## Primary references

[MAINTAINER-DOC] Reviewed 2026-10-03:
[Docker firewall behavior](https://docs.docker.com/engine/network/packet-filtering-firewalls/),
[CoreDNS file plugin](https://coredns.io/plugins/file/),
[Caddy TLS](https://caddyserver.com/docs/caddyfile/directives/tls),
[OCI security rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm).
