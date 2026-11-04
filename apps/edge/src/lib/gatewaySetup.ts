import {record,records,label} from './records';
export type SetupCheck={name:string;state:'observed'|'unverified'|'missing';detail:string};
/** Service activity, association and capture are separate observations, never forwarding proof. */
export function gatewayChecks(host:unknown,wifi:unknown,traffic:unknown):SetupCheck[]{
 const h=record(host),w=record(wifi),t=record(traffic),summary=record(t.summary);const services=records(h.services);const has=(name:string)=>services.some(s=>s.name===name&&s.state==='online');const associated=records(w.interfaces).filter(i=>i.connected===true);
 return [
 {name:'WAN association',state:associated.length?'observed':'unverified',detail:associated.length?associated.map(i=>label(i.name)+': '+label(i.connected_ssid,'SSID unreported')).join(', '):'No current association evidence supplied.'},
 {name:'Client access point',state:has('cerberus-hostapd')?'observed':'unverified',detail:has('cerberus-hostapd')?'Host AP service is active. Beacon/client association still requires client evidence.':'Host AP service activity is not established.'},
 {name:'Address allocation',state:has('cerberus-dhcp')?'observed':'unverified',detail:has('cerberus-dhcp')?'DHCP service active; individual leases have not been supplied.':'DHCP activity and client leases are not established.'},
 {name:'Client internet path',state:'unverified',detail:'Requires a selected client lease, route/NAT/DNS observations and a successful client-originated connectivity check.'},
 {name:'Traffic observation',state:summary.status==='running'?'observed':'unverified',detail:summary.status==='running'?'Capture running on '+label(summary.interface)+'. Visibility is limited to this interface; encrypted payloads and all-path coverage are not established.':'No running capture was observed.'},
 {name:'Recovery',state:has('tailscaled')?'observed':'unverified',detail:'Tailscale service '+(has('tailscaled')?'active':'unverified')+'. Its reachability may depend on the uplink being changed; Ethernet may serve downstream clients.'}
 ];
}
export function validateGatewayPlan(uplink:string,ap:string,ssid:string){if(!uplink||!ap)return 'Choose the WAN and AP interfaces.';if(uplink===ap)return 'WAN and AP must use separate verified radios unless concurrent operation is explicitly supported.';if(!ssid.trim()||new TextEncoder().encode(ssid).length>32)return 'AP name must contain 1–32 UTF-8 bytes.';if(/[\x00-\x1f\x7f]/.test(ssid))return 'AP name cannot contain control characters.';return undefined}
