import tempfile,unittest
from pathlib import Path
from overview import freshness,vendor
class ProjectionTests(unittest.TestCase):
 def test_unknown_and_old_time_cannot_be_current(self):
  self.assertEqual(freshness({}),'unknown');self.assertEqual(freshness({'generated_at':'2000-01-01T00:00:00Z'}),'stale')
 def test_local_mac_never_receives_manufacturer(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'oui';p.write_text('001122     (base 16) Example maker\n021122     (base 16) Fake maker\n')
   self.assertEqual(vendor('00:11:22:33:44:55',str(p)),'Example maker');self.assertIsNone(vendor('02:11:22:33:44:55',str(p)))
 def test_overview_reads_only_sources_and_account_completed_explanation(self):
  import asyncio,sqlite3,json,datetime
  from overview import overview
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'ledger.sqlite'
   def db():
    c=sqlite3.connect(path);c.row_factory=sqlite3.Row;return c
   with db() as c:
    c.execute('CREATE TABLE audit(seq INTEGER PRIMARY KEY,at REAL,actor TEXT,kind TEXT,payload TEXT)')
    c.executemany('INSERT INTO audit VALUES(?,?,?,?,?)',[(1,1,'other','explanation',json.dumps({'status':'completed','explanation':'private'})),(2,2,'me','explanation',json.dumps({'status':'completed','explanation':'saved'})),(3,3,'me','explanation',json.dumps({'status':'failed'}))])
   paths=[]
   async def upstream(app,path,**kw):
    paths.append(path)
    if path=='/api/insights':raise TimeoutError()
    return {'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'services':[{'state':'online'}]}
   result=asyncio.run(overview({},'', 'me',upstream,db))
   self.assertEqual(result['latest_explanation']['explanation'],'saved');self.assertEqual(result['sources']['insights']['freshness'],'unavailable');self.assertEqual(len(paths),3);self.assertNotIn('/api/insights/explain',paths)
