import re
from .mal_types import (_symbol, _keyword, _list, _vector, _hash_map, _hash_map_Q, _hash_set, _s2u, _u)

class Blank(Exception): pass

    
__current_file_path__ = "__CONSOLE__"

def set_current_file(filepath):
    global __current_file_path__
    save = __current_file_path__
    __current_file_path__ = filepath
    return save

class Reader():
    def __init__(self, tokens, position=0):
        self.tokens = tokens
        self.position = position
        self.file_path = __current_file_path__

    def next(self):
        self.position += 1
        return self.tokens[self.position-1][0]

    def peek(self):
        if len(self.tokens) > self.position:
            return self.tokens[self.position][0]
        else:
            return None

    def filepath(self):
        return self.file_path

    def coords(self):
        if len(self.tokens) > self.position-1:
            return self.tokens[self.position-1][1:]
        else:
            return None

def set_coords(o, reader):
    if reader:
        o.__coords__ = [reader.filepath(), reader.coords()]
    return o

def coords_tokenize(str):
    tre = re.compile(r"""[\s,]*(~@|\#\{|\#\(|\%\&|\%\d?|[\[\]{}()'`~^@]|"(?:[\\].|[^\\"])*"?|;.*|[^\s\[\]{}()'"`@,;]+)""")
    
    tokens_with_coords = []
    line_num = 1
    col_num = 1
    prev_start = 0
    #print(f"str={str[0:50]}")
    for match in re.finditer(tre, str):
        token = match.group(1)
        #print(f"token={token}")
        if token[0] != ';':
            start, end = match.span()
            start = end - len(token)
            #print(f"start={start} end={end} prev_start={prev_start}")
            # Calcola la linea e la colonna basandosi sul contenuto fino al token attuale
            prev_newlines = str.count('\n', prev_start, start)
            #print(f"prev_newlines={prev_newlines}")
            if prev_newlines > 0:
                col_num = 1
                line_num += prev_newlines   
            else:
                col_num += start - prev_start
            prev_start = start
            
            #print(f"col_num={col_num} line_num={line_num}")

            tokens_with_coords.append((token, line_num, col_num))

    return tokens_with_coords

def make_exception(ex, msg, reader):
    return ex(msg + f" in file {reader.filepath()} at position:{reader.coords()}")

def make_symbol(token, reader):
    sym = _symbol(token)
    set_coords(sym, reader)
    return sym

def _unescape(s):
    return s.replace('\\\\', _u('\u029e')).replace('\\"', '"').replace('\\n', '\n').replace(_u('\u029e'), '\\')

def read_int_token(m, reader):
    res = None
    if m.group(2):
        return 0
    if m.group(3):
        res = int(m.group(3))
    elif m.group(4):
        res = int(m.group(4), 16)
    elif m.group(5):
        res = int(m.group(5), 8)
    elif m.group(6):
        base = int(m.group(6))
        res = int(m.group(7), int(base))
    if m.group(1):
        res = - res 
    if not res:
        print(f"read_int_token. m={m} group_2={m.group(2)} token={m.group(0)}")
        raise make_exception(Exception, f"read_int_token. m={m} group_2={m.group(2)} token={m.group(0)}", reader) 
    return res       


def read_atom(reader):
   # int_re = re.compile(r"-?[0-9]+$")
    int_re = re.compile(r"^([-+]?)(?:(0)|([1-9][0-9]*)|0[xX]([0-9A-Fa-f]+)|0([0-7]+)|([1-9][0-9]?)[rR]([0-9A-Za-z]+)|0[0-9]+)(N)?$")
    #float_re = re.compile(r"-?[0-9][0-9.]*$")
    float_re = re.compile(r"([-+]?[0-9]+(\.[0-9]*)?([eE][-+]?[0-9]+)?)(M)?")
    string_re = re.compile(r'"(?:[\\].|[^\\"])*"')
    token = reader.next()
    #print(f"read_atom. token={token}")
    
    if (m := re.match(int_re, token)):     return read_int_token(m, reader)
    elif re.match(float_re, token): return float(token)
    elif re.match(string_re, token):return _s2u(_unescape(token[1:-1]))
    elif token[0] == '"':           raise make_exception(Exception,"expected '\"', got EOF", reader)
    elif token[0] == ':':           return _keyword(token[1:])
    elif token == "nil":            return None
    elif token == "true":           return True
    elif token == "false":          return False
    else:                           return make_symbol(token, reader)

def read_sequence(reader, typ, start='(', end=')'):
    ast = typ()
    ast = set_coords(ast, reader)
    token = reader.next()
    if token != start: raise make_exception(Exception, "expected '" + start + "'",reader)

    token = reader.peek()
    k = None
    n = 0
    def is_even(n):
        return n % 2 == 0
    while token != end:
        if not token: raise make_exception(Exception, "expected '" + end + "', got EOF", reader)
        if _hash_map_Q(ast):
            if is_even(n):
                k = read_form(reader)
                n = n + 1
            else:
                ast.add_pair(k, read_form(reader))
                n = n + 1
        else:
            ast.append(read_form(reader))
        token = reader.peek()
    reader.next()
    if _hash_map_Q(ast) and not is_even(n):
        raise make_exception(Exception, "trying to define a hash_map with odd number of elements", reader)
    return ast

def read_anonymous_function(reader):
    def get_number(s):
        if s == "%":
            return 1
        elif s == "%&":
            return "&"
        elif s.startswith('%'):
            try:
                return int(s[1:])
            except ValueError:
                return None
        return None
    def ordered_values(d):
        print(f"ordered_values. d={d}")
        if d:
            max_key = max(d.keys())
            return _vector(*[d.get(i, "_") for i in range(1, max_key+1)])
        else:
            return _vector()

    params = {}
    ast = _list()
    set_coords(ast, reader)
    token = reader.next()
    if token != '#(': raise make_exception(Exception, "expected '#('", reader)

    token = reader.peek()
    while token != ')':
        if not token: raise make_exception(Exception, "expected ')', got EOF", reader)
        n = get_number(token) 
        if n is None:
            ast.append(read_form(reader))
        elif n == "&":
            params[0] = make_symbol("__param_rest__", reader)
            ast.append(params[0])
            reader.next()
        else:
            params[n] = make_symbol(f"__param_{n}__", reader)
            ast.append(params[n])
            reader.next()
        token = reader.peek()
    reader.next()
    if 0 in params:
        params[max(params.keys())+1] = make_symbol("&", reader)
        params[max(params.keys())+1] = params[0]
    res = _list(make_symbol('fn', reader), ordered_values(params), ast)
    set_coords(res, reader)
    return res

def read_hash_map(reader):
    return read_sequence(reader, _hash_map, '{', '}')

def read_hash_set(reader):
    lst = read_sequence(reader, _list, '#{', '}')
    #print(f"read_hash_set. lst={lst}")
    res =  _list(make_symbol('set', reader)).__add__(lst)
    set_coords(res, reader)
    return res


def read_list(reader):
    return read_sequence(reader, _list, '(', ')')

def read_vector(reader):
    ast = read_sequence(reader, _vector, '[', ']')
    return ast

def read_form(reader):
    token = reader.peek()
    #print(f"read_form. token={token}")
    # reader macros/transforms
    if token[0] == ';':
        reader.next()
        return None
    elif token == '\'':
        reader.next()
        res = _list(make_symbol('quote', reader), read_form(reader))
        set_coords(res, reader)
        return res
    elif token == '`':
        reader.next()
        res = _list(make_symbol('quasiquote', reader), read_form(reader))
        set_coords(res, reader)
        return res
    elif token == '~':
        reader.next()
        res =  _list(make_symbol('unquote', reader), read_form(reader))
        set_coords(res, reader)
        return res
    elif token == '~@':
        reader.next()
        res =  _list(make_symbol('splice-unquote', reader), read_form(reader))
        set_coords(res, reader)
        return res
    elif token == '^':
        reader.next()
        meta = read_form(reader)
        res = _list(make_symbol('with-meta', reader), read_form(reader), meta)
        set_coords(res, reader)
        return res
    elif token == '@':
        reader.next()
        res = _list(make_symbol('deref', reader), read_form(reader))
        set_coords(res, reader)
        return res
    # list
    elif token == ')': raise make_exception(Exception, "unexpected ')'", reader)
    elif token == '(': return read_list(reader)

    # vector
    elif token == ']': raise make_exception(Exception, "unexpected ']'", reader)
    elif token == '[': return read_vector(reader)

    # hash-set
    elif token == '}': raise make_exception(Exception, "unexpected '}'", reader)
    elif token == '#{': return read_hash_set(reader)

    # hash-map
    elif token == '}': raise make_exception(Exception, "unexpected '}'", reader);
    elif token == '{': return read_hash_map(reader);

    # anonymous functions
    elif token == ')': raise make_exception(Exception, "unexpected '}'", reader);
    elif token == '#(': return read_anonymous_function(reader);

    elif token[0] == '%': raise make_exception(Exception, "'%' is allowed as token only in lambda functions", reader);
    # atom
    else:              return read_atom(reader);


def read_str(str):
    tokens = coords_tokenize(str)
    #print(f"read_str. str={str} tokens={tokens}")
    if len(tokens) == 0: raise Blank("Blank Line")
    return read_form(Reader(tokens))
