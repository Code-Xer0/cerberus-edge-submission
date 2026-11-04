// @vitest-environment jsdom
import {describe,it,expect} from 'vitest';
import {project,alias} from './privacy';
describe('recording projection',()=>{it('withholds free text and identifiers recursively without mutating originals',()=>{const input={id:'192.168.0.221',mac:'00:11:22:33:44:55',ssid:'private-network',explanation:'private-user laptop',csrf:'secret',os:'Linux on private-user',manufacturer:'Example',count:4};const output=JSON.stringify(project(input));for(const raw of ['192.168.0.221','00:11:22','private-network','private-user','secret'])expect(output).not.toContain(raw);expect(output).toContain('Linux');expect(output).toContain('Example');expect(input.id).toBe('192.168.0.221')});it('aliases correlate within the session',()=>expect(alias('one')).toBe(alias('one')))});
