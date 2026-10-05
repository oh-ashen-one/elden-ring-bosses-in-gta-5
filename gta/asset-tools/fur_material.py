# SPDX-License-Identifier: Apache-2.0
"""Flatten owned ER C[Fur] UV0 colour + UV2 strand maps for GTA's one UV set.

Geometry stays intact. Derived RGBA maps are lossless after shader adaptation;
overlapping UV0 islands select the highest-coverage strand sample explicitly.
"""
import numpy as np
from PIL import Image

def bake(geometries,base,strand,normal,fields,sample,tile=(1,1)):
    strand_float=strand.astype(np.float32);normal_float=normal.astype(np.float32)
    h=max(base.shape[0],strand.shape[0]);w=max(base.shape[1],strand.shape[1])
    out=np.asarray(Image.fromarray(base).resize((w,h),Image.Resampling.BILINEAR)).copy()
    colour=out[:,:,:3].copy();source_alpha=out[:,:,3].copy();out[:,:,3]=0
    bump=np.empty_like(out);bump[:]=[128,128,128,255];covered=np.zeros((h,w),bool)
    def unit(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-10)
    def basis(pos,uv,n):
        d1,d2=uv[1]-uv[0],uv[2]-uv[0];den=d1[0]*d2[1]-d1[1]*d2[0]
        if abs(den)<1e-10:return None
        tangent=((pos[1]-pos[0])*d2[1]-(pos[2]-pos[0])*d1[1])/den
        bitangent=((pos[2]-pos[0])*d1[0]-(pos[1]-pos[0])*d2[0])/den
        t=unit(tangent-n*np.sum(n*tangent,axis=-1,keepdims=True))
        b=unit(np.cross(n,t));b*=np.where(np.sum(b*bitangent,axis=-1,keepdims=True)<0,-1,1)
        return t,b
    for g in geometries:
        f=fields(g)
        if 'TexCoord2' not in f:raise ValueError('C[Fur] requires authored UV2 strand coordinates')
        triangles=np.fromstring(g.findtext('IndexBuffer/Data'),sep=' ',dtype=int).reshape(-1,3)
        for ids in triangles:
            uv=f['TexCoord0'][ids];secondary=f['TexCoord2'][ids]*np.asarray(tile);pos=f['Position'][ids]
            p=(uv-np.floor(uv.mean(0)))*[w-1,h-1];lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),[w-1,h-1])
            if (lo>hi).any():continue
            a,b,c=p;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
            a0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            a1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;a2=1-a0-a1
            inside=(a0>=-.001)&(a1>=-.001)&(a2>=-.001);weights=np.stack([a0,a1,a2],axis=-1)
            uv2=weights@secondary;s=sample(strand_float,uv2)
            region=(slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1));target=out[region]
            alpha=np.rint(s[:,:,3]*source_alpha[region]/255).astype(np.uint8);chosen=inside & (alpha>target[:,:,3])
            covered[region]|=inside
            if not chosen.any():continue
            n=sample(normal_float,uv2)
            rgb=np.rint(colour[region].astype(float)*s[:,:,:3]/255).clip(0,255).astype(np.uint8)
            target[chosen,:3]=rgb[chosen];target[chosen,3]=alpha[chosen];covered[region]|=inside
            smooth=unit(weights@f['Normal'][ids]);b0=basis(pos,uv,smooth);b2=basis(pos,secondary,smooth)
            if b0 is not None and b2 is not None:
                xy=n[:,:,:2]/127.5-1;xy/=np.maximum(1,np.linalg.norm(xy,axis=-1,keepdims=True));z=np.sqrt(np.maximum(0,1-np.sum(xy*xy,axis=-1)))
                world=b2[0]*xy[:,:,0,None]+b2[1]*xy[:,:,1,None]+smooth*z[:,:,None]
                mapped=np.stack([np.sum(world*b0[0],axis=-1),np.sum(world*b0[1],axis=-1)],axis=-1)
                dst=bump[region];dst[chosen,:2]=np.rint((mapped[chosen]+1)*127.5).clip(0,255).astype(np.uint8);dst[chosen,2]=n[chosen,2].round().clip(0,255).astype(np.uint8)
    if not covered.any():raise ValueError('No C[Fur] UV coverage')
    return out,bump,{'coverage_above_half':float((out[:,:,3]>=128).mean()),'authored_uv2_strands':True,'target_size':[w,h]}
