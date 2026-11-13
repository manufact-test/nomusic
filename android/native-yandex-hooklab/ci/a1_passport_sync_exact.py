"""Strict clone-owned outer resource repair; never touch nested original or auth logic."""
from __future__ import annotations
import struct

class PassportResourceMismatch(ValueError):
    pass

def _chunk(d, p):
    if p < 0 or p+8 > len(d):
        raise PassportResourceMismatch('RESOURCE_BOUNDS')
    t,h,n = struct.unpack_from('<HHI', d, p)
    if h < 8 or n < h or p+n > len(d):
        raise PassportResourceMismatch('RESOURCE_CHUNK_INVALID')
    return t,h,n

def _len8(d,p):
    a=d[p];p+=1
    return (((a&127)<<8)|d[p],p+1) if a&128 else (a,p)

def _putlen(n):
    if not 0<=n<32768:
        raise PassportResourceMismatch('RESOURCE_LENGTH_UNSUPPORTED')
    return bytes((n,)) if n<128 else bytes((128|(n>>8),n&255))

def _strings(d):
    t,h,n=_chunk(d,12)
    if t!=1 or h!=28:
        raise PassportResourceMismatch('GLOBAL_POOL_EXPECTED')
    count,styles,flags,start,sty_start=struct.unpack_from('<5I',d,20)
    if flags!=256 or start < h+4*(count+styles) or start>n:
        raise PassportResourceMismatch('UTF8_GLOBAL_POOL_REQUIRED')
    if styles and not start<=sty_start<n:
        raise PassportResourceMismatch('STYLES_UNSUPPORTED')
    offs=[struct.unpack_from('<I',d,12+h+i*4)[0] for i in range(count)]
    records=[]
    for o in offs:
        p=12+start+o
        nch,p=_len8(d,p)
        size,p=_len8(d,p)
        if p+size>=12+n or d[p+size]!=0:
            raise PassportResourceMismatch('RESOURCE_STRING_BOUNDS')
        value=d[p:p+size].decode('utf8')
        if len(value.encode('utf-16le'))//2!=nch:
            raise PassportResourceMismatch('RESOURCE_STRING_LENGTH_DRIFT')
        records.append((value,p+size+1))
    return records,offs,dict(size=n,start=start,styles=styles,styles_start=sty_start,header=h)

def rewrite_exact_sync_authority(d,original_package,clone_package):
    """Only the own-clone Passport sync provider authority."""
    if original_package!='ru.yandex.music' or clone_package!='pro.celikom.yandex.nativeclonelab':
        raise PassportResourceMismatch('RESOURCE_UNEXPECTED_SYNC_IDENTITIES')
    return _rewrite_exact_string(d,
        'com.yandex.passport.sync.'+original_package,
        'com.yandex.passport.sync.'+clone_package)

def rewrite_exact_owned_account_type(d, original_package, clone_package):
    """Independent account type legitimately OWNED by our authenticator.

    This does not change code, impersonate a publisher certificate, access the
    publisher's accounts or bypass Android's account ownership permission.
    """
    if original_package!='ru.yandex.music' or clone_package!='pro.celikom.yandex.nativeclonelab':
        raise PassportResourceMismatch('RESOURCE_UNEXPECTED_ACCOUNT_IDENTITIES')
    return _rewrite_exact_string(d,'com.yandex.passport',clone_package+'.passport')

def _rewrite_exact_string(d,old,new):
    """Rewrite one unique UTF8 pool value; untouched strings and chunks are identical."""
    if (not isinstance(d,bytes) or not old or not new or old==new
        or '\0' in old or '\0' in new):
        raise PassportResourceMismatch('RESOURCE_INPUT_INVALID')
    t,h,n=_chunk(d,0)
    if t!=2 or h!=12 or n!=len(d) or struct.unpack_from('<I',d,8)[0]!=1:
        raise PassportResourceMismatch('RESOURCE_TABLE_EXPECTED')
    pool,offs,meta=_strings(d)
    hits=[i for i,(s,_) in enumerate(pool) if s==old]
    if len(hits)!=1 or new in (x[0] for x in pool):
        raise PassportResourceMismatch('RESOURCE_EXACT_OLD_VALUE_REQUIRED')
    idx=hits[0]
    if offs.count(offs[idx])!=1:
        raise PassportResourceMismatch('RESOURCE_ALIASED_STRING_OFFSET')
    begin=12+meta['start']+offs[idx]
    end=pool[idx][1]
    new_bytes=new.encode('utf8')
    replacement=_putlen(len(new.encode('utf-16le'))//2)+_putlen(len(new_bytes))+new_bytes+b'\0'
    delta=len(replacement)-(end-begin)
    sty=meta['styles_start']
    tail=12+(sty if sty else meta['size'])
    if end>tail:
        raise PassportResourceMismatch('RESOURCE_STRING_STYLES_OVERLAP')
    pad=(-(meta['size']+delta))%4
    newpool=bytearray(d[12:begin])+replacement+d[end:tail]+b'\0'*pad+d[tail:12+meta['size']]
    shift=len(newpool)-meta['size']
    if shift!=delta+pad:
        raise PassportResourceMismatch('RESOURCE_POOL_SHIFT_INVALID')
    struct.pack_into('<I',newpool,4,len(newpool))
    if sty:
        struct.pack_into('<I',newpool,24,sty+shift)
    for i,o in enumerate(offs):
        struct.pack_into('<I',newpool,meta['header']+4*i,o+delta if o>offs[idx] else o)
    out=bytearray(d[:12])+newpool+d[12+meta['size']:]
    struct.pack_into('<I',out,4,len(out))
    final=bytes(out)
    check,_,_=_strings(final)
    if (len(check)!=len(pool) or check[idx][0]!=new or
        any(i!=idx and a[0]!=b[0] for i,(a,b) in enumerate(zip(pool,check))) or
        final[12+len(newpool):]!=d[12+meta['size']:]):
        raise PassportResourceMismatch('RESOURCE_SINGLE_STRING_PARITY_FAILED')
    return final
