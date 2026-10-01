# SPDX-License-Identifier: Apache-2.0
"""Validate registration of this project's script-spawned creature props."""
from xml.etree import ElementTree as ET


def validate_registration(setup_path, content_path):
    setup = ET.parse(setup_path).getroot()
    content = ET.parse(content_path).getroot()
    startup = {n.text for n in setup.findall('contentChangeSetGroups/Item')
               if n.findtext('NameHash') == 'GROUP_STARTUP'
               for n in n.findall('ContentChangeSets/Item')}
    enabled = {n.text for c in content.findall('contentChangeSets/Item')
               if c.findtext('changeSetName') in startup for n in c.findall('filesToEnable/Item')}
    files = content.findall('dataFiles/Item')
    requests = [n for n in files if n.findtext('fileType') == 'DLC_ITYP_REQUEST']
    if not requests: raise ValueError('Creature DLC has no archetype registration request')
    for request in requests:
        if request.findtext('contents') != 'CONTENTS_PROPS':
            raise ValueError('Creature archetypes must register as CONTENTS_PROPS for object creation')
    for entry in files:
        if entry.find('disabled') is not None and entry.find('disabled').get('value') == 'true':
            if entry.findtext('filename') not in enabled:
                raise ValueError('Disabled DLC file is never enabled by GROUP_STARTUP')
    return len(requests)
