#!/usr/bin/env python3
"""Strict, opt-in repair of just a clone-owned resources.arsc package name.

Input must be bytes from a disposable CELIKOM APK, not the original vendor
APK or the nested signed LSPatch origin. Preserves every ID, value and byte
outside one fixed 256-byte UTF-16LE package-name field.
"""
from __future__ import annotations
import struct
import re

TABLE_TYPE=0x0002
PACKAGE_TYPE=0x0200
NAME_OFFSET=12
NAME_LENGTH=256

class InvalidResourceTable(ValueError):
    pass

def _chunk(data,off,limit):
    if off<0 or off+8>limit:raise InvalidResourceTable("TRUNCATED_CHUNK")
    kind,head,size=struct.unpack_from("<HHI",data,off)
    if head<8 or size<head or off+size>limit:
        raise InvalidResourceTable("INVALID_CHUNK_BOUNDS")
    return kind,head,size

def _name(data,off):
    raw=data[off+NAME_OFFSET:off+NAME_OFFSET+NAME_LENGTH]
    if len(raw)!=NAME_LENGTH:raise InvalidResourceTable("INVALID_NAME_BOUNDS")
    try:
        s=raw.decode("utf-16le")
    except UnicodeError as e:
        raise InvalidResourceTable("INVALID_UTF16") from e
    if "\0" not in s:raise InvalidResourceTable("UNTERMINATED_NAME")
    name,padding=s.split("\0",1)
    if padding.strip("\0"):raise InvalidResourceTable("NAME_PADDING_NOT_ZERO")
    return name

def package_names(data):
    if not isinstance(data,bytes):raise InvalidResourceTable("BYTES_REQUIRED")
    kind,head,size=_chunk(data,0,len(data))
    if kind!=TABLE_TYPE or head<12 or size!=len(data):
        raise InvalidResourceTable("NOT_RESOURCE_TABLE")
    expected=struct.unpack_from("<I",data,8)[0]
    if not 1<=expected<=64:raise InvalidResourceTable("UNEXPECTED_PACKAGE_COUNT")
    result=[]
    off=head
    while off<size:
        child,ch,sz=_chunk(data,off,size)
        if child==PACKAGE_TYPE:
            if ch<NAME_OFFSET+NAME_LENGTH:
                raise InvalidResourceTable("SHORT_PACKAGE_HEADER")
            result.append(_name(data,off))
        off+=sz
    if off!=size or len(result)!=expected:
        raise InvalidResourceTable("PACKAGE_COUNT_DRIFT")
    return tuple(result)

def rewrite_exact_namespace(data,old,new):
    if (not isinstance(old,str) or not isinstance(new,str)
        or not old or not new or old==new or "\0" in old or "\0" in new
        or len(new.encode("utf-16le"))>=NAME_LENGTH):
        raise InvalidResourceTable("UNSAFE_NAMESPACE")
    names=package_names(data)
    if names.count(old)!=1 or new in names:
        raise InvalidResourceTable("NAMESPACE_NOT_UNIQUE")
    out=bytearray(data)
    start=struct.unpack_from("<H",data,2)[0]
    updated=0
    for off in _offsets(data,start):
        kind,head,size=_chunk(data,off,len(data))
        if kind==PACKAGE_TYPE and _name(data,off)==old:
            b=new.encode("utf-16le")
            field=off+NAME_OFFSET
            out[field:field+NAME_LENGTH]=b+b"\0"*(NAME_LENGTH-len(b))
            updated+=1
    result=bytes(out)
    if updated!=1 or len(result)!=len(data) or new not in package_names(result):
        raise InvalidResourceTable("NAMESPACE_REWRITE_FAILED")
    return result

def _offsets(data,off):
    while off<len(data):
        yield off
        _,_,size=_chunk(data,off,len(data))
        off+=size


def classify_outer_signing_change(name):
    """Only classify a ZIP member name; NEVER log private member names or bytes.

    This is a *diagnostic* classification, not authorization to mutate content.
    """
    if name == "META-INF/MANIFEST.MF":
        return "V1_MANIFEST"
    if re.fullmatch(r"META-INF/[A-Za-z0-9_-]+\.SF", name, re.IGNORECASE):
        return "V1_SIGNATURE_FILE"
    if re.fullmatch(r"META-INF/[A-Za-z0-9_-]+\.(?:RSA|DSA|EC)", name, re.IGNORECASE):
        return "V1_SIGNATURE_BLOCK"
    if name.startswith("META-INF/"):
        return "OTHER_META_INF"
    return "NON_META_INF_APP_CONTENT"

def only_expected_own_v1_signing_changes(names):
    """Exactly three existing, matching top-level V1 signature entries.

    The full ZIP-member parity check and independent signer certificate
    equality are separate mandatory checks. This never exempts arbitrary
    META-INF files, vendor data, nested APKs, DEX, native libs or assets.
    """
    if len(names)!=3 or len(set(names))!=3:
        return False
    categories={}
    for name in names:
        category=classify_outer_signing_change(name)
        categories.setdefault(category,[]).append(name)
    if {key:len(value) for key,value in categories.items()} != {
        "V1_MANIFEST":1,"V1_SIGNATURE_FILE":1,"V1_SIGNATURE_BLOCK":1}:
        return False
    signer_sf=categories["V1_SIGNATURE_FILE"][0]
    signer_block=categories["V1_SIGNATURE_BLOCK"][0]
    return signer_sf.rsplit(".",1)[0]==signer_block.rsplit(".",1)[0]
