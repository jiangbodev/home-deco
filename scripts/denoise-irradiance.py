"""Offline OIDN RT HDR denoising (the bundled Blender library omits RTLightmap weights); no web runtime dependency.
API reference: https://www.openimagedenoise.org/documentation.html#rt
"""
import ctypes as C,json,sys,os
from pathlib import Path
folder=Path(sys.argv[1]);library=os.environ.get('HOME_DECO_OIDN','/Applications/Blender.app/Contents/Resources/lib/libOpenImageDenoise.dylib')
lib=C.CDLL(library)
def api(name,restype,*types):
 fn=getattr(lib,name);fn.restype=restype;fn.argtypes=types;return fn
ptr=C.c_void_p;size=C.c_size_t
newdev=api('oidnNewDevice',ptr,C.c_int);commitdev=api('oidnCommitDevice',None,ptr);newfilter=api('oidnNewFilter',ptr,ptr,C.c_char_p)
setimage=api('oidnSetSharedFilterImage',None,ptr,C.c_char_p,ptr,C.c_int,size,size,size,size,size)
commit=api('oidnCommitFilter',None,ptr);execute=api('oidnExecuteFilter',None,ptr);release=api('oidnReleaseFilter',None,ptr);error=api('oidnGetDeviceError',C.c_int,ptr,C.POINTER(C.c_char_p))
device=newdev(1);commitdev(device)
def check():
 msg=C.c_char_p();code=error(device,C.byref(msg))
 if code:raise RuntimeError(msg.value.decode())
check();plan=json.loads((folder/'plan.json').read_text())
import numpy as np
def denoise(raw,w,h):
 source=C.create_string_buffer(raw,len(raw));output=C.create_string_buffer(raw,len(raw));f=newfilter(device,b'RT');check();api('oidnSetFilterBool',None,ptr,C.c_char_p,C.c_bool)(f,b'hdr',True)
 setimage(f,b'color',source,3,w,h,0,16,w*16);setimage(f,b'output',output,3,w,h,0,16,w*16);commit(f);check();execute(f);check();release(f)
 return np.frombuffer(output.raw,dtype=np.float32).reshape(h,w,4).copy()
for kind in ['floor','wall']:
 info=plan[kind];w,h=info['width'],info['height'];raw=(folder/(kind+'.rgba32f')).read_bytes();assert len(raw)==w*h*16
 source=np.frombuffer(raw,dtype=np.float32).reshape(h,w,4);result=source.copy()
 if kind=='floor':result=denoise(raw,w,h)
 else:
  # Atlas islands are unrelated surfaces. Never let the denoiser borrow another island's colors.
  for index,r in enumerate(info['receivers']):
   for rect in r['rects']:
    x,y,rw,rh=[round(v*(w if i%2==0 else h)) for i,v in enumerate(rect)]
    tile=source[y:y+rh,x:x+rw].copy();pad=16
    padded=np.pad(tile,((pad,pad),(pad,pad),(0,0)),mode='edge')
    clean=denoise(padded.tobytes(),rw+pad*2,rh+pad*2)[pad:pad+rh,pad:pad+rw]
    # Low-density irradiance charts store broad transport, not material texture.
    # A small spatial filter removes residual Monte Carlo grain at 32 texels/metre.
    sigma=2.5;radius=6;kernel=np.exp(-np.arange(-radius,radius+1,dtype=np.float32)**2/(2*sigma*sigma));kernel/=kernel.sum()
    for axis in [0,1]:
     padding=[(0,0),(0,0),(0,0)];padding[axis]=(radius,radius);extended=np.pad(clean,padding,mode='edge');smooth=np.zeros_like(clean)
     for k,weight in enumerate(kernel):
      slices=[slice(None),slice(None),slice(None)];slices[axis]=slice(k,k+clean.shape[axis]);smooth+=extended[tuple(slices)]*weight
     clean=smooth
    # Dilation is confined to this chart's gutter; avoid bilinear seams at the edges.
    result[y-3:y+rh+3,x-3:x+rw+3]=np.pad(clean,((3,3),(3,3),(0,0)),mode='edge')
   if index%100==0:print('Chart denoise',index,flush=True)
 result[:,:,3]=source[:,:,3]
 result.tofile(folder/(kind+'.denoised.rgba32f'));print('Denoised',kind,w,h,flush=True)
api('oidnReleaseDevice',None,ptr)(device)
