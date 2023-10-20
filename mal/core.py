import copy, time, os
from itertools import chain

from . import  mal_types as types
from .mal_types import MalException, List, Vector
from . import  mal_readline
from . import  reader
from . import  printer

from functools import reduce
from operator import and_, gt,lt,le,ge,ne,add, sub, mul, floordiv, mod, pow
import math

# Errors/Exceptions
def throw(obj): raise MalException(obj)


# String functions
def pr_str(*args):
    return " ".join(map(lambda exp: printer._pr_str(exp, True), args))

def do_str(*args):
    return "".join(map(lambda exp: printer._pr_str(exp, False), args))

def prn(*args):
    print(" ".join(map(lambda exp: printer._pr_str(exp, True), args)))
    return None

def println(*args):
    print(" ".join(map(lambda exp: printer._pr_str(exp, False), args)))
    return None


# Hash map functions
def assoc(src_hm, *key_vals):
    hm = copy.copy(src_hm)
    for i in range(0,len(key_vals),2): hm[key_vals[i]] = key_vals[i+1]
    return hm

def dissoc(src_hm, *keys):
    hm = copy.copy(src_hm)
    for key in keys:
        hm.pop(key, None)
    return hm

def get(hm, key, default=None):
    if hm is not None and key in hm:
        return hm.get(key)
    else:
        return default

def contains_Q(hm, key): return key in hm

def keys(hm): return types._list(*hm.keys())

def vals(hm): return types._list(*hm.values())


# Sequence functions
def coll_Q(coll): return sequential_Q(coll) or hash_map_Q(coll)

def cons(x, seq): return List([x]) + List(seq)

def concat(*lsts): 
    list_seq = [item if item is not None else [] for item in lsts]
    return List(chain(*list_seq))

def mapcat(f, *lst): return list(chain.from_iterable(map(f, *lst)))

def interleave(*iterables):
    return list(chain.from_iterable(zip(*iterables)))

def map_indexed(func, iterable):
    return list(map(lambda item: func(item[0], item[1]), enumerate(iterable)))


def nth(lst, idx):
    if idx < len(lst): return lst[idx]
    else: throw("nth: index out of range")

def first(lst):
    if types._nil_Q(lst): return None
    else: return lst[0]

def rest(lst):
    if types._nil_Q(lst): return List([])
    else: return List(lst[1:])

def empty_Q(lst): return len(lst) == 0

def count(lst):
    if types._nil_Q(lst): return 0
    else: return len(lst)

def apply(f, *args): return f(*(list(args[0:-1])+args[-1]))

def mapf(f, *lst): return List(map(f, *lst))

def range_(start, end, step): return list(range(start,end,step))

def select_keys(dict, keys_list): return {k: dict[k] for k in keys_list if k in dict}

def partition(*args):
    """
    Partitions `coll` into chunks of size `n`, with an optional step size between chunks.
    If `pad` is provided, the last chunk is filled up with elements from `pad`.
    """
    if len(args) == 2:
        n, coll = args
        step = n
        pad = None
    elif len(args) == 3:
        n, step, coll = args
        pad = None
    elif len(args) == 4:
        n, step, coll, pad = args
    else:
        raise ValueError("Invalid number of arguments.")

    if step == 0:
        raise ValueError("Step must be a non-zero value.")
        
    result = []
    i = 0
    while i < len(coll):
        slice_ = coll[i:i+n]
        if pad and len(slice_) < n:
            slice_.extend(pad[:(n-len(slice_))])
        result.append(slice_)
        i += step
    return result



# retains metadata
def conj(lst, *args):
    if types._list_Q(lst): 
        new_lst = List(list(reversed(list(args))) + lst)
    else:
        new_lst = Vector(lst + list(args))
    if hasattr(lst, "__meta__"):
        new_lst.__meta__ = lst.__meta__
    return new_lst

def seq(obj):
    if types._list_Q(obj):
        return obj if len(obj) > 0 else None
    elif types._vector_Q(obj):
        return List(obj) if len(obj) > 0 else None
    elif types._string_Q(obj):
        return List([c for c in obj]) if len(obj) > 0 else None
    elif obj == None:
        return None
    else: throw ("seq: called on non-sequence")

# Metadata functions
def with_meta(obj, meta):
    new_obj = types._clone(obj)
    new_obj.__meta__ = meta
    return new_obj

def meta(obj):
    return getattr(obj, "__meta__", None)


# Atoms functions
def deref(atm):    return atm.val
def reset_BANG(atm,val):
    atm.val = val
    return atm.val
def swap_BANG(atm,f,*args):
    atm.val = f(atm.val,*args)
    return atm.val

def compare_op(op, values):
        pairs = [values[i:i+2] for i in range(len(values) - 1)]
        b_values = map(lambda pair:op(pair[0], pair[1]), pairs)
        return reduce(and_, b_values)
    
def slurp(filepath):
    print(f"filepath={filepath} curdir={os.getcwd()}")
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()
    
ns = { 
        '=': types._equal_Q,
        'throw': throw,
        'nil?': types._nil_Q,
        'true?': types._true_Q,
        'false?': types._false_Q,
        'number?': types._number_Q,
        'string?': types._string_Q,
        'symbol': types._symbol,
        'symbol?': types._symbol_Q,
        'keyword': types._keyword,
        'keyword?': types._keyword_Q,
        'fn?': lambda x: (types._function_Q(x) and not hasattr(x, '_ismacro_')),
        'macro?': lambda x: (types._function_Q(x) and
                             hasattr(x, '_ismacro_') and
                             x._ismacro_),

        'pr-str': pr_str,
        'str': do_str,
        'prn': prn,
        'println': println,
        'readline': lambda prompt: mal_readline.readline(prompt),
        'read-string': reader.read_str,
        'slurp': slurp,
        '<':  lambda *xs: compare_op(lt,xs),
        '<=': lambda *xs: compare_op(le,xs),
        '>':  lambda *xs: compare_op(gt,xs),
        '>=': lambda *xs: compare_op(ge,xs),
        '+':  lambda *xs: reduce(add, xs),
        '-':  lambda *xs: reduce(sub, xs),
        '/':  lambda a,b: (a/b),
        '*':  lambda *xs: reduce(mul, xs),
        'mod':  mod,
        'pow':  pow,
        'quot':  floordiv,
        'time-ms': lambda : int(time.time() * 1000),

        'list': types._list,
        'list?': types._list_Q,
        'vector': types._vector,
        'vector?': types._vector_Q,
        'hash-map': types._hash_map,
        'map?': types._hash_map_Q,
        'assoc': assoc,
        'dissoc': dissoc,
        'get': get,
        'contains?': contains_Q,
        'keys': keys,
        'vals': vals,
        'range*': range_,
        'select-keys': select_keys,
        'mapcat': mapcat,
        'interleave': interleave,
        'map-indexed': map_indexed,
    
        'sequential?': types._sequential_Q,
        'cons': cons,
        'concat': concat,
        'vec': Vector,
        'nth': nth,
        'first': first,
        'rest': rest,
        'empty?': empty_Q,
        'count': count,
        'apply': apply,
        'map': mapf,
        'partition': partition,

        'conj': conj,
        'seq': seq,

        'with-meta': with_meta,
        'meta': meta,
        'atom': types._atom,
        'atom?': types._atom_Q,
        'deref': deref,
        'reset!': reset_BANG,
        'swap!': swap_BANG}

