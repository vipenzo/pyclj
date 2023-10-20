
from mal.stepA_mal import Env,core,types,sys,mal_readline,reader,printer,traceback,PRINT,EVAL,READ


# repl
repl_env = Env()
def REP(str):
    return PRINT(EVAL(READ(str), repl_env))

# core.py: defined using python
for k, v in core.ns.items(): repl_env.set(types._symbol(k), v)
repl_env.set(types._symbol('eval'), lambda ast: EVAL(ast, repl_env))
repl_env.set(types._symbol('*ARGV*'), types._list(*sys.argv[2:]))


import math
repl_env.set(types._symbol('PI'), math.pi)

repl_env.set(types._symbol('is_close'), lambda n1,n2:(math.fabs(n1-n2) < 1e-9))
repl_env.set(types._symbol('abs'), math.fabs)
repl_env.set(types._symbol('sin'), math.sin)
repl_env.set(types._symbol('cos'), math.cos)
repl_env.set(types._symbol('tan'), math.tan)
repl_env.set(types._symbol('asin'), math.asin)
repl_env.set(types._symbol('acos'), math.acos)
repl_env.set(types._symbol('atan'), math.atan)
repl_env.set(types._symbol('sqrt'), math.sqrt)
repl_env.set(types._symbol('python_atan2'), math.atan2)
repl_env.set(types._symbol('atan2'), lambda x,y:(math.sqrt(x**2 + y**2), math.atan2(y/x)))
repl_env.set(types._symbol('to_degrees'), math.degrees)
repl_env.set(types._symbol('to_radians'), math.radians)



# core.mal: defined using the language itself
REP("(def! *host-language* \"python\")")
REP("(def! load-file (fn* [f] (eval (read-string (str \"(do \" (slurp f) \"\nnil)\") ))))")
REP("(load-file \"mal/core.mal\")")

# repl loop
REP("(println (str \"Mal [\" *host-language* \"]\"))")
while True:
    try:
        line = mal_readline.readline("mal > ")
        if line == None: break
        if line == "": continue
        print(REP(line))
    except reader.Blank: continue
    except types.MalException as e:
        print("Error:", printer._pr_str(e.object))
    except Exception as e:
        print("".join(traceback.format_exception(*sys.exc_info())))
