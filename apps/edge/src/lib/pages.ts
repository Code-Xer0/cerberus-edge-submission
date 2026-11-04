import {IconActivity as Activity,IconBell as Bell,IconBox as Box,IconChevronRight as ChevronRight,IconHelpCircle as CircleHelp,IconCpu as Cpu,IconDatabase as Database,IconWorld as Globe2,IconDeviceFloppy as HardDrive,IconHome2 as Home,IconLock as LockKeyhole,IconMap as Map,IconNetwork as Network,IconBroadcast as Radio,IconRefresh as RefreshCw,IconSettings as Settings,IconShield as Shield,IconShieldExclamation as ShieldAlert,IconUsers as Users,IconWifi as Wifi} from '@tabler/icons-react';
type Page={id:string;name:string;group:string;icon:typeof Home;api?:string;description:string};
export const pages:Page[]=[
 {id:'origins',name:'About & provenance',group:'MANAGE',icon:Shield,description:'Contribution boundaries, upstream notices, and release maturity.'},
 {id:'evidence',name:'Evidence desk',group:'RESPOND',icon:Database,description:'Investigate, record decisions, and export source receipts.'},
 {id:'home',name:'Overview',group:'PROTECT',icon:Home,api:'/api/edge/summary',description:'Your network and the things that need attention.'},
 {id:'locations',name:'Locations',group:'PROTECT',icon:Globe2,api:'/api/edge/fleet',description:'Connected sites and their current status.'},
 {id:'site-map',name:'Site map',group:'PROTECT',icon:Map,description:'Explore the physical site and its devices.'},
 {id:'devices',name:'Devices',group:'PROTECT',icon:Box,api:'/api/edge/devices',description:'Devices observed by your edge sensor.'},
 {id:'device-detail',name:'Device detail',group:'PROTECT',icon:Box,description:'Inspect a device and its evidence.'},
 {id:'traffic',name:'Traffic',group:'PROTECT',icon:Activity,api:'/api/edge/traffic/speed',description:'Understand traffic crossing this site.'},
 {id:'firewall',name:'Firewall',group:'PROTECT',icon:Shield,api:'/api/edge/firewall/doors',description:'Review doors, filters, and network rules.'},
 {id:'gateway-setup',name:'Gateway setup',group:'MANAGE',icon:Wifi,description:'Guided WAN, client AP, addressing and verification workflow.'},
 {id:'wireless',name:'Wi-Fi & Bluetooth',group:'PROTECT',icon:Wifi,api:'/api/edge/wireless',description:'Radio interfaces and wireless observations.'},
 {id:'action-receipts',name:'Action receipts',group:'RESPOND',icon:Database,description:'Persistent decisions, model explanations and verified runtime receipts.'},
 {id:'threat-reporting',name:'Threat reporting',group:'RESPOND',icon:Globe2,api:'/web/cerberus-edge/reporting.v1.json',description:'Durable observations, approximate endpoint locations, and reporting providers.'},
 {id:'checkups',name:'Checkups',group:'PROTECT',icon:Shield,api:'/api/edge/checkups',description:'Review findings and controlled checkups.'},
 {id:'alerts',name:'Alerts',group:'RESPOND',icon:ShieldAlert,api:'/api/edge/alerts',description:'Investigate events and requests for approval.'},
 {id:'insights',name:'Operator insights',group:'RESPOND',icon:Cpu,api:'/api/edge/insights',description:'What the evidence means, in plain language.'},
 {id:'incident-replay',name:'Incident replay',group:'RESPOND',icon:Activity,description:'Follow evidence and decisions in an incident.'},
 {id:'notifications',name:'Notifications',group:'RESPOND',icon:Bell,api:'/api/edge/notifications',description:'Delivery history and notification status.'},
 {id:'weekly-report',name:'Weekly report',group:'RESPOND',icon:Database,description:'Review a site report and its evidence.'},
 {id:'add-box',name:'Add a box',group:'MANAGE',icon:Box,description:'Pair another Cerberus Edge device.'},
 {id:'sync',name:'Sync & backup',group:'MANAGE',icon:Database,api:'/api/edge/sync',description:'Connection, backup, and synchronization state.'},
 {id:'people',name:'People & access',group:'MANAGE',icon:Users,api:'/api/edge/users',description:'People and their access to this site.'},
 {id:'settings',name:'Settings',group:'MANAGE',icon:Settings,api:'/api/edge/settings',description:'System configuration and safety limits.'},
 {id:'pi-screensaver',name:'Pi screensaver',group:'MANAGE',icon:Activity,description:'At-a-glance presentation for the Pi display.'},
 {id:'system',name:'System & hardware',group:'MANAGE',icon:Cpu,description:'Host, services, hardware, and recovery.'},
 {id:'storage',name:'Storage & logs',group:'MANAGE',icon:HardDrive,description:'Storage health and diagnostic evidence.'},
 {id:'dns',name:'DNS / Pi-hole',group:'MANAGE',icon:Network,description:'Manage the existing resolver through a private, reviewed control broker.'},
 {id:'network-map',name:'Network map',group:'MANAGE',icon:Network,description:'Explore sensor-observed connections and host interface relationships.'},
 {id:'global-activity',name:'Global activity',group:'RESPOND',icon:Globe2,description:'Follow reported findings and approximate endpoint countries.'},
 {id:'network',name:'Network & recovery',group:'MANAGE',icon:Network,description:'Interfaces, firewall observations, and recovery links.'},
];
export const pack=[{name:'VESPER',role:'HUNT',image:'vesper.svg',color:'#e8b54a',desc:'Investigates signals'},{name:'ARGUS',role:'WATCH',image:'argus.svg',color:'#4fd8ec',desc:'Observes the network'},{name:'BASTION',role:'LOCK',image:'bastion.svg',color:'#ff5252',desc:'Protects the edge'}];

export const pageIds=pages.map(p=>p.id);
