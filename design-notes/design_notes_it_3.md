# multi arity functions
## Current status
Ok, è già implementata, ma con una grossa limitazione: non gestisce le funzioni variadiche, e non funzionano con recur.
Quindi funzionano:
```
(defn pippo
  ([] (pippo 3))
  ([a] (inc a)))

(def peppe (fn 
             ([] (peppe 33))
             ([a] (dec a))
             ))

(defn xx [a]
  (println a)
  (if (> a 0)
    (recur (dec a))
    (println "Done")))
```
Ma non funziona:
```
(python-traceback-on)

(defn pippo
  ([] (recur 3))
  ([a] (inc a))
  ([& xs] (apply + xs))
  )

(def peppe (fn 
             ([] (recur 33))
             ([a] (dec a))
             ))
```
## Current implementation
La versione corrente è implementata così:
- Ho aggiunto all'interprete la special form `fn**`
- Questa form si aspetta un dizionario che ha come chiavi le arity e come valori gli ast associati
- riscritto la `fn` in questo modo: 
```(defmacro fn [params & xs]
  (if (every? list? (cons params xs))
    (let [make-pair (fn [params-and-body]
                      (let [params (first params-and-body)
                            body (rest params-and-body)]
                        [(count params) [params `(do ~@body)]]))
          maf-dict (apply hash-map (apply concat (map make-pair (cons params xs))))]
      `(fn** ~maf-dict))
    `(fn* ~params (do ~@xs))))
  ```

- In pratica se i parametri sono un vettore di liste costruisce il dizionario e chiama la `fn**` altrimenti chiama la  precedente implementazione di `fn`

## Implementazione variadic multi arity
Ora, per farlo funzionare anche coi variadici, un'idea potrebbe essere di:
1. riconoscere se ci sono parametri preceduti da &
2. in questo caso generare la chiave con  -1.
3. a questo punto, la funzione generata, a fronte di una chiamata con n parametri dovrebbe:
  - prima cercare nel dizionario n (la versione con parametri fissi)
  - se questa non esiste cercare -1 e applicare quelli variadici
4. bisognerebbe controllare che ci sia una sola funzione coi variadici (se ce n'è più di una è un'ambiguità)
5. nell'esecuzione bisognerebbe segnalare con un eccezione fatta meglio  che la funzione cercata non esiste. Ora torna un'eccezione delle get del dizionario (che non trova la chiave)

Fatti 1,2,3 e 5. La 4 direi che non vale la pena: se si definiscono più funzioni variadiche ne vince una.
e funziona !
la `fn` è diventata così:
```
(defn some
  [pred coll]
  (cond
    (nil? (seq coll)) false
    (pred (first coll)) (first coll)
    :else (recur pred (next coll))))


; Multi Arity Functions
(defmacro fn [params & xs]
  (if (every? list? (cons params xs))
    (let [make-pair (fn [params-and-body]
                      (let [params (first params-and-body)
                            body (rest params-and-body)
                            variadic? (some (fn [par] (= (str par) "&")) params )
                            k (if variadic? -1 (count params))]
                        [k [params `(do ~@body)]]))
          maf-dict (apply hash-map (apply concat (map make-pair (cons params xs))))]
      `(fn** ~maf-dict))
    `(fn* ~params (do ~@xs))))
  ```
  ho dovuto implementare anche la `some`, che non c'era

  e la `_multi_arity_function` in mal_types.py è diventata: 
```
  def _multi_arity_function(Eval, Env, maf_dict, env):
    print(f"_multi_arity_function. maf_dict={maf_dict}")
    def maf_dispatcher(args):
        n = len(args)
        if len(args) in maf_dict:
                n = len(args)
        elif -1 in maf_dict:
                n = -1
        else: 
            raise Exception("Calling multi arity function with wrong number of parameters")
        return n
        
    def fn(*args):
        params,ast = maf_dict[len(args)]
        return Eval(ast, Env(env, params, List(args)))
    fn.__meta__ = None
    fn.__multi_arity__ = True
    fn.__ast__ = lambda args: maf_dict[maf_dispatcher(args)][1]
    fn.__gen_env__ = lambda args: Env(env, maf_dict[maf_dispatcher(args)][0], args)
    return fn
```    
## Multi arity and recur
Ora resta il problema della recur da analizzare.

### Implementazione corrente
Il meccanismo di `recur` è implementato in due posti:
- durante l'esecuzione delle funzioni che hanno AST (credo siano le funzioni normali, quelle che non sono nè macro, nè primitive scritte in python).
  Al fondo della funzione EVAL:
```
           else:
                el = eval_ast(ast, env)
                #print(f"else: ast={ast} el={el}")
                f = el[0]
                if hasattr(f, '__multi_arity__') and f.__multi_arity__ :
                    ast = f.__ast__(el[1:])
                    env = f.__gen_env__(el[1:])
                    env.set('__recur_target__', f)
                elif hasattr(f, '__ast__'):
                    ast = f.__ast__
                    env = f.__gen_env__(el[1:])
                    env.set('__recur_target__', f)

```
  dopo una serie di if che gestiscono le special forms, si arriva qui e ci sono due casi:
  - funzioni che hanno l'attributo __ast__
  - funzioni che hanno quello __multi_arity__
  - come si vede la gestione è molto simile. La differenza sta nel fatto che nel caso delle multi_arity l'attributo non contiene direttamente l'AST, ma una funzione che ritorna un AST diverso a seconda del numero e tipo dei parametri.
- Nella special form `recur`, gestita così:
```
           elif "recur" == a0:
                el = eval_ast(ast[1:], env)
                f = env.get('__recur_target__')
                ast = f.__ast__
                env = f.__gen_env__(el)
                env.set('__recur_target__', f)
```
Come si vede, all'atto dell'esecuzione di una funzione viene aggiunto all'env corrente (associato alla funzione) un elemento `recur_target` che registra l'oggetto funzione.
Quando viene eseguita la special form `recur` questa:
1. valuta gli argomenti (ast[1:])
2. recupera l'oggetto funzione associato a `__recur_target__`
3. prende ast dall'attributo `__ast__` della funzione
4. rigenera un env su cui fa bind dei nuovi attributi
5. rimette nel nuovo env la `__recur_target__` per rendere possibile in prossimo, eventuale, ciclo di ricorsione.

Chiaramente il problema che stiamo avendo riguarda il punto 3. Nel caso delle funzioni normali `__ast__` contiene direttamente l'AST, mentre nel caso delle multi arity contiene una funzione da chiamare.
Potremmo risolverla 
  1. rendendo funzione anche quella delle funzioni normali 
  2. inventarci un attributo diverso per le multi arity
  3. testare nella recur se si tratta di una multi arity e chiamare la funzione solo in questo caso. 
Mi sembra che la 3. sia più pulita.

Fatto e funziona!
Signori! la nuova `recur`:
```
            elif "recur" == a0:
                el = eval_ast(ast[1:], env)
                f = env.get('__recur_target__')
                if f.__multi_arity__ :
                    ast = f.__ast__(el)
                else:
                    ast = f.__ast__
                env = f.__gen_env__(el)
                env.set('__recur_target__', f)
```