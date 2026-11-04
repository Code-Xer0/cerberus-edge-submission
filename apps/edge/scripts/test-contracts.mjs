import {execFileSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
execFileSync('node',['node_modules/typescript/bin/tsc','--skipLibCheck','--target','ES2022','--module','commonjs','--moduleResolution','node','--esModuleInterop','--outDir','.cache/contracts','src/lib/api.ts','src/lib/mood.ts','src/lib/records.ts','src/lib/navigation.ts','src/lib/compatibility.ts','src/lib/operations.ts','src/lib/gatewaySetup.ts','src/lib/visualData.ts'],{stdio:'inherit'});
writeFileSync('.cache/contracts/package.json',JSON.stringify({type:'commonjs'}));
execFileSync('node',['--test','tests/contracts.test.cjs'],{stdio:'inherit'});
