# SPDX-License-Identifier: Apache-2.0
import importlib.util
import math
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as E
s=importlib.util.spec_from_file_location('ground',Path(__file__).parents[1]/'asset-tools/align_ground_contact.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class GroundContact(unittest.TestCase):
 def fixture(self):
  root=E.Element('Drawable');E.SubElement(root,'BoundingBoxMin',x='-2',y='-1',z='-1');bound=E.SubElement(root,'Bounds',type='Composite');child=E.SubElement(E.SubElement(bound,'Children'),'Item',type='Box')
  for item in [bound,child]:
   E.SubElement(item,'BoxMin',x='-2',y='-1',z='-1');E.SubElement(item,'BoxMax',x='2',y='1',z='3');E.SubElement(item,'Volume',value='32');E.SubElement(item,'Inertia',x='1',y='1',z='1');E.SubElement(item,'SphereCenter',x='0',y='0',z='0');E.SubElement(item,'SphereRadius',value='2')
  E.SubElement(child,'CompositeTransform').text='1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1';return root
 def test_floor_moves_without_changing_render_bounds(self):
  root=self.fixture();old=m.adjust(root,-0.1);self.assertEqual(old,[-1,-1]);self.assertEqual(root.find('BoundingBoxMin').get('z'),'-1')
  for item in [root.find('Bounds'),root.find('Bounds/Children/Item')]:
   self.assertEqual(float(item.find('BoxMin').get('z')),-.1);self.assertAlmostEqual(float(item.find('Volume').get('value')),24.8)
   self.assertGreaterEqual(float(item.find('SphereRadius').get('value')),math.sqrt(14)-1e-7)
 def test_runtime_and_packager_floor_references_match(self):
  source=(Path(__file__).parents[1]/'src/combat.hpp').read_text()
  for _,(name,floor) in m.CONTACTS.items():
   block=source[source.index('"'+name+'"'):].split('}',1)[0]
   runtime=float(re.search(r',\s*(-?[0-9.]+)f\s*$',block).group(1))
   self.assertEqual(runtime,floor)
 def test_unknown_shape_transform_and_invalid_floor_rejected(self):
  r=self.fixture();r.find('Bounds/Children/Item').set('type','Capsule')
  with self.assertRaises(ValueError):m.adjust(r,0)
  r=self.fixture();r.find('Bounds/Children/Item/CompositeTransform').text='0 '*16
  with self.assertRaises(ValueError):m.adjust(r,0)
  for value in [float('nan'),4,-2]:
   with self.assertRaises(ValueError):m.adjust(self.fixture(),value)

if __name__=='__main__':unittest.main()
