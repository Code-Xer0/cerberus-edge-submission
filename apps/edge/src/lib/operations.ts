import {edgeWrite} from './gateway';
import {record,records,label} from './records';
export type Receipt={state:'verified'|'unverified';message:string;at:string};
export async function executeCapture(action:'start'|'stop',interfaceName:string,send:(path:string,body:unknown)=>Promise<unknown>,read:()=>Promise<unknown>,pause:(ms:number)=>Promise<void>):Promise<Receipt>{
 if(action==='start'&&!/^[a-zA-Z0-9_.:-]{1,32}$/.test(interfaceName))throw new Error('Choose an observed interface.');
 const result=record(await send('/api/traffic/'+action,action==='start'?{interface:interfaceName}:{}));
 if(result.success!==true)throw new Error(label(result.error||result.message,'The runtime rejected the request.'));
 for(let attempt=0;attempt<6;attempt++){
  if(attempt)await pause(2000);
  try{const response=record(await read());const summary=record(response.summary);if(response.success===true&&summary.status===(action==='start'?'running':'stopped')&&(action==='stop'||summary.interface===interfaceName))return {state:'verified',message:action==='start'?'Capture is running on '+interfaceName+'.':'Capture is stopped.',at:new Date().toISOString()}}catch{/* Acknowledgement remains unverified; do not retry the write. */}
 }
 return {state:'unverified',message:'The runtime accepted the request, but its resulting state could not be verified. Refresh status before retrying.',at:new Date().toISOString()};
}
export async function postRuntime(path:string,body:unknown):Promise<unknown>{
 if(!['/api/traffic/start','/api/traffic/stop'].includes(path))throw new Error('Operation is not allowlisted.');
 return edgeWrite('capture/'+path.split('/').at(-1),body);
}

export function observedAlerts(value:unknown){const d=record(value);if(d.success!==true)throw new Error('The watcher did not provide a valid result.');return records(d.alerts).map(a=>({id:typeof a.key==='string'?a.key:undefined,title:label(a.title,'Untitled observation'),severity:label(a.severity,'unknown'),source:label(a.source,'Unknown source'),at:typeof a.ts==='number'?new Date(a.ts*1000).toISOString():undefined,target:label(a.target||a.src,'Not reported')}))}
export function networkInsights(traffic:unknown,watcher:unknown){const t=record(traffic),s=record(t.summary),w=record(watcher);const output:Array<{title:string;detail:string}>=[];
 if(t.success===true){if(s.status==='stopped')output.push({title:'Traffic capture is stopped',detail:'Traffic-derived insights cannot reflect current packets until capture is started on an appropriate interface.'});else if(s.status==='running')output.push({title:'Capture is running on '+label(s.interface),detail:label(s.total_packets,'Unreported')+' packets and '+label(s.active_connections,'unreported')+' active connections reported. These are observations, not a safety verdict.'});if(typeof s.unacknowledged_alerts==='number'&&s.unacknowledged_alerts>0)output.push({title:s.unacknowledged_alerts+' traffic alerts need review',detail:'Inspect the sensor findings and source evidence before deciding on any response.'})}
 if(w.success===true){output.push({title:w.enabled===true?'Watchtower aggregation is enabled':'Watchtower aggregation is disabled',detail:'A watcher setting does not prove that every sensor is operating.'});const alerts=observedAlerts(w);if(alerts.length)output.push({title:alerts.length+' watcher observations returned',detail:'The returned feed can include historical findings. Review individual source timestamps.'})}
 return output;
}
