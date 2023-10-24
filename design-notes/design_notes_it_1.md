# design notes it
Questo è un journal in cui provo a registrare le scelte implementate, e, in generale, il progredire dello sviluppo del progetto. 
## general info
### what is it
Il progetto **pyclj** è un’implementazione in python di un *lisp* il più possibile simile al linguaggio *Clojure*, un dialetto del lisp più moderno.
Si basa su [**mal**](https://github.com/kanaka/mal) un’implementazione didattica del lisp, che costruisce passo passo un interprete di questo linguaggio partendo da una versione estremamente elementare e estendendola in una decina di passi fino a farne un linguaggio, ancora rozzo rispetto a implementazioni *production ready*, ma già in grado di eseguire programmi complessi.
*mal* è un progetto di kanaka (Joel Martin), che ha realizzato anche molte delle implementazioni in diversi linguaggi, tra cui python.
*pyclj* parte dall’ultimo step di implementazione di *mal* in **python**, lo *stepA_mal* e lo estende aggiungendo una serie di funzionalità.
### why ?
Lo scopo di questo lavoro è di realizzare un linguaggio simil-clojure scritto in python, che permetta quindi di eseguire programmi Clojure su piattaforme che offrono funzionalità di scripting in python.
Il target principale è Blender. **pyclj** nasce come supporto del progetto [**turtlemal**](https://github.com/vipenzo/turtlemal). Viene gestito come progetto separato per permetterne un eventuale riuso su altre piattaforme e, soprattutto, per permettere evoluzioni della parte *linguaggio* che non destabilizzino il progetto turtlemal.
### repository
Pyclj è su GitHub [qui](https://github.com/vipenzo/pyclj).
 
## journal 
### inizio
Il journal parte a metà dell’opera, quando molte modifiche a mal-python sono già state fatte. Le più significative sono:
- Added slurp
- Added fn, let, defn  
- Forced functions parameter list to be a Vector
- Made Vector and Hash_Map hashable (they can now be used as keys in dictionaries)
- Added PI, is_close, abs, sin, cos, tan, asin, acos, atan, sqrt, python_atan2, atan2, to_degrees, to_radians. No math namespace, added to repl env.
- Added default arg to get. (get {:a 3} :b 33) returns 33.
- Added range (not yet (range) without arguments), select-keys, mapcat, interleave, partition
- Added inc, dec, second, while, dotimes, reduce, comment, when, next, destruct (works on basic cases and not yet integrated into let, fn, defn)
- Added map-indexed, loop, recur (works both on loop and functions)
- Aggiunte le funzioni multi-arity (not handled variadic case yet)
- Aggiunti i set (mancano le funzioni che li usano: union …
- Aggiunte le funzioni anonime con sintassi #(inc %1)
