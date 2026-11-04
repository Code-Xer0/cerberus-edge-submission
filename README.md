# Cerberus Edge

An evidence-first operator console for a Raspberry Pi network-security appliance. The interface puts source observations, model explanations and human decisions in separate, inspectable layers. Built with Vite, React and TypeScript; presentation and animation run on the viewing client.

## What is new here

Six operator workspaces; situation brief; evidence-backed inventory/topology; saved model provenance; durable action receipts; conversation/history integration; a scoped recording projection; weighted controls, motion and licensed interface sound; and a same-origin adapter that validates existing Ragnar sessions and CSRF-protects writes. The adapter exposes bounded operations rather than arbitrary commands. Reviewed Meta explanations are server-side and explicit—opening the interface does not request paid inference.

The running appliance integrates the existing Ragnar/Bjorn sensor runtime and a separate private Cerberus endpoint. This repository contains the new interface and adapter, not those applications. It is not a claim that the upstream sensor runtime was authored during the hackathon. See [contribution and dependency disclosure](THIRD_PARTY_NOTICES.md).

## Reproducible frontend build

Node 22+ and npm:

```sh
cd apps/edge
npm ci
npm run build
npm run test:contracts
npm run test:ui
npm run dev -- --host 127.0.0.1
```

Open the URL printed by Vite. An unconnected checkout displays explicit source-unavailable states. It does not manufacture live devices, attacks or model output. The public source uses original vector stand-ins; private recording artwork is not distributed.

## Integration boundary

`services/edge-gateway` is a loopback aiohttp adapter. Set `CERBERUS_EDGE_ORIGIN` to the deployment origin and `CERBERUS_RAGNAR_COOKIE_NAME` to the existing runtime cookie name. Its fixed upstreams are Ragnar on loopback 8000 and the separately installed endpoint on loopback 8766; the adapter listens on 8767. Supply any provider credentials through server-side service credentials, never browser storage. See the source tests for the expected route contracts. The upstream applications and appliance network provisioning are deployment prerequisites, not installed by this repository.

```sh
python3 -m venv .venv
.venv/bin/pip install -r services/edge-gateway/requirements.txt
.venv/bin/python -m unittest discover -s services/edge-gateway
```

Do not point this development checkout at a production gateway without reviewing authentication, origin, service policy, recovery and upstream licenses. No AP/firewall commissioning is performed by the public frontend build.

## Honest demo boundaries

The action-based recording path uses actual authenticated host observations, retained inventory and a verified Meta `muse-spark-1.3` response generated through the review dialog. The result remains inspectable as a saved receipt. It does not claim local Glimmer inference. The A7500 demonstration is a dated AP validation, not proof of receive-only passive IDS. The scoped recording view masks selected presentation surfaces; the full engineering interface, developer tools and browser chrome are outside its privacy guarantee. Operational writes and raw exports are omitted from the recording flow.

## Release scope

This fresh public repository excludes the private application's history, credentials, host snapshots, packet captures, operational logs and uncleared artwork. It is not a flashable appliance image or full runtime distribution. Publication does not establish competition eligibility or grant rights to omitted/upstream software.

The private endpoint route-inventory integration test is excluded because that endpoint source is not distributed here. The included gateway, broker and frontend suites cover their isolated boundaries; they do not establish live radio/enforcement acceptance.

## Pitch assets

[Video kit](video-kit/README.md): editable 1080p cards, transparent lower-thirds and a silent four-second MP4 title bumper. These are presentation graphics, not manufactured telemetry or interface recordings.

## Full-interface recording

The optional `/recording` entry now leads through the existing login into the complete operator UI (`?operator=1#home`), not the older read-only presentation scenes. This full interface displays private operational identifiers: blur them in an edited recording. Its header Sign Out uses an explicit browser-session review and preserves appliance monitoring. The old scoped view is not a substitute for demonstrating the working controls. A refreshed signed cookie retains its CSRF review binding to the validated login; a new login has a separate binding.

The latest full-interface verification completed a reviewed Meta explanation and a durable operator acknowledgment. Two separately reviewed local Glimmer requests timed out at the current provider bound; local inference is not an accepted demo claim. The production AP was preserved, and no receive-only monitoring claim is made. Video recording, upload and owner eligibility/terms review remain separate from source publication.
