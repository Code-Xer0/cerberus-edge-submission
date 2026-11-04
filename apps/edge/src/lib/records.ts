export type RecordValue=Record<string,unknown>;
export function record(value:unknown):RecordValue{return typeof value==='object'&&value!==null&&!Array.isArray(value)?value as RecordValue:{}}
export function records(value:unknown):RecordValue[]{return Array.isArray(value)?value.filter(x=>typeof x==='object'&&x!==null&&!Array.isArray(x)) as RecordValue[]:[]}
export function label(value:unknown,fallback='Unavailable'):string{return (typeof value==='string'||typeof value==='number')?String(value).slice(0,1200):fallback}
export function identifier(value:RecordValue):string|undefined{const id=value.mac||value.id;return typeof id==='string'&&id.length>0?id:undefined}
export function percent(value:unknown):number|undefined{if(typeof value==='string'&&!/^\d+(\.\d+)?%?$/.test(value))return undefined;const n=typeof value==='number'?value:typeof value==='string'?Number(value.replace('%','')):NaN;return Number.isFinite(n)&&n>=0&&n<=100?n:undefined}
export function statusTone(value:unknown):string{const s=label(value,'').toLowerCase();return ['online','healthy','safe','trusted','complete','closed','synced'].includes(s)?'good':['high','critical','failed','offline','cut off'].includes(s)?'bad':['degraded','pending','needs approval','watching'].includes(s)?'warn':'muted'}
