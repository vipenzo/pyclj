from .stepA_mal import Env,core,types,sys,mal_readline,reader,printer,traceback,PRINT,EVAL,READ

def BOOT():
    # repl
    boot_env = Env()
    def REP(str):
        return PRINT(EVAL(READ(str), boot_env))

    # core.py: defined using python
    for k, v in core.ns.items(): boot_env.set(types._symbol(k), v)
    boot_env.set(types._symbol('eval'), lambda ast: EVAL(ast, boot_env))
    boot_env.set(types._symbol('*ARGV*'), types._list(*sys.argv[2:]))


    import math
    boot_env.set(types._symbol('PI'), math.pi)

    boot_env.set(types._symbol('is_close'), lambda n1,n2:(math.fabs(n1-n2) < 1e-9))
    boot_env.set(types._symbol('abs'), math.fabs)
    boot_env.set(types._symbol('sin'), math.sin)
    boot_env.set(types._symbol('cos'), math.cos)
    boot_env.set(types._symbol('tan'), math.tan)
    boot_env.set(types._symbol('asin'), math.asin)
    boot_env.set(types._symbol('acos'), math.acos)
    boot_env.set(types._symbol('atan'), math.atan)
    boot_env.set(types._symbol('sqrt'), math.sqrt)
    boot_env.set(types._symbol('python_atan2'), math.atan2)
    boot_env.set(types._symbol('atan2'), lambda x,y:(math.sqrt(x**2 + y**2), math.atan2(y/x)))
    boot_env.set(types._symbol('to_degrees'), math.degrees)
    boot_env.set(types._symbol('to_radians'), math.radians)

    # core.mal: defined using the language itself
    REP("(def! *host-language* \"python\")")
    REP("(def! load-file (fn* [f] (eval (read-string (str \"(do \" (slurp f) \"\nnil)\") ))))")

    import os
    current_file_path = os.path.realpath(__file__)
    mal_directory = os.path.dirname(current_file_path)
    REP(f"(def! mal_directory \"{mal_directory}\")")
    core_mal_path = os.path.join(mal_directory, "core.mal")
    #
    # core.mal: defined using the language itself
    REP(f"(load-file \"{core_mal_path}\")")

    def REPL():
        REP("(repl-loop)")
        
    return REP, REPL

