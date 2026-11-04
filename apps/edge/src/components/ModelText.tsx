import {lazy,Suspense} from 'react';
const Markdown=lazy(()=>import('react-markdown'));
/** Model text is untrusted. No raw HTML, external images, or executable links. */
export function ModelText({children}:{children:string}){return <div className="model-output"><Suspense fallback={<p>{children}</p>}><Markdown skipHtml disallowedElements={['img','iframe','script','style']} components={{a:({children})=><span>{children}</span>}}>{children}</Markdown></Suspense></div>}
