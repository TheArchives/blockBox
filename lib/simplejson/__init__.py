__version__ = '2.1.1'
__all__ = [
    'dump', 'dumps', 'load', 'loads',
    'JSONDecoder', 'JSONDecodeError', 'JSONEncoder',
    'OrderedDict',
]

__author__ = 'Bob Ippolito <bob@redivi.com>'

from decimal import Decimal

from decoder import JSONDecoder, JSONDecodeError
from encoder import JSONEncoder
def _import_OrderedDict():
    import collections
    try:
        return collections.OrderedDict
    except AttributeError:
        import ordered_dict
        return ordered_dict.OrderedDict
OrderedDict = _import_OrderedDict()

def _import_c_make_encoder():
    try:
        from lib.simplejson._speedups import make_encoder
        return make_encoder
    except ImportError:
        return None

_default_encoder = JSONEncoder(
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    encoding='utf-8',
    default=None,
    use_decimal=False,
)

def dump(obj, fp, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, cls=None, indent=None, separators=None,
        encoding='utf-8', default=None, use_decimal=False, **kw):

    # cached encoder
    if (not skipkeys and ensure_ascii and
        check_circular and allow_nan and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and default is None and not kw):
        iterable = _default_encoder.iterencode(obj)
    else:
        if cls is None:
            cls = JSONEncoder
        iterable = cls(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
            check_circular=check_circular, allow_nan=allow_nan, indent=indent,
            separators=separators, encoding=encoding,
            default=default, use_decimal=use_decimal, **kw).iterencode(obj)
    # could accelerate with writelines in some versions of Python, at
    # a debuggability cost
    for chunk in iterable:
        fp.write(chunk)


def dumps(obj, skipkeys=False, ensure_ascii=True, check_circular=True,
        allow_nan=True, cls=None, indent=None, separators=None,
        encoding='utf-8', default=None, use_decimal=False, **kw):
    # cached encoder
    if (not skipkeys and ensure_ascii and
        check_circular and allow_nan and
        cls is None and indent is None and separators is None and
        encoding == 'utf-8' and default is None and not use_decimal
        and not kw):
        return _default_encoder.encode(obj)
    if cls is None:
        cls = JSONEncoder
    return cls(
        skipkeys=skipkeys, ensure_ascii=ensure_ascii,
        check_circular=check_circular, allow_nan=allow_nan, indent=indent,
        separators=separators, encoding=encoding, default=default,
        use_decimal=use_decimal, **kw).encode(obj)


_default_decoder = JSONDecoder(encoding=None, object_hook=None,
                               object_pairs_hook=None)


def load(fp, encoding=None, cls=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None,
        use_decimal=False, **kw):
    return loads(fp.read(),
        encoding=encoding, cls=cls, object_hook=object_hook,
        parse_float=parse_float, parse_int=parse_int,
        parse_constant=parse_constant, object_pairs_hook=object_pairs_hook,
        use_decimal=use_decimal, **kw)


def loads(s, encoding=None, cls=None, object_hook=None, parse_float=None,
        parse_int=None, parse_constant=None, object_pairs_hook=None,
        use_decimal=False, **kw):
    if (cls is None and encoding is None and object_hook is None and
            parse_int is None and parse_float is None and
            parse_constant is None and object_pairs_hook is None
            and not use_decimal and not kw):
        return _default_decoder.decode(s)
    if cls is None:
        cls = JSONDecoder
    if object_hook is not None:
        kw['object_hook'] = object_hook
    if object_pairs_hook is not None:
        kw['object_pairs_hook'] = object_pairs_hook
    if parse_float is not None:
        kw['parse_float'] = parse_float
    if parse_int is not None:
        kw['parse_int'] = parse_int
    if parse_constant is not None:
        kw['parse_constant'] = parse_constant
    if use_decimal:
        if parse_float is not None:
            raise TypeError("use_decimal=True implies parse_float=Decimal")
        kw['parse_float'] = Decimal
    return cls(encoding=encoding, **kw).decode(s)


def _toggle_speedups(enabled):
    import lib.simplejson.decoder as dec
    import lib.simplejson.encoder as enc
    import lib.simplejson.scanner as scan
    c_make_encoder = _import_c_make_encoder()
    if enabled:
        dec.scanstring = dec.c_scanstring or dec.py_scanstring
        enc.c_make_encoder = c_make_encoder
        enc.encode_basestring_ascii = (enc.c_encode_basestring_ascii or 
            enc.py_encode_basestring_ascii)
        scan.make_scanner = scan.c_make_scanner or scan.py_make_scanner
    else:
        dec.scanstring = dec.py_scanstring
        enc.c_make_encoder = None
        enc.encode_basestring_ascii = enc.py_encode_basestring_ascii
        scan.make_scanner = scan.py_make_scanner
    dec.make_scanner = scan.make_scanner
    global _default_decoder
    _default_decoder = JSONDecoder(
        encoding=None,
        object_hook=None,
        object_pairs_hook=None,
    )
    global _default_encoder
    _default_encoder = JSONEncoder(
       skipkeys=False,
       ensure_ascii=True,
       check_circular=True,
       allow_nan=True,
       indent=None,
       separators=None,
       encoding='utf-8',
       default=None,
   )
