// @vitest-environment jsdom
import {describe,it,expect,vi,afterEach} from 'vitest';
import {render,screen,cleanup} from '@testing-library/react';
import {LinkTransitions} from './LinkTransitions';
vi.mock('../lib/sound',()=>({cue:vi.fn()}));
afterEach(cleanup);
const host=(state:string)=>({links:[{interface:'wan',name:'WAN link',state}]});
describe('connection transition semantics',()=>{it('does not claim recovery on the first successful observation',()=>{const view=render(<LinkTransitions host={undefined} stale/>);view.rerender(<LinkTransitions host={host('online')} stale={false}/>);expect(screen.queryByText('CONNECTION UPDATE')).toBeNull()});it('only announces a link loss after a confirmed online baseline',()=>{const view=render(<LinkTransitions host={host('online')} stale={false}/>);view.rerender(<LinkTransitions host={host('offline')} stale={false}/>);expect(screen.getByText('LINK LOST')).toBeTruthy();expect(screen.getByText('WAN link reports disconnected.')).toBeTruthy()});it('distinguishes failed telemetry from a confirmed disconnect',()=>{const view=render(<LinkTransitions host={host('online')} stale={false}/>);view.rerender(<LinkTransitions host={undefined} stale/>);expect(screen.getByText('SOURCE DELAYED')).toBeTruthy();expect(screen.queryByText('LINK LOST')).toBeNull()})});
