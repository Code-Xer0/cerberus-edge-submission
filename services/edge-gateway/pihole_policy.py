"""Shared exact-domain and bounded-action contract for the Pi-hole plugin."""
import ipaddress,re

def domain_name(value):
 if not isinstance(value,str):raise ValueError('A DNS name is required')
 value=value.strip().rstrip('.').lower()
 try:value=value.encode('idna').decode('ascii')
 except UnicodeError:raise ValueError('Invalid DNS name')
 if len(value)>253 or '.' not in value or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',p) for p in value.split('.')):raise ValueError('Use one exact fully qualified DNS name; no URL, wildcard or regex')
 try:ipaddress.ip_address(value)
 except ValueError:return value
 raise ValueError('Use a DNS name, not an address')

def validate_action(data):
 action=data.get('action')
 if action not in ('enable','pause','allow','deny','remove_allow','remove_deny'):raise ValueError('Unsupported DNS action')
 result={'action':action}
 if action=='pause':
  seconds=data.get('seconds')
  if type(seconds) is not int or seconds not in (30,60,300):raise ValueError('Pause must be 30, 60 or 300 seconds')
  result['seconds']=seconds
 elif action not in ('enable',):result['domain']=domain_name(data.get('domain'))
 return result
