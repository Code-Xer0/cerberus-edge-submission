// @vitest-environment jsdom
import {describe,it,expect,vi,afterEach,beforeEach} from 'vitest';
import {render,screen,cleanup,fireEvent} from '@testing-library/react';
import {ActivityDrawer} from './ActivityDrawer';
vi.mock('../lib/sound',()=>({cue:vi.fn()}));
HTMLDialogElement.prototype.showModal=vi.fn();HTMLDialogElement.prototype.close=vi.fn();
class FakeEventSource{close=vi.fn();onmessage:null=null}
beforeEach(()=>{vi.stubGlobal('EventSource',FakeEventSource)});
afterEach(()=>{cleanup();vi.unstubAllGlobals()});
const json=(data:unknown)=>({ok:true,headers:new Headers({'content-type':'application/json'}),json:async()=>data} as Response);
const settle=()=>new Promise(r=>setTimeout(r,300));
describe('voice this button',()=>{
 it('posts a reviewed refresh and reloads the voiced feed',async()=>{
  let voiced=false;
  const fetch=vi.fn(async(url:string)=>{
   if(String(url)==='/api/edge/session')return json({csrf:'token'});
   if(String(url)==='/api/edge/radio')return json(voiced?{events:[{hk:'vesper',tag:'HIGH',txt:'Sign: test.',t:'x'}],count:1}:{events:[{hk:'argus',tag:'MEDIUM',txt:'Yard looks settled.',t:'x'}],count:1});
   if(String(url)==='/api/edge/radio/refresh'){voiced=true;return json({events:[],count:0,voiced:'model'})}
   return json({})});
  vi.stubGlobal('fetch',fetch);
  render(<ActivityDrawer value={{}}/>);
  fireEvent.click(screen.getByText('ACTIVITY / CONVERSATION'));
  await screen.findByText('VOICE THIS');
  try {
   await screen.findByText(/Yard looks settled./, undefined, {timeout: 2000});
  } catch {
   throw new Error('yard line never rendered');
  }
  fireEvent.click(screen.getByText('VOICE THIS'));
  await settle();
  expect(fetch).toHaveBeenCalledWith('/api/edge/radio/refresh',expect.objectContaining({method:'POST'}));
  await screen.findByText(/Sign: test./);});
 it('shows the failure without clearing the instant lines',async()=>{
  const fetch=vi.fn(async(url:string)=>{
   if(String(url)==='/api/edge/session')return json({csrf:'token'});
   if(String(url)==='/api/edge/radio')return json({events:[{hk:'argus',tag:'MEDIUM',txt:'Yard looks settled.',t:'x'}],count:1});
   return {ok:false,status:503,headers:new Headers({'content-type':'application/json'}),json:async()=>({error:'upstream_unavailable'})} as Response});
  vi.stubGlobal('fetch',fetch);
  render(<ActivityDrawer value={{}}/>);
  fireEvent.click(screen.getByText('ACTIVITY / CONVERSATION'));
  await screen.findByText('VOICE THIS');
  fireEvent.click(screen.getByText('VOICE THIS'));
  await settle();
  await screen.findByText(/upstream_unavailable/i);
  expect(screen.getByText(/Yard looks settled./)).toBeTruthy()})});
