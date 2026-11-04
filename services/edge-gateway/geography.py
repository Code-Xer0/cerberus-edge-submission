"""Bounded, offline country projection of authenticated sensor connection observations."""
import datetime,ipaddress,sqlite3
from contextlib import closing
from pathlib import Path
COUNTRY_DB=Path('/opt/cerberus-edge/geo/country.sqlite')
def projection(payload,path=COUNTRY_DB):
 if not isinstance(payload,dict) or payload.get('success') is not True:raise ValueError('Connection observations unavailable')
 countries={};items=[];unknown=0;public=0;rows=payload.get('connections',[])
 if not isinstance(rows,list):raise ValueError('Invalid connection observations')
 with closing(sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)) as geo:
  for index,row in enumerate(rows[:60]):
   if not isinstance(row,dict):continue
   endpoints=[]
   for candidate in set(str(row.get(k,'')) for k in ('src_ip','dst_ip')):
    try:ip=ipaddress.ip_address(candidate)
    except ValueError:continue
    if not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_unspecified:continue
    public+=1;key=ip.packed;found=geo.execute('SELECT end,country FROM ranges WHERE version=? AND start<=? ORDER BY start DESC LIMIT 1',(ip.version,key)).fetchone();country=found[1] if found and key<=found[0] else None
    if not country or not isinstance(country,str) or len(country)!=2:unknown+=1;continue
    countries[country]=countries.get(country,0)+1;endpoints.append({'country':country})
   if endpoints:
    items.append({'id':'connection-'+str(index),'endpoint_locations':endpoints,'last_seen':row.get('last_seen') if isinstance(row.get('last_seen'),str) else None})
 return {'schema':'cerberus.traffic-geography/1','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'locations':[{'country':country,'count':count} for country,count in sorted(countries.items())],'events':items,'connections_returned':min(len(rows),60),'public_endpoint_observations':public,'unknown_country_observations':unknown,'source':'Ragnar retained connection sample; not an attack feed','provider':{'id':'db-ip-country-lite','mode':'offline','release':'2026-11','attribution':'IP Geolocation by DB-IP','license':'CC BY 4.0'}}
