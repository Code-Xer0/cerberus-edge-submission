export type EdgeRoute={page:string;selected?:string};
export function parseRoute(hash:string,known:readonly string[]):EdgeRoute{const [page,query='']=hash.replace(/^#/,'').split('?',2);const selected=new URLSearchParams(query).get('target')||undefined;return {page:known.includes(page)?page:'home',selected:selected&&selected.length<=256&&!/[\x00-\x1f]/.test(selected)?selected:undefined}}
export function routeHash(page:string,selected?:string):string{return '#'+page+(selected?'?'+new URLSearchParams({target:selected}).toString():'')}
