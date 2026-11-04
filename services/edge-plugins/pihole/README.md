# Pi-hole DNS manager / control broker

This optional Cerberus plugin manages an existing Pi-hole v6 service. It does not insert a new DNS proxy, change port 53, DHCP, upstream resolvers, forwarding or gateway policy.

The server-side Edge adapter exposes authenticated status and bounded exact-domain policy. Writes require the Ragnar session, same-origin CSRF, an account-bound expiring review, native Pi-hole command execution, actual readback and a durable receipt. Models have no access to this control surface.

## Architecture

`Browser → authenticated Edge gateway → private HTTPS broker → installed Pi-hole CLI → Pi-hole API`

Install the broker **inside the existing Pi-hole container**, not as a general command runner on the virtualization host. The broker invokes the installed `/usr/local/bin/pihole` with fixed argument arrays. It uses Pi-hole's existing local CLI authentication; admin passwords and sessions are never copied to the browser or returned by the broker. The shared `services/edge-gateway/pihole_policy.py` must be installed alongside `broker.py` so both sides enforce identical action/name bounds.

The broker requires a separate random bearer credential, loaded through systemd credentials on both ends. Expose it only through the existing private network using verified HTTPS. Preserve any prior Tailscale Serve handlers; never enable Funnel. If the node cannot resolve MagicDNS, the Edge adapter can pin the trusted tailnet address while retaining the broker hostname for TLS SNI, certificate validation and Host routing. Do not disable certificate verification.

Root-owned Edge service settings:

- `CERBERUS_PIHOLE_BROKER_URL`: fixed HTTPS origin, no path, query, password or userinfo.
- `CERBERUS_PIHOLE_BROKER_IP`: optional pinned management address.
- `LoadCredential=pihole-broker:<private credential file>`.

Broker configuration:

- `CERBERUS_DNS_BIND`: existing private container address, not a new public listener.
- `LoadCredential=broker-token:<private credential file>`.
- `/v1/status`, `/v1/domains`, `/v1/domain?name=<validated exact name>`, `/v1/actions`. All require the broker credential. No arbitrary upstream, shell, filesystem, config, resolver or service-lifecycle route exists.

## Controls and evidence limits

- Enable filtering.
- Pause filtering for **30, 60 or 300 seconds** using Pi-hole's native timer. The UI defaults to 60 seconds. Pausing an already disabled service is rejected; it cannot silently extend a previous pause. A verified pause receipt requires disabled readback plus a positive bounded provider timer.
- Add/remove exact allow/deny entries through the installed CLI. Names are canonical IDNA FQDNs, not IPs, URLs, shell fragments, wildcards or regex. The review binds the previous policy state; a concurrent change is rejected. Adding a deny entry while an exact allow exception exists is rejected.
- Policy list shows up to 200 entries per exact type; direct target readback checks are not limited to that list window. Default-group assignment and native Pi-hole precedence apply. A stored entry does not prove any particular client query was blocked.
- Aggregate counters are projected through an allowlist. Raw query logs, client names, credentials, upstream configuration, regex/group edits, gravity updates and service restarts are excluded.
- The existing DNS hairpin can merge AP clients under a NAT identity. Pi-hole client counts are not verified appliance/device counts.
- A timeout means uncertain completion. The same review ID is not executed twice; inspect actual filtering/policy and receipts before another action. Domain recovery uses an explicit inverse action; a temporary filtering pause uses the native timer.

## Attribution and tests

The plugin is new Edge integration code; Pi-hole remains an external installed dependency with its existing notices and licenses. No vendor scripts are bundled or rewritten. Source behavior was verified against the installed CLI and the [Pi-hole API documentation](https://docs.pi-hole.net/api/), [authentication documentation](https://docs.pi-hole.net/api/auth/) and [CLI documentation](https://docs.pi-hole.net/main/pihole-command/).

Tests cover input bounds, fixed CLI argument lists, pause timer readback, policy conflict handling, credential/query-name minimization, authenticated routes, durable replay and unknown completion. Live policy writes must be reported separately from simulated contract tests. Deployment itself must not pause filtering or alter domain policy.

Rollback: disable only the newly added private HTTPS listener, stop this broker, and remove its optional Edge service drop-in after selecting the previous gateway source. Keep Pi-hole/FTL, DNS hairpin, DHCP and gateway services running. Preserve the private DNS action ledger and credentials for recovery; do not export them with source.
