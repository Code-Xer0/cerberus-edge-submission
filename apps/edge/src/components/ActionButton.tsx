import {motion} from 'motion/react';
import type {ComponentProps} from 'react';
export function ActionButton({variant='secondary',...props}:ComponentProps<typeof motion.button>&{variant?:'primary'|'secondary'|'danger'|'quiet'}){return <motion.button {...props} className={'action-button action-'+variant+' '+(props.className||'')} whileTap={props.disabled?undefined:{y:2,scale:.985}} transition={{duration:.1}}/>}
