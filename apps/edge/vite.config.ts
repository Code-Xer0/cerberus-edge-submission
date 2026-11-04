import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
export default defineConfig({
 plugins:[react(),{name:'local-reference-qa',apply:'serve',configureServer(server){server.middlewares.use('/__qa__',async(req,res)=>{const match=req.url?.match(/^\/(\d{2}-[a-z-]+)\/mock\.json$/);if(!match||Number(match[1].slice(0,2))>18){res.statusCode=404;res.end();return}try{const data=await readFile(path.join('/tmp/cerberus-v3-reference/handoff',match[1],'mock.json'));res.setHeader('Content-Type','application/json');res.setHeader('Cache-Control','no-store');res.end(data)}catch{res.statusCode=404;res.end()}})}}],
 base:'./',publicDir:'public-v3',server:{host:'127.0.0.1',allowedHosts:['terminal.local']}
});
