import {describe,expect,it} from 'vitest';
import {alias} from './privacy';
import {category,osFamily,recordingProjection,recordingStep,safeState,safeTime,safeVendor} from './recording';
const LEAKS=['192.168.0.221','192.0.2.58','00:11:22:33:44:55','AA:BB:CC:DD:EE:FF','private-network','private-user','secret-token-value','password=hunter2','ExampleUplink','edge.example.invalid'];
function overviewFindings(){return [{id:'a1',title:'Observed endpoint 192.168.0.221 changed DNS bailiwick',severity:'high',operator_state:'unreviewed',observed_at:'2026-11-04T00:00:00Z',facts:['192.168.0.221 queried private-network'],explanation:'private-user laptop did secret-token-value stuff'}]}
function overview(){return {generated_at:'2026-11-04T01:00:00Z',sources:{host:{freshness:'current',data:{services:[{state:'online'},{state:'offline'}]}},insights:{freshness:'current'},archive:{freshness:'stale',total_events:7}},insights:overviewFindings()}}
function topology(){return {generated_at:'2026-11-04T01:00:00Z',nodes:[{id:'00:11:22:33:44:55',source:'ragnar-stable-cache',manufacturer:'Example Corp',os:'Linux 6.18 on private-user box',status:'reported-up',seen:'2026-11-04T00:30:00Z'},{id:'192.168.0.221',source:'ragnar-stable-cache',manufacturer:'password=hunter2 vendor',os:'Totally Unknown OS 9000',status:'evil;DROP TABLE',seen:'not-a-time'}],edges:[{id:'e1',source:'00:11:22:33:44:55',target:'192.168.0.221',protocol:'tcp'},{id:'e2',source:'00:11:22:33:44:55',target:'excluded-node',protocol:'weirdproto'}]}}
describe('recording primitive guards',()=>{
 it('osFamily projects to safe family or Unknown, never raw strings',()=>{
  expect(osFamily('Linux on private-user box')).toBe('Linux');expect(osFamily('Totally Unknown OS 9000')).toBe('Unknown');expect(osFamily(undefined)).toBe('Unknown');expect(osFamily(42)).toBe('Unknown')});
 it('safeVendor rejects identifiers, URLs and secrets',()=>{
  expect(safeVendor('Example Corp')).toBe('Example Corp');expect(safeVendor('00:11:22:33:44:55')).toBe('MAC vendor unknown');expect(safeVendor('192.168.0.221')).toBe('MAC vendor unknown');expect(safeVendor('https://evil.example/x')).toBe('MAC vendor unknown');expect(safeVendor('password=hunter2 vendor')).toBe('MAC vendor unknown');expect(safeVendor(undefined)).toBe('MAC vendor unknown')});
 it('category never repeats raw titles',()=>{
  expect(category('Observed endpoint changed DNS bailiwick')).toBe('DNS-related observation');expect(category('Port 22 opened')).toBe('Service change');expect(category('Radio hardware fault')).toBe('Hardware observation');expect(category('192.168.0.221 did a thing')).toBe('Sensor observation')});
 it('safeState allowlists known states',()=>{
  expect(safeState('current')).toBe('current');expect(safeState('evil;DROP TABLE')).toBe('unknown');expect(safeState(undefined)).toBe('unknown')});
 it('safeTime never throws on garbage',()=>{
  expect(safeTime('2026-11-04T22:10:00')).toContain('source zone unspecified');expect(safeTime('not-a-time')).toBe('Time unavailable');expect(safeTime(undefined)).toBe('Time unavailable');expect(typeof safeTime('2026-11-04T00:00:00Z')).toBe('string')});
 it('recordingStep defaults unknown hashes to overview',()=>{
  expect(recordingStep('#recording/wifi-defense')).toBe('wifi-defense');expect(recordingStep('#recording/evil')).toBe('overview');expect(recordingStep('')).toBe('overview')});
 it('aliases correlate within the session',()=>{expect(alias('one')).toBe(alias('one'));expect(alias('one')).not.toBe(alias('two'))})});
describe('recordingProjection privacy boundary',()=>{
 it('withholds every raw identifier, free text and secret in one JSON dump',()=>{
  const output=JSON.stringify(recordingProjection(overview(),topology()));
  for(const raw of LEAKS)expect(output).not.toContain(raw)});
 it('projects nodes to alias + safe vendor + OS family only',()=>{
  const {nodes}=recordingProjection(overview(),topology());
  expect(nodes).toHaveLength(2);
  expect(nodes[0].manufacturer).toBe('Example Corp');expect(nodes[0].os).toBe('Linux');expect(nodes[0].state).toBe('reported-up');
  expect(nodes[1].manufacturer).toBe('MAC vendor unknown');expect(nodes[1].os).toBe('Unknown');expect(nodes[1].state).toBe('unknown');
  expect(nodes[0].id).toMatch(/^Entity-[0-9a-f]{1,6}$/)});
 it('drops edges to non-inventory targets and normalizes unknown protocols',()=>{
  const {edges}=recordingProjection(overview(),topology());
  expect(edges).toHaveLength(1);expect(edges[0].protocol).toBe('tcp')});
 it('projects findings to category + severity, never raw titles',()=>{
  const {findings}=recordingProjection(overview(),topology());
  expect(findings).toHaveLength(1);expect(findings[0].category).toBe('DNS-related observation');expect(findings[0].severity).toBe('high')});
 it('reports source freshness as allowlisted states and service counts',()=>{
  const out=recordingProjection(overview(),topology());
  expect(out.sources).toEqual({host:'current',insights:'current',archive:'stale'});
  expect(out.services_reported).toBe(2);expect(out.services_active).toBe(1);expect(out.archive_events).toBe(7)});
 it('is null-safe on hostile shapes',()=>{
  const out=recordingProjection(null,{nodes:'not-an-array',edges:null});
  expect(out.nodes).toEqual([]);expect(out.edges).toEqual([]);expect(out.findings).toEqual([]);expect(out.services_reported).toBe(0)})});
