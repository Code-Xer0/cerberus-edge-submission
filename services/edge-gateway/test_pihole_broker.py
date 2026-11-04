import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
from pihole_policy import domain_name,validate_action
spec=importlib.util.spec_from_file_location('pihole_broker',Path(__file__).parents[1]/'edge-plugins/pihole/broker.py');broker=importlib.util.module_from_spec(spec);spec.loader.exec_module(broker)
class BrokerTests(unittest.TestCase):
 def setUp(self):broker.CACHE.clear()
 def test_only_exact_names_and_bounded_actions_are_accepted(self):
  for name in ('https://example.com','*.example.com','evil.com;reboot','127.0.0.1','example.com\nbad','single-label'):
   with self.assertRaises(ValueError):domain_name(name)
  self.assertEqual(domain_name('Example.COM.'),'example.com')
  for seconds in (0,1,301,-1,True,'60'):
   with self.assertRaises(ValueError):validate_action({'action':'pause','seconds':seconds})
  with self.assertRaises(ValueError):validate_action({'action':'exec','command':'reboot'})
 def test_pause_uses_native_timer_and_requires_verified_timer_readback(self):
  with patch.object(broker,'status',side_effect=[{'blocking':True},{'blocking':False,'timer_seconds':60}]),patch.object(broker,'command') as call:
   receipt=broker.apply({'action':'pause','seconds':60});self.assertEqual(receipt['state'],'verified');call.assert_called_once_with('disable','60s')
  with patch.object(broker,'status',return_value={'blocking':False}),patch.object(broker,'command') as call:
   with self.assertRaises(ValueError):broker.apply({'action':'pause','seconds':60})
   call.assert_not_called()
 def test_enable_verifies_filtering_without_domain_policy_lookup(self):
  with patch.object(broker,'status',side_effect=[{'blocking':False},{'blocking':True,'timer_seconds':None}]),patch.object(broker,'command') as call,patch.object(broker,'domain_state') as lookup:
   result=broker.apply({'action':'enable'});self.assertEqual(result['state'],'verified');call.assert_called_once_with('enable');lookup.assert_not_called()
  with patch.object(broker,'status',return_value={'blocking':False,'timer_seconds':None}),patch.object(broker,'command'):
   self.assertEqual(broker.apply({'action':'enable'})['state'],'unverified')
 def test_domain_policy_is_review_bound_and_uses_fixed_cli_arguments(self):
  with patch.object(broker,'status',return_value={'blocking':True,'timer_seconds':None}),patch.object(broker,'domain_state',side_effect=[{'allow':False,'deny':False,'allow_enabled':False,'deny_enabled':False},{'allow':True,'deny':False,'allow_enabled':True,'deny_enabled':False}]),patch.object(broker,'command') as call:
   result=broker.apply({'action':'allow','domain':'example.com','expected_policy':{'allow':False,'deny':False,'allow_enabled':False,'deny_enabled':False}});self.assertEqual(result['state'],'verified');call.assert_called_once_with('allow','example.com')
  with patch.object(broker,'status',return_value={'blocking':True}),patch.object(broker,'domain_state',return_value={'allow':True,'deny':False,'allow_enabled':True,'deny_enabled':False}),patch.object(broker,'command') as call:
   with self.assertRaises(ValueError):broker.apply({'action':'deny','domain':'example.com','expected_policy':{'allow':False,'deny':False,'allow_enabled':False,'deny_enabled':False}})
   call.assert_not_called()
 def test_present_but_disabled_rule_is_not_verified_as_active_policy(self):
  prior={'allow':False,'deny':False,'allow_enabled':False,'deny_enabled':False};after={'allow':True,'deny':False,'allow_enabled':False,'deny_enabled':False}
  with patch.object(broker,'status',return_value={'blocking':True,'timer_seconds':None}),patch.object(broker,'domain_state',side_effect=[prior,after]),patch.object(broker,'command'):
   result=broker.apply({'action':'allow','domain':'example.com','expected_policy':prior});self.assertEqual(result['state'],'unverified')
 def test_status_projection_does_not_export_credentials_or_query_names(self):
  def source(path):return {'blocking':'enabled','timer':None} if path=='dns/blocking' else {'queries':{'total':42,'blocked':2,'api_key':'must-not-export'},'clients':{'active':1,'names':['private.example']}}
  with patch.object(broker,'api',side_effect=source):value=broker.status(True)
  self.assertTrue(value['blocking']);self.assertEqual(value['queries']['total'],42);self.assertNotIn('must-not-export',str(value));self.assertNotIn('private.example',str(value))
