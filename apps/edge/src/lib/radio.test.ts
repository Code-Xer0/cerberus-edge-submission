import {describe,expect,it,vi} from 'vitest';
import {edgeData} from './compatibility';
import {ApiError} from './api';
const miss=(e:unknown)=>e instanceof ApiError&&e.status===404;
describe('radio compat',()=>{
 it('maps /api/edge/radio events into the PackRadio feed shape',async()=>{
  const fetcher=vi.fn(async(url:string)=>{
   if(url==='/api/edge/radio')return {events:[{hk:'vesper',tag:'HIGH · SOURCE LABEL',txt:'Sign: test device.',t:'2026-11-04T00:00:00Z'},{hk:'bastion',txt:'The gate holds.',tag:'INFO',t:'x'}],count:2};
   throw new ApiError('no',404)});
  const out=await edgeData('/api/edge/radio',fetcher,miss) as {feedTop:unknown;feedRest:unknown[]};
  expect(fetcher).toHaveBeenCalledTimes(1);
  expect((out.feedTop as {hk:string}).hk).toBe('vesper');
  expect(out.feedRest).toHaveLength(1);
  expect((out.feedRest[0] as {hk:string}).hk).toBe('bastion')});
 it('falls back to silent when the radio route is missing',async()=>{
  const fetcher=vi.fn(async()=>{throw new ApiError('This edge capability has not been delivered.',404)});
  await expect(edgeData('/api/edge/radio',fetcher,miss)).rejects.toThrow();
  expect(fetcher).toHaveBeenCalledTimes(1)});
 it('passes non-radio 404s through to the legacy shim unchanged',async()=>{
  const fetcher=vi.fn(async(url:string)=>{
   if(url==='/api/net/watchtower?limit=30')return {success:true,enabled:true,alerts:[{title:'t',source:'s',severity:'high',ts:1}]};
   throw new ApiError('no',404)});
  const out=await edgeData('/api/edge/summary',fetcher,miss) as {feedTop:{hk:string}};
  expect(out.feedTop.hk).toBe('argus')})});
