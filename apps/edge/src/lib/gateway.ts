import {getJSON} from './api';
import {record,label} from './records';
export const canonical='https://edge.example.invalid/web/cerberus-edge/index.html';
export async function edgeWrite(path:string,payload:unknown){
 let session:Record<string,unknown>;
 try{session=record(await getJSON('/api/edge/session'))}catch{throw new Error('This action needs the complete Tailscale HTTPS interface and an active login.')}
 if(typeof session.csrf!=='string')throw new Error('The authenticated action token is unavailable.');
 let response:Response;
 try{response=await fetch('/api/edge/'+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Cerberus-CSRF':session.csrf},body:JSON.stringify(payload),signal:AbortSignal.timeout(path==='insights/explain'?70000:25000)})}catch{throw new Error('The response was lost. Check the receipt/history before retrying; completion may be uncertain.')}
 if(response.redirected||response.status===401)throw new Error('Your session expired. Sign in again.');
 if(!(response.headers.get('content-type')||'').includes('json'))throw new Error('Invalid action response. Inspect state before retrying.');
 const data=record(await response.json());if(!response.ok){if(typeof window!=='undefined')window.dispatchEvent(new CustomEvent('cerberus-action-result',{detail:data.completion==='unknown'||data.state==='unknown'||response.status>=500?'unknown':'rejected'}));throw new Error(label(data.detail||data.error,'Action failed with HTTP '+response.status))}if(typeof window!=='undefined')window.dispatchEvent(new CustomEvent('cerberus-action-result',{detail:data.state==='verified'||data.durable===true||data.status==='completed'?'verified':'accepted'}));return data;
}
