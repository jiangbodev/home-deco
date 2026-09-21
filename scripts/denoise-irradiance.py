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
for kind in ['floor','wall']:
 info=plan[kind];w,h=info['width'],info['height'];raw=(folder/(kind+'.rgba32f')).read_bytes();assert len(raw)==w*h*16
 source=C.create_string_buffer(raw,len(raw));output=C.create_string_buffer(raw,len(raw));f=newfilter(device,b'RT');check();api('oidnSetFilterBool',None,ptr,C.c_char_p,C.c_bool)(f,b'hdr',True)
 setimage(f,b'color',source,3,w,h,0,16,w*16);setimage(f,b'output',output,3,w,h,0,16,w*16);commit(f);check();execute(f);check();release(f)
 (folder/(kind+'.denoised.rgba32f')).write_bytes(output.raw);print('Denoised',kind,w,h,flush=True)
api('oidnReleaseDevice',None,ptr)(device)
