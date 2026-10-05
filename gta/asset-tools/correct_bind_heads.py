# SPDX-License-Identifier: Apache-2.0
"""Compensate bounded Blender cloth-joint head shifts before native skinning.

Preserves target bone axes/scales and all geometry. Reject large discrepancies;
do not relax the downstream source/target bind-position validation.
"""
import numpy as np
from rebuild_animation import matrix,world_matrices,split_matrix,Y_UP_TO_Z_UP

def source_axes(tree,source):
    """Restore source rest axes for rigs with animated nonuniform scaling.

    Bone names/tags/parents, vertex weights and positions are preserved. Native
    inverse binds are rebuilt from these same rest transforms by CodeWalker.
    """
    bones=tree.findall('Skeleton/Bones/Item');parents=[int(b.find('ParentIndex').get('value')) for b in bones]
    def v(b,tag,axes):return [float(b.find(tag).get(a)) for a in axes]
    worlds=world_matrices([matrix(v(b,'Translation','xyz'),v(b,'Rotation','xyzw'),v(b,'Scale','xyz')) for b in bones],parents)
    for i,b in enumerate(bones):
        if b.findtext('Name') in source.names:worlds[i]=Y_UP_TO_Z_UP@source.rest[source.names[b.findtext('Name')]]
    for i,b in enumerate(bones):
        t,q,s=split_matrix(worlds[i] if parents[i]<0 else np.linalg.inv(worlds[parents[i]])@worlds[i])
        for tag,values,axes in [('Translation',t,'xyz'),('Rotation',q,'xyzw'),('Scale',s,'xyz')]:
            for a,x in zip(axes,values):b.find(tag).set(a,format(float(x),'.12g'))
    return {'source_rest_axes_restored':True,'bones':len(bones)}

def correct(tree,source,maximum=.02):
    bones=tree.findall('Skeleton/Bones/Item');parents=[int(b.find('ParentIndex').get('value')) for b in bones]
    def v(b,tag,axes):return [float(b.find(tag).get(a)) for a in axes]
    local=[matrix(v(b,'Translation','xyz'),v(b,'Rotation','xyzw'),v(b,'Scale','xyz')) for b in bones]
    worlds=world_matrices(local,parents);desired=worlds.copy();report=[]
    for i,b in enumerate(bones):
        name=b.findtext('Name')
        if name not in source.names:continue
        position=(Y_UP_TO_Z_UP@source.rest[source.names[name]])[:3,3]
        error=float(np.linalg.norm(worlds[i,:3,3]-position))
        if error>maximum:raise ValueError('Unexpected bind displacement: '+name)
        desired[i,:3,3]=position
        if error>.00001:report.append({'bone':name,'head_correction_m':error})
    for i,b in enumerate(bones):
        value=desired[i] if parents[i]<0 else np.linalg.inv(desired[parents[i]])@desired[i]
        # Full world rotations are unchanged, so their original local rotation
        # and scale can be retained without a new quaternion decomposition.
        for a,x in zip('xyz',value[:3,3]):b.find('Translation').set(a,format(float(x),'.9g'))
    return report
