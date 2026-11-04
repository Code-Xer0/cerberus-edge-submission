import {edgeData} from './compatibility';
import {useCallback,useEffect,useRef,useState} from 'react';
export type Result={data?:unknown;error?:string;at?:number;url?:string;stale?:boolean;attemptedAt?:number;httpStatus?:number};
export class ApiError extends Error{constructor(message:string,public status:number){super(message)}}
export async function getJSON(url:string):Promise<unknown>{const r=await fetch(url,{credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(8000)});if(r.status===401||(r.redirected&&new URL(r.url).pathname==='/login'))throw new ApiError('Your session is unavailable or expired. Sign in to Ragnar to continue.',401);if(r.status===403)throw new ApiError('Your account is not authorized to view this source.',403);if(!r.ok)throw new ApiError(r.status===404?'This edge capability has not been delivered.':'Request failed ('+r.status+').',r.status);if(!(r.headers.get('content-type')||'').includes('json'))throw new Error('The service did not return JSON.');return r.json()}
export function failedResult(previous:Result,url:string,error:unknown,now=Date.now()):Result{
 const message=error instanceof Error?error.message:'Service unavailable.';
 if(error instanceof ApiError&&[401,403].includes(error.status))return {url,error:message,attemptedAt:now,httpStatus:error.status};
 return {...(previous.url===url?previous:{}),url,error:message,stale:previous.url===url&&previous.data!==undefined,attemptedAt:now};
}
export function useResult(url?:string,intervalMs=30000){
 const [stored,setValue]=useState<Result>({});const [loading,setLoading]=useState(false);const request=useRef(0);const inFlight=useRef<number|undefined>(undefined);
 const refresh=useCallback(async()=>{
  if(inFlight.current!==undefined)return;
  const current=++request.current;if(!url){setValue({});setLoading(false);return}inFlight.current=current;setLoading(true);
  try{const data=await edgeData(url,getJSON,error=>error instanceof ApiError&&error.status===404);if(current===request.current)setValue({data,at:Date.now(),url})}
  catch(e){if(current===request.current)setValue(previous=>failedResult(previous,url,e))}
  finally{if(inFlight.current===current)inFlight.current=undefined;if(current===request.current)setLoading(false)}
 },[url]);
 useEffect(()=>{void refresh();const visible=()=>{if(!document.hidden)void refresh()};document.addEventListener('visibilitychange',visible);const timer=url?window.setInterval(visible,intervalMs):undefined;return()=>{request.current++;inFlight.current=undefined;document.removeEventListener('visibilitychange',visible);if(timer)window.clearInterval(timer)}},[refresh,url,intervalMs]);
 const value=stored.url===url?stored:{};return{value,loading,refresh};
}
