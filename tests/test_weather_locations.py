"""Pinned catalog/index and preference transactions, synthetic XDG/network only."""
import copy
import fcntl
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
from urllib.error import URLError

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'widgets'))
import weather_locations as geo
from test_weather import weather


class LocationTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);self.root=Path(folder.name)
        self.env=patch.dict(os.environ,{'XDG_CACHE_HOME':str(self.root/'cache'),'XDG_CONFIG_HOME':str(self.root/'config'),'ORBITZ_LOCALE':'en-US'})
        self.env.start();self.addCleanup(self.env.stop)
        self.world=[dict(iso2='BR',name='Brazil',states=[dict(id=1,name='Distrito Federal',cities=[dict(id=1,name='Brasília',latitude='-15.7939',longitude='-47.8828',timezone='America/Sao_Paulo'),dict(id=2,name='São Lugar',latitude=1,longitude=2)])]),dict(iso2='US',name='United States',states=[dict(id=2,name='California',cities=[dict(id=3,name='City / ../ label',latitude=30,longitude=-120,timezone='America/Los_Angeles')])])]

    def source(self,world=None):
        value=world if world is not None else self.world
        raw=gzip.compress(json.dumps(value).encode(),mtime=0)
        notices={name:('Original credit '+name).encode() for name in geo.NOTICES}
        counts=(len(value),sum(len(c['states']) for c in value),sum(len(s['cities']) for c in value for s in c['states']))
        patches=[patch.object(geo,'DIGEST',hashlib.sha256(raw).hexdigest()),patch.object(geo,'NOTICES',{name:hashlib.sha256(content).hexdigest() for name,content in notices.items()}),patch.object(geo,'EXPECTED_COUNTS',counts)]
        for item in patches:item.start();self.addCleanup(item.stop)
        def response(request,timeout):
            self.assertEqual(timeout,8);self.assertTrue(request.full_url.startswith(geo.BASE));self.assertNotIn('latest',request.full_url);self.assertNotIn('master',request.full_url)
            name=request.full_url[len(geo.BASE):]
            return io.BytesIO(raw if name==geo.ASSET else notices[name])
        return Mock(side_effect=response),notices

    def test_pins_and_license_are_fixed_without_runtime_latest_metadata(self):
        self.assertEqual(geo.SNAPSHOT,'v5.0.0-export.1')
        self.assertEqual(geo.DIGEST,'72cbb838c2004ccedc97fb18b10b2d8916fd9275bf227e9a4d26e814adc16eb8')
        self.assertEqual(len(geo.NOTICES),5);self.assertEqual(geo.EXPECTED_COUNTS,(250,5327,152378))
        self.assertEqual(geo.ATTRIBUTION['license'],'ODbL-1.0')

    def test_catalog_builds_all_parents_notices_cache_and_resolves_coordinates(self):
        opener,notices=self.source()
        countries=geo.countries_regions_cities('countries',opener=opener)
        self.assertEqual(countries['total'],2);self.assertTrue(countries['complete']);self.assertIsNone(countries['next_cursor'])
        self.assertEqual(countries['snapshot'],geo.SNAPSHOT)
        regions=geo.countries_regions_cities('regions','BR',opener=Mock(side_effect=AssertionError('cache missed')))
        self.assertEqual(regions['items'],[dict(id='1',name='Distrito Federal',country_id='BR')])
        cities=geo.countries_regions_cities('cities','BR','1',query='SAO',opener=Mock(side_effect=AssertionError('cache missed')))
        self.assertEqual([c['id'] for c in cities['items']],['2'])
        self.assertEqual(cities['items'][0]['timezone'],'auto')
        city=geo.resolve_city('1','BR','1');self.assertEqual(city['latitude'],-15.7939)
        for name,raw in notices.items():self.assertEqual((geo.cache_directory()/name).read_bytes(),raw)
        self.assertEqual(opener.call_count,6)
        self.assertEqual((geo.cache_directory()/'catalog.sqlite3').stat().st_mode&0o777,0o600)
        with self.assertRaises(geo.LocationError):geo.resolve_city('1','US','2')

    def test_pagination_total_and_query_do_not_claim_a_subset_is_complete(self):
        world=copy.deepcopy(self.world)
        world[0]['states'][0]['cities']=[dict(id=i+10,name=f'Place {i:03}',latitude=0,longitude=0) for i in range(105)]
        opener,_=self.source(world)
        page=geo.countries_regions_cities('cities','BR','1',opener=opener)
        self.assertEqual((page['total'],len(page['items']),page['next_cursor'],page['complete']),(105,100,'100',False))
        last=geo.countries_regions_cities('cities','BR','1',cursor='100')
        self.assertEqual(len(last['items']),5);self.assertIsNone(last['next_cursor']);self.assertFalse(last['complete'])
        filtered=geo.countries_regions_cities('cities','BR','1',query='Place 104')
        self.assertEqual(filtered['total'],1);self.assertTrue(filtered['complete'])

    def test_checksum_download_size_redirect_and_decompression_limits(self):
        with self.assertRaises(geo.LocationError) as caught:geo.download(geo.ASSET,geo.DIGEST,10,Mock(return_value=io.BytesIO(b'bad')))
        self.assertEqual(caught.exception.code,'checksum')
        with self.assertRaises(geo.LocationError):geo.download(geo.ASSET,'irrelevant',10,Mock(return_value=io.BytesIO(b'x'*11)))
        with self.assertRaises(geo.LocationError):geo.SafeRedirect().redirect_request(None,None,302,'',{},'https://evil.invalid/')
        with self.assertRaises(geo.LocationError):geo.SafeRedirect().redirect_request(None,None,302,'',{},'http://github.com/')
        with patch.object(geo,'MAX_EXPANDED',10),sqlite3.connect(':memory:') as connection:
            with self.assertRaises(geo.LocationError):geo._build(gzip.compress(b'['+b' '*1000+b']'),connection)

    def test_invalid_schema_ids_or_count_never_publish_index(self):
        world=copy.deepcopy(self.world);world[0]['states'][0]['cities'][0]['id']='../../unsafe'
        opener,_=self.source(world)
        with self.assertRaises(geo.LocationError):geo.countries_regions_cities('countries',opener=opener)
        self.assertFalse((geo.cache_directory()/'catalog.sqlite3').exists())
        self.assertEqual(list(geo.cache_directory().glob('.index-*')),[])

    def test_default_preferences_no_file_and_cas_preserves_other_field_and_permissions(self):
        before=geo.preferences();self.assertEqual(before['revision'],0);self.assertEqual(before['location']['id'],'builtin-brasilia')
        self.assertFalse(geo.preferences_directory().exists())
        changed=geo.set_preferences(unit='fahrenheit',expected=0)
        self.assertEqual(changed['revision'],1);self.assertEqual(changed['location'],before['location'])
        opener,_=self.source()
        chosen=geo.set_preferences(city_id='3',country='US',region='2',expected=1,opener=opener)
        self.assertEqual(chosen['unit'],'fahrenheit');self.assertEqual(chosen['revision'],2)
        self.assertEqual(chosen['location']['id'],'3')
        self.assertEqual(chosen['location']['country_name'],'United States')
        self.assertEqual(chosen['location']['region_name'],'California')
        path=geo.preferences_directory()/'weather.json';raw=path.read_bytes()
        self.assertEqual(path.stat().st_mode&0o777,0o600)
        with self.assertRaises(geo.LocationError) as caught:geo.set_preferences(unit='celsius',expected=1)
        self.assertEqual(caught.exception.code,'conflict');self.assertEqual(path.read_bytes(),raw)
        self.assertEqual(geo.preferences(),chosen)

    def test_invalid_preferences_and_symlink_are_preserved(self):
        directory=geo.preferences_directory();directory.mkdir(parents=True)
        path=directory/'weather.json';path.write_text('{broken')
        with self.assertRaises(geo.LocationError):geo.preferences()
        with self.assertRaises(geo.LocationError):geo.set_preferences(unit='fahrenheit')
        self.assertEqual(path.read_text(),'{broken');path.unlink()
        outside=self.root/'outside.json';outside.write_text('outside');path.symlink_to(outside)
        with self.assertRaises(geo.LocationError):geo.set_preferences(unit='fahrenheit')
        self.assertEqual(outside.read_text(),'outside')

    def test_optional_location_names_are_validated_and_old_preferences_still_read(self):
        geo.set_preferences(unit='fahrenheit')
        path=geo.preferences_directory()/'weather.json'
        old=json.loads(path.read_text())
        for field in geo.LOCATION_LABELS:old['location'].pop(field,None)
        path.write_text(json.dumps(old));raw=path.read_bytes()
        self.assertEqual(geo.preferences()['location'],old['location'])
        self.assertEqual(path.read_bytes(),raw)
        old['location']['country_name']='invalid\nlabel';path.write_text(json.dumps(old));raw=path.read_bytes()
        with self.assertRaises(geo.LocationError):geo.preferences()
        self.assertEqual(path.read_bytes(),raw)

    def test_busy_preferences_lock_does_not_write(self):
        fd=geo.directory(geo.preferences_directory(),True)
        try:
            with geo.locked(fd,'weather.lock'):
                with self.assertRaises(geo.LocationError) as caught:geo.set_preferences(unit='fahrenheit')
                self.assertEqual(caught.exception.code,'busy')
            self.assertFalse((geo.preferences_directory()/'weather.json').exists())
        finally:os.close(fd)

    def test_geocoded_selection_persists_without_catalog_and_keeps_unit_and_cas(self):
        item=dict(id=123,name='Brasília',admin1='Distrito Federal',country='Brazil',country_code='BR',latitude=-15.79,longitude=-47.88,timezone='America/Sao_Paulo')
        geo.set_preferences(unit='fahrenheit')
        output=[]
        with patch.object(geo,'catalog',side_effect=AssertionError('CSC must not load')):
            weather.main(['--set-geocoded-location',json.dumps(item),'--expected-revision','1'],output=output.append)
            saved=json.loads(output[-1].split(':',1)[1])
            self.assertTrue(saved['ok']);self.assertEqual(saved['revision'],2)
            self.assertEqual(saved['unit'],'fahrenheit')
            self.assertEqual(saved['location']['id'],'geonames:123')
            self.assertEqual(saved['location']['region_id'],'')
            self.assertEqual(saved['location']['region_name'],'Distrito Federal')
            self.assertEqual(saved['location']['country_name'],'Brazil')
            self.assertEqual(geo.preferences()['location'],saved['location'])
            weather.main(['--set-geocoded-location',json.dumps({**item,'name':'Other'}),'--expected-revision','1'],output=output.append)
            self.assertEqual(json.loads(output[-1].split(':',1)[1])['error_code'],'conflict')
            self.assertEqual(geo.preferences()['location'],saved['location'])
        self.assertFalse(geo.cache_directory().exists())

    def test_invalid_geocoded_selection_preserves_file_and_sanitizes_cli_errors(self):
        item=dict(id=123,name='City',country='Country',country_code='BR',latitude=0,longitude=0,timezone='UTC')
        geo.set_preferences(geocoded=item)
        path=geo.preferences_directory()/'weather.json';before=path.read_bytes()
        for field,bad in [('id',True),('id',-1),('name','Bad\nLabel'),('country_code','../'),('latitude',float('nan')),('longitude',True),('timezone','auto'),('admin1',[]),('admin1',None)]:
            with self.subTest(field=field,bad=bad):
                output=[];weather.main(['--set-geocoded-location',json.dumps({**item,field:bad})],output=output.append)
                self.assertTrue(output[0].startswith('AZCLOCK_WEATHER_PREFS:'))
                self.assertFalse(json.loads(output[0].split(':',1)[1])['ok'])
                self.assertEqual(path.read_bytes(),before)
        for raw in ('null','[]','{broken','['*1100+'0'+']'*1100,' '*16385):
            output=[];weather.main(['--set-geocoded-location',raw],output=output.append)
            self.assertFalse(json.loads(output[0].split(':',1)[1])['ok'])
            self.assertEqual(path.read_bytes(),before)

    def test_cli_preferences_catalog_and_conflict_prefixes(self):
        output=[];weather.main(['--preferences-json'],output=output.append)
        self.assertTrue(output[-1].startswith('AZCLOCK_WEATHER_PREFS:'));self.assertTrue(json.loads(output[-1].split(':',1)[1])['ok'])
        weather.main(['--set-unit','fahrenheit','--expected-revision','0'],output=output.append)
        self.assertEqual(json.loads(output[-1].split(':',1)[1])['unit'],'fahrenheit')
        weather.main(['--set-unit','celsius','--expected-revision','0'],output=output.append)
        self.assertEqual(json.loads(output[-1].split(':',1)[1])['error_code'],'conflict')
        opener,_=self.source();weather.main(['--geo-countries'],opener=opener,output=output.append)
        self.assertTrue(output[-1].startswith('AZCLOCK_GEOCATALOG:'));self.assertEqual(json.loads(output[-1].split(':',1)[1])['total'],2)
        weather.main(['--set-location','3','--country-code','US','--region-id','2','--expected-revision','1'],opener=opener,output=output.append)
        self.assertEqual(json.loads(output[-1].split(':',1)[1])['location']['id'],'3')

    def test_offline_failure_and_bad_query_are_safe_and_do_not_change_preferences(self):
        output=[];weather.main(['--geo-countries'],opener=Mock(side_effect=URLError('SECRET_REMOTE')),output=output.append)
        error=json.loads(output[-1].split(':',1)[1]);self.assertFalse(error['ok']);self.assertEqual(error['error_code'],'unavailable');self.assertNotIn('SECRET_REMOTE',output[-1])
        for cursor in ('-1','../../file','1;DROP TABLE cities'):
            with self.assertRaises(geo.LocationError):geo.countries_regions_cities('countries',cursor=cursor)
        self.assertEqual(geo.preferences()['revision'],0)
