import re
from .mal_types import (_symbol, _keyword, _list, _vector, _hash_map, _hash_set, _s2u, _u)

class Blank(Exception): pass

class Reader():
    def __init__(self, tokens, position=0):
        self.tokens = tokens
        self.position = position

    def next(self):
        self.position += 1
        return self.tokens[self.position-1]

    def peek(self):
        if len(self.tokens) > self.position:
            return self.tokens[self.position]
        else:
            return None

def tokenize(str):
    tre = re.compile(r"""[\s,]*(~@|\#\{|\#\(|\%\d?|[\[\]{}()'`~^@]|"(?:[\\].|[^\\"])*"?|;.*|[^\s\[\]{}()'"`@,;]+)""");
    return [t for t in re.findall(tre, str) if t[0] != ';']

def _unescape(s):
    return s.replace('\\\\', _u('\u029e')).replace('\\"', '"').replace('\\n', '\n').replace(_u('\u029e'), '\\')

def read_atom(reader):
    int_re = re.compile(r"-?[0-9]+$")
    float_re = re.compile(r"-?[0-9][0-9.]*$")
    string_re = re.compile(r'"(?:[\\].|[^\\"])*"')
    token = reader.next()
    if re.match(int_re, token):     return int(token)
    elif re.match(float_re, token): return float(token)
    elif re.match(string_re, token):return _s2u(_unescape(token[1:-1]))
    elif token[0] == '"':           raise Exception("expected '\"', got EOF")
    elif token[0] == ':':           return _keyword(token[1:])
    elif token == "nil":            return None
    elif token == "true":           return True
    elif token == "false":          return False
    else:                           return _symbol(token)

def read_sequence(reader, typ=list, start='(', end=')'):
    ast = typ()
    token = reader.next()
    if token != start: raise Exception("expected '" + start + "'")

    token = reader.peek()
    while token != end:
        if not token: raise Exception("expected '" + end + "', got EOF")
        ast.append(read_form(reader))
        token = reader.peek()
    reader.next()
    return ast

def read_anonymous_function(reader):
    def get_number(s):
        if s == "%":
            return 1
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
    token = reader.next()
    if token != '#(': raise Exception("expected '#('")

    token = reader.peek()
    while token != ')':
        if not token: raise Exception("expected ')', got EOF")
        n = get_number(token) 
        if n is None:
            ast.append(read_form(reader))
        else:
            params[n] = _symbol(f"__param_{n}__")
            ast.append(params[n])
            reader.next()
        token = reader.peek()
    reader.next()
    return _list(_symbol('fn'), ordered_values(params), ast)

def read_hash_map(reader):
    lst = read_sequence(reader, list, '{', '}')
    return _list(_symbol('hash-map')).__add__(lst)
    #return _hash_map(*lst)

def read_hash_set(reader):
    lst = read_sequence(reader, list, '#{', '}')
    print(f"read_hash_set. lst={lst}")
    return _list(_symbol('set')).__add__(lst)


def read_list(reader):
    return read_sequence(reader, _list, '(', ')')

def read_vector(reader):
    return read_sequence(reader, _vector, '[', ']')

def read_form(reader):
    token = reader.peek()
    #print(f"read_form. token={token}")
    # reader macros/transforms
    if token[0] == ';':
        reader.next()
        return None
    elif token == '\'':
        reader.next()
        return _list(_symbol('quote'), read_form(reader))
    elif token == '`':
        reader.next()
        return _list(_symbol('quasiquote'), read_form(reader))
    elif token == '~':
        reader.next()
        return _list(_symbol('unquote'), read_form(reader))
    elif token == '~@':
        reader.next()
        return _list(_symbol('splice-unquote'), read_form(reader))
    elif token == '^':
        reader.next()
        meta = read_form(reader)
        return _list(_symbol('with-meta'), read_form(reader), meta)
    elif token == '@':
        reader.next()
        return _list(_symbol('deref'), read_form(reader))

    # list
    elif token == ')': raise Exception("unexpected ')'")
    elif token == '(': return read_list(reader)

    # vector
    elif token == ']': raise Exception("unexpected ']'");
    elif token == '[': return read_vector(reader);

    # hash-set
    elif token == '}': raise Exception("unexpected '}'");
    elif token == '#{': return read_hash_set(reader);

    # hash-map
    elif token == '}': raise Exception("unexpected '}'");
    elif token == '{': return read_hash_map(reader);

    # anonymous functions
    elif token == ')': raise Exception("unexpected '}'");
    elif token == '#(': return read_anonymous_function(reader);

    elif token[0] == '%': raise Exception("'%' is allowed as token only in lambda functions");
    # atom
    else:              return read_atom(reader);

def read_str(str):
    tokens = tokenize(str)
    if len(tokens) == 0: raise Blank("Blank Line")
    return read_form(Reader(tokens))
