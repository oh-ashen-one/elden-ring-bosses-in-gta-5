# SPDX-License-Identifier: Apache-2.0
"""Keep each drawable geometry's skin indices within the native byte range.

Skeletons may exceed 256 bones; each vertex buffer addresses its local palette.
Preserve every weighted GLOBAL joint association while compacting that palette.
"""
import numpy as np
from upgrade_visuals import SIZES

def identity(drawable):
    """Animated GTA object path: use global indices when the rig fits a byte.

    Local per-geometry palettes passed CodeWalker checks but visibly scattered
    the object's parts in GTA. Full identity palettes restore the working path.
    Larger rigs require a separately verified strategy; never wrap their IDs.
    """
    count=len(drawable.findall('Skeleton/Bones/Item'))
    if not 0<count<=256:raise ValueError('Identity skin indices require <=256 bones')
    reports=[]
    for geometry in drawable.findall('.//Geometries/Item'):
        ids=geometry.find('BoneIDs')
        if ids is None or not ids.text:continue
        palette=np.array([int(v) for v in ids.text.split(',')]);vb=geometry.find('VertexBuffer');names=[n.tag for n in vb.find('Layout')]
        widths=[SIZES[n] for n in names];data=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,sum(widths))
        wi=sum(widths[:names.index('BlendWeights')]);ii=sum(widths[:names.index('BlendIndices')]);active=data[:,wi:wi+4]>0
        old=data[:,ii:ii+4].astype(int);new=np.zeros_like(old);new[active]=palette[old[active]]
        if (new<0).any() or (new>=count).any():raise ValueError('Global skin index outside skeleton')
        data[:,ii:ii+4]=new;ids.text=', '.join(map(str,range(count)))
        vb.find('Data').text='\n'+'\n'.join(' '.join(format(float(v),'.9g') for v in row) for row in data)+'\n'
        reports.append({'old_palette':len(palette),'new_palette':count,'global_identity_indices':True,'weighted_global_joints_preserved':True})
    return reports

def compact(drawable):
    reports=[]
    for geometry in drawable.findall('.//Geometries/Item'):
        ids=geometry.find('BoneIDs')
        if ids is None or not ids.text:continue
        palette=np.array([int(v) for v in ids.text.split(',')])
        vb=geometry.find('VertexBuffer');names=[n.tag for n in vb.find('Layout')]
        widths=[SIZES[n] for n in names];data=np.fromstring(vb.findtext('Data'),sep=' ').reshape(-1,sum(widths))
        wi=sum(widths[:names.index('BlendWeights')]);ii=sum(widths[:names.index('BlendIndices')])
        weights=data[:,wi:wi+4];indices=data[:,ii:ii+4].astype(int);active=weights>0
        if (indices[active]<0).any() or (indices[active]>=len(palette)).any():raise ValueError('Skin index outside old palette')
        before=palette[indices[active]];used=np.unique(before)
        if len(used)>256:raise ValueError('Geometry needs bone-aware partitioning before native export')
        remap={int(old):new for new,old in enumerate(used)};new_indices=np.zeros_like(indices)
        for row,lane in np.argwhere(active):new_indices[row,lane]=remap[int(palette[indices[row,lane]])]
        if not np.array_equal(used[new_indices[active]],before):raise ValueError('Skin association changed')
        data[:,ii:ii+4]=new_indices
        ids.text=', '.join(str(int(i)) for i in used)
        vb.find('Data').text='\n'+'\n'.join(' '.join(format(float(v),'.9g') for v in row) for row in data)+'\n'
        reports.append({'old_palette':len(palette),'new_palette':len(used),'weighted_global_joints_preserved':True})
    return reports
