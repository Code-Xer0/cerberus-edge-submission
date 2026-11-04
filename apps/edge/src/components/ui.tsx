import React from 'react';
import {IconHelpCircle as CircleHelp} from '@tabler/icons-react';
export function tone(s?:string){return s==='online'?'good':s==='offline'?'bad':'muted'}
export function Pill({children,kind='muted'}:{children:React.ReactNode;kind?:string}){return <span className={'pill '+kind}><i/>{children}</span>}
export function Panel({title,eyebrow,children}:{title:string;eyebrow:string;children:React.ReactNode}){return <section className="panel"><div className="panel-head"><div><small>{eyebrow}</small><h2>{title}</h2></div></div>{children}</section>}
export function Empty({error,loading}:{error?:string;loading?:boolean}){return <div className="empty"><CircleHelp size={21}/><div><strong>{loading?'Checking the edge…':error?'Data unavailable':'Waiting for a live source'}</strong><p>{error||(loading?'Getting the latest observation.':'This plane will show evidence when its adapter is connected.')}</p></div></div>}
