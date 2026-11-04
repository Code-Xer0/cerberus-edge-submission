// @vitest-environment jsdom
import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import {OperatorOverview} from './OperatorOverview';
vi.mock('../lib/api',()=>({useResult:()=>({value:{data:{schema:'cerberus.overview/1',brief:[{text:'Two services report active.',kind:'observation'}],sources:{insights:{data:{insights:[]}}},insights:[],recent_actions:[{seq:9,kind:'dns',at:1}],gaps:[]}},loading:false,refresh:vi.fn()})}));
Object.defineProperty(HTMLDialogElement.prototype,'close',{configurable:true,value:vi.fn()});Object.defineProperty(HTMLDialogElement.prototype,'showModal',{configurable:true,value:vi.fn()});afterEach(cleanup);
describe('operator overview',()=>{it('puts source facts and AI discovery on the opening screen without a model write',()=>{render(<OperatorOverview navigate={vi.fn()}/>);expect(screen.getByText(/Two services report active/)).toBeTruthy();expect(screen.getByText('AI intelligence')).toBeTruthy();expect(screen.getByText('REVIEW REQUEST')).toBeTruthy()})});
