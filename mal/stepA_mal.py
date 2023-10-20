import functools
import sys, traceback
from . import mal_readline
from . import  mal_types as types
from . import  reader, printer
from .env import Env
from . import  core
# read
def READ(str):
    return reader.read_str(str)

# eval
def qq_loop(acc, elt):
    if types._list_Q(elt) and len(elt) == 2 and elt[0] == u'splice-unquote':
        return types._list(types._symbol(u'concat'), elt[1], acc)
    else:
        return types._list(types._symbol(u'cons'), quasiquote(elt), acc)

def qq_foldr(seq):
    return functools.reduce(qq_loop, reversed(seq), types._list())

def quasiquote(ast):
    if types._list_Q(ast):
        if len(ast) == 2 and ast[0] == u'unquote':
            return ast[1]
        else:
            return qq_foldr(ast)
    elif types._hash_map_Q(ast) or types._symbol_Q(ast):
        return types._list(types._symbol(u'quote'), ast)
    elif types._vector_Q (ast):
        return types._list(types._symbol(u'vec'), qq_foldr(ast))
    else:
        return ast

def is_macro_call(ast, env):
    return (types._list_Q(ast) and
            types._symbol_Q(ast[0]) and
            env.find(ast[0]) and
            hasattr(env.get(ast[0]), '_ismacro_'))

def macroexpand(ast, env):
    #print(f"macroexpand. ast={ast}")
    while is_macro_call(ast, env):
        #print(f"macroexpand. è una macro ast={ast}")
        mac = env.get(ast[0])
        #print(f"macroexpand. mac={mac} rest={ast[1:]}")
        ast = mac(*ast[1:])
        #print(f"macroexpand. ast-espanso={ast}")
    return ast

def eval_ast(ast, env):
    #print(f"eval_ast ast={ast}")
    if types._symbol_Q(ast):
        return env.get(ast)
    elif types._list_Q(ast):
        return types._list(*map(lambda a: EVAL(a, env), ast))
    elif types._vector_Q(ast):
        return types._vector(*map(lambda a: EVAL(a, env), ast))
    elif types._hash_map_Q(ast):
        return types.Hash_Map((k, EVAL(v, env)) for k, v in ast.items())
    else:
        return ast  # primitive value, return unchanged

def EVAL(ast, env):
    #print("EVAL %s" % printer._pr_str(ast))
    while True:
        #print("L-EVAL %s" % printer._pr_str(ast))
        if not types._list_Q(ast):
            return eval_ast(ast, env)

        # apply list
        #print(f"AST prima di macroespand={ast}")
        ast = macroexpand(ast, env)
        #print(f"AST dopo macroespand={ast}")
        if not types._list_Q(ast):
            return eval_ast(ast, env)
        if len(ast) == 0: return ast
        a0 = ast[0]

        if "env_dump" == a0:
            env.dump()
            return None
        elif "def!" == a0 or "def" == a0:
            a1, a2 = ast[1], ast[2]
            res = EVAL(a2, env)
            #print(f"EVAL(def*) res={res}")
            return env.set(a1, res)
        elif "let*" == a0:
            a1, a2 = ast[1], ast[2]
            #print(f"a1={a1} a2={a2} ast={ast}")
            let_env = Env(env)
            for i in range(0, len(a1), 2):
                let_env.set(a1[i], EVAL(a1[i+1], let_env))
            ast = a2
            env = let_env
            # Continue loop (TCO)
        elif "loop*" == a0:
            a1, a2 = ast[1], ast[2]
            params = a1[::2]
            args = a1[1::2]
            #print(f"loop* args={args}")
            el = eval_ast(args, env)            
            #print(f"loop* el={el}")
            f = types._function(EVAL, Env, a2, env, params)
            ast = f.__ast__
            env = f.__gen_env__(el)
            env.set('__recur_target__', f)
            #env.dump_last()

        elif "quote" == a0:
            return ast[1]
        elif "quasiquoteexpand" == a0:
            return quasiquote(ast[1]);
        elif "quasiquote" == a0:
            ast = quasiquote(ast[1]);
            # Continue loop (TCO)
        elif 'defmacro!' == a0:
            func = types._clone(EVAL(ast[2], env))
            func._ismacro_ = True
            return env.set(ast[1], func)
        elif 'macroexpand' == a0:
            return macroexpand(ast[1], env)
        elif "py!*" == a0:
            exec(compile(ast[1], '', 'single'), globals())
            return None
        elif "py*" == a0:
            return types.py_to_mal(eval(ast[1]))
        elif "." == a0:
            el = eval_ast(ast[2:], env)
            f = eval(ast[1])
            return f(*el)
        elif "try*" == a0:
            if len(ast) < 3:
                return EVAL(ast[1], env)
            a1, a2 = ast[1], ast[2]
            if a2[0] == "catch*":
                err = None
                try:
                    return EVAL(a1, env)
                except types.MalException as exc:
                    err = exc.object
                except Exception as exc:
                    err = exc.args[0]
                catch_env = Env(env, [a2[1]], [err])
                return EVAL(a2[2], catch_env)
            else:
                return EVAL(a1, env);
        elif "do" == a0:
            eval_ast(ast[1:-1], env)
            ast = ast[-1]
            # Continue loop (TCO)
        elif "if" == a0:
            a1, a2 = ast[1], ast[2]
            cond = EVAL(a1, env)
            if cond is None or cond is False:
                if len(ast) > 3: ast = ast[3]
                else:            ast = None
            else:
                ast = a2
            # Continue loop (TCO)
        elif "fn*" == a0:
            #print(f"fn* ast={ast}")
            a1, a2 = ast[1], ast[2]
            #print(f"fn*. a1={a1} a2={a2}")
            return types._function(EVAL, Env, a2, env, a1)
        elif "recur" == a0:
            #print(f"recur ast={ast} ")
            el = eval_ast(ast[1:], env)
            #env.get('__recur_target__').__gen_env__(el).dump_last()
            #print(f"recur el={el}")
            f = env.get('__recur_target__')
            ast = f.__ast__
            env = f.__gen_env__(el)
            env.set('__recur_target__', f)
        else:
            el = eval_ast(ast, env)
            f = el[0]
            if hasattr(f, '__ast__'):
                #print(f"eseguo funzione. el[0]={el[0]} parametri={el[1:]}")
                ast = f.__ast__
                env = f.__gen_env__(el[1:])
                env.set('__recur_target__', f)
                #print("fn call.")
                #env.dump()
            else:
                return f(*el[1:])

# print
def PRINT(exp):
    return printer._pr_str(exp)


