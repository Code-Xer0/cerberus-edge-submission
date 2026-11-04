// @vitest-environment jsdom
import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,cleanup,fireEvent,waitFor} from '@testing-library/react';
import {DemoConsole} from './DemoConsole';
import {edgeWrite} from '../lib/gateway';
let denied=false;
vi.mock('../lib/api',()=>({useResult:(url:string)=>({loading:false,refresh:vi.fn(),value:{httpStatus:denied?401:200,data:url.includes('recording-evidence')?{ai:{state:'unavailable'},wifi:{state:'unavailable'}}:url.includes('topology')?{nodes:[{source:'ragnar-stable-cache',id:'192.0.2.44',hostname:'private-account',manufacturer:'Example Corp',os:'Linux private-account',status:'reported-up'}],edges:[]}:{sources:{host:{freshness:'current',data:{services:[]}}},insights:[{id:'secret-device-reference',title:'DNS private-account 192.0.2.44',severity:'high',operator_state:'unreviewed'}]}}})}));
vi.mock('../lib/gateway',()=>({edgeWrite:vi.fn().mockRejectedValue(new Error('test failure'))}));
vi.mock('../visuals/Motion',()=>({useMotion:()=>({active:false})}));
Object.defineProperty(HTMLDialogElement.prototype,'close',{configurable:true,value:vi.fn()});Object.defineProperty(HTMLDialogElement.prototype,'showModal',{configurable:true,value:vi.fn()});
afterEach(()=>{cleanup();denied=false;vi.clearAllMocks()});
describe('scoped recording acceptance',()=>{
 it('projects identities and performs no automatic writes',()=>{location.hash='#recording/overview';const {container}=render(<DemoConsole leave={vi.fn()}/>);expect(container.innerHTML).not.toContain('192.0.2.44');expect(container.innerHTML).not.toContain('private-account');expect(container.innerHTML).not.toContain('secret-device-reference');expect(screen.getByText('DNS-related observation')).toBeTruthy();expect(edgeWrite).not.toHaveBeenCalled()});
 it('fails closed for expired authentication and absent model proof',()=>{location.hash='#recording/intelligence';const first=render(<DemoConsole leave={vi.fn()}/>);expect(screen.getByText(/Model evidence unavailable/i)).toBeTruthy();expect(screen.queryByText('VERIFIED RECORDED RESPONSE')).toBeNull();first.unmount();denied=true;render(<DemoConsole leave={vi.fn()}/>);expect(screen.getByText(/Session unavailable/i)).toBeTruthy();expect(screen.queryByText('DNS-related observation')).toBeNull()});
 it('does not claim session end when the reviewed write fails',async()=>{location.hash='#recording/safety';render(<DemoConsole leave={vi.fn()}/>);fireEvent.click(screen.getByRole('button',{name:'END BROWSER SESSION → SIGN-IN'}));await waitFor(()=>expect(screen.getByRole('alert').textContent).toContain('Do not assume you are signed out'));expect(edgeWrite).toHaveBeenCalledWith('session/end',{})});
});
