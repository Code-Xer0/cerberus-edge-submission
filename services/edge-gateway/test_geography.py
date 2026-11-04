import ipaddress,sqlite3,tempfile,unittest
from pathlib import Path
from geography import projection
class GeographyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'country.sqlite'
  with sqlite3.connect(self.path) as db:
   db.execute('CREATE TABLE ranges(version INTEGER,start BLOB,end BLOB,country TEXT,PRIMARY KEY(version,start)) WITHOUT ROWID')
   for address,country in [('8.8.8.8','US'),('1.1.1.1','AU')]:
    ip=ipaddress.ip_address(address);db.execute('INSERT INTO ranges VALUES(?,?,?,?)',(ip.version,ip.packed,ip.packed,country))
 def tearDown(self):self.temp.cleanup()
 def test_only_real_public_endpoints_are_located_without_exposing_addresses(self):
  payload=projection({'success':True,'connections':[{'src_ip':'192.168.0.2','dst_ip':'8.8.8.8'},{'src_ip':'100.64.0.10','dst_ip':'1.1.1.1'},{'src_ip':'127.0.0.1','dst_ip':'unknown'}]},self.path)
  self.assertEqual(payload['locations'],[{'country':'AU','count':1},{'country':'US','count':1}]);self.assertEqual(payload['public_endpoint_observations'],2);self.assertNotIn('8.8.8.8',str(payload));self.assertNotIn('192.168',str(payload))
 def test_unknown_lookup_stays_unknown_and_does_not_create_marker(self):
  payload=projection({'success':True,'connections':[{'src_ip':'9.9.9.9','dst_ip':'10.0.0.1'}]},self.path);self.assertEqual(payload['locations'],[]);self.assertEqual(payload['unknown_country_observations'],1)
 def test_connections_are_bounded_and_source_failure_is_not_quiet(self):
  payload=projection({'success':True,'connections':[{'src_ip':'8.8.8.8','dst_ip':'1.1.1.1'}]*1000},self.path);self.assertEqual(payload['connections_returned'],60);self.assertEqual(payload['public_endpoint_observations'],120)
  with self.assertRaises(ValueError):projection({'success':False},self.path)
