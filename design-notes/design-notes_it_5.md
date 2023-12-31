# Destructuring
Riprendiamo il lavoro sul destructuring

# current state
Ad oggi è implementata così
```
;-------- destruct
(def destruct-associative nil)
(def destruct-sequential nil)
(defn destruct [bindings values]
  (println "destruct" bindings values)
  (when bindings
    (cond (sequential? bindings)
          (destruct-sequential bindings values)

          (map? bindings)
          (destruct-associative bindings values)

          :else
          [bindings values])))

(defn destruct-sequential [binding-seq val-seq]
  ;(println "destruct-sequential" binding-seq val-seq)
    (if (= (first binding-seq) '&)
      [(second binding-seq) val-seq]
      (concat (destruct (first binding-seq) (first val-seq))
              (destruct (next binding-seq) (next val-seq)))))
  

(defn destruct-associative [binding-map val-map]
  (println "destruct-associative" binding-map val-map)
  (let [default-map (get binding-map :or)
              keys-bindings (get binding-map :keys)
              binding-map (if keys-bindings
                            (apply hash-map (interleave keys-bindings
                                                        (map keyword keys-bindings)))
                            binding-map)
              binding-map (if default-map (dissoc binding-map :or) binding-map)
              m (select-keys val-map (vals binding-map))]
             (mapcat (fn [b v] (destruct b (get m v (get default-map (symbol v)))))
                     (keys binding-map)
                     (vals binding-map))))
```

Esiste cioè solo la funzione `destruct` non associata a `let`, `fn` e alle **chiamate di funzioni o macro**, e è praticamente presa di peso da questo articolo.
L'associazione a `let`, come esposto nell'articolo è problematica per:
- la necessità di aggiungere una eval in certi casi (range)
- il fatto che il valore dei simboli già valutati non è disponibile a quelli dopo (cosa che invece succede nella `let`)

## Implementazione

L'articolo lascia la cosa a metà, in attesa di una seconda parte, non ancora uscita e propone un indizio per andare avanti. Indizio che, per ora non mi dice molto.
Ma andiamo con ordine. Intanto copio in destruct.mal i casi di test dell'articolo, così vediamo se ho i suoi stessi risultati.

Ok, un intoppo già qui.Questo test dà errore: `(destruct '{a :a b :b c :c} {:a 1 :b 2 :c 3})`. Il problema è che una hash_map non si comporta come una lista di pairs. (first '{a :a b :b c :c}), dovrebbe ritornare ['a 2] e invece gennera un'eccezione. Provo a capire dov'è il problema e a correggerlo.
Risolto: ora first e rest funzionano sulle hash_map, ma c'è un altro problema:
Il reader trasforma "'{a :a b :b}" in "(hash_map a :a b :b)",  era un modo per differire la trasformazione a dopo, funziona in genere, ma non qui. Devo far tornare al reader direttamente l'hash_map.
Ok, messo a posto, ma avremo lo stesso problema con le hash_set che fanno ancora la stessa cosa: lo metto a posto quando si presenta il problema e ho un test.
Ok, gli esempi della destruct sembrano andare tutti eccetto gli ultimi due:
```
(destruct (quote []) [])  -->  ()
(destruct (quote [a b c]) [1 2 3])  -->  (a 1 b 2 c 3)
(destruct (quote [a b c & cs]) (range 10))  -->  (a 0 b 1 c 2 cs (3 4 5 6 7 8 9))
(destruct (quote {a :a b :b c :c}) {:a 1 :b 2 :c 3})  -->  ['a', 1, 'b', 2, 'c', 3]
(destruct (quote {a :a b :b [x y & zs] :c}) {:a 1 :b 2 :c (range 10)})  -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9]]
(destruct (quote {a :a b :b [x y & zs] :c d :d :or {d 1000}}) {:a 1 :b 2 :c (range 10)})  -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9], 'd', None]
(destruct (quote {a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {d 1000}}) {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}})  -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9], 'd', None, 'g', 100, 'h', 200]
```
:or non sembra andare.
In effetti il codice funzionava, l'errore era nell'esempio (che viene dall'articolo), quei due {d 1000} dovevano essere {:d 1000}

Ora funziona:
```
(destruct (quote []) [])  -->  ()
(destruct (quote [a b c]) [1 2 3])  -->  (a 1 b 2 c 3)
(destruct (quote [a b c & cs]) (range 10))  -->  (a 0 b 1 c 2 cs (3 4 5 6 7 8 9))
(destruct (quote {a :a b :b c :c}) {:a 1 :b 2 :c 3})  -->  ['a', 1, 'b', 2, 'c', 3]
(destruct (quote {a :a b :b [x y & zs] :c}) {:a 1 :b 2 :c (range 10)})  -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9]]
(destruct (quote {a :a b :b [x y & zs] :c d :d :or {:d 1000}}) {:a 1 :b 2 :c (range 10)})  -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9], 'd', 1000]
(destruct (quote {a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}}) {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}})  -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9], 'd', 1000, 'g', 100, 'h', 200]
```
Ora provo ad aggiungere la definizione di `let-` dell'articolo.
L'accetta, provo gli esempi con `let-`.
Dà un eccezione perchè non trova la `->>`, che in effetti non ho mai implementato. Probabilmente mi ero fermato per questo.
L'implementazione dal sorgente di clojure sembra abbastanza semplice, provo a usare quella.
Dà errore perchè non trova `seq?`, bisogna implementare prima quella. Qui non posso usare il sorgente di clojure, perchè testa se l'argomento è un'istanza di ISeq.
Provo a implementarla come `or` di test sulle classi che si comportano come liste (liste, vettori etc ..)
Non funziona. la mia `seq?` torna sempre `nil` per cui la `->>` non funziona.
Ho cambiato l'implementazione di `->>` in modo che usi la `list?` e ora va tutto.
```
code:  (let- [[] []] nada) 
    -->  nada
code:  (let- [[a b c] [1 2 3]] [a b c]) 
    -->  [1 2 3]
code:  (let- [[a b c & cs] (range 10)] [a b c cs]) 
    -->  [<function _function.<locals>.fn at 0x102c859e0> 10 nil nil]
code:  (let- [{a :a b :b c :c} {:a 1 :b 2 :c 3}] [a b c]) 
    -->  [1 2 3]
code:  (let- [{a :a b :b [x y & zs] :c} {:a 1 :b 2 :c (range 10)}] [a b x y zs]) 
    -->  [1 2 <function _function.<locals>.fn at 0x102c859e0> 10 nil]
code:  (let- [{a :a b :b [x y & zs] :c d :d :or {d 1000}} {:a 1 :b 2 :c (range 10)}] [a b x y zs d]) 
    -->  [1 2 <function _function.<locals>.fn at 0x102c859e0> 10 nil nil]
code:  (let- [{a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {d 1000}} {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}] [a b x y zs d g h]) 
    -->  [1 2 <function _function.<locals>.fn at 0x102c859e0> 10 nil nil 100 200]
destruct.mal
``` 

Dà esattamente gli errori descritti nell'articolo. Ora se vado avanti come dice lui e metto la eval mi trovo di fronte allo stesso vicolo cieco. Forse è meglio capire prima che fare.

Guardando meglio l'articolo il suggerimento ha senso. 
Ho provato a implementarlo così:
```
(defn destruct-sequential [binding-seq val-seq]
  (if (= (first binding-seq) '&)
    [(second binding-seq) val-seq]
    (apply concat (map-indexed (fn [i v] (vector v `(nth ~val-seq ~i))) binding-seq))))
```
e sia `destruct` che `let-` funzionano producendo il codice con nth, eccetto per le variadic che fanno casino.
```
code:  (let- [[a b c & cs] (range 10)] [a b c cs]) 
    -->  [0 1 2 4]
```
Il problema è questa riga: `(if (= (first binding-seq) '&)`. Ora la destruct sequential lavora in un blocco solo, non è più ricorsiva, per cui la `'&`, se c'è, si trova al penultimo posto di bindings. Quindi bisogna:
- testare se c'è il variadic
- nel caso assegnare all'ultima variabile la porzione di lista composta dagli ultimi `n` elementi, dove `n` è `(count bingings)` meno `2` e  fare concat con l'assegnazione alle prime `n` variabili di bindings dei primi `n` valori
- se con c'è variadic fa quello che fa ora

Dà errore perchè la mia and è implementata male: non si comporta come una special form: valuta prima tutti i parametri e ne fa l'and, la special form deve fermarsi al primo false (in questo caso `(>= (count bindings) 2)`).
Ho provato a mettere in core.mal direttamente il sorgente della `and` di clojure, ma non funziona perchè è una macro multiarity (la mia implementazione del multiarity non funziona con le macro finora.)
Non voglio aprire troppi rami, per cui cambio l'implementazione a mano. BTW, vedo che usa simboli che finiscono per # (immagino siano dei temporanei, ma è una cosa non ancora implementata e da approfondire. Immagino che al momento la mia implementazione li tratti come simboli normali e rischino quindi di *ricoprire* simboli utente, basta farci attenzione)
La nuova `and` è questa:
```
(defmacro and
  [& exprs]
  (when exprs
    `(let [sym ~(first exprs)]
       (if sym
         ~(if (next exprs)
            `(and ~@(rest exprs))
            'sym)
         sym))))
```
Non funziona perchè manca la `last`. La implemento scopiazzando la first.
ora manca la `take` (e immagino anche la `drop`), le aggiungo.
Ok, l'implementazione non è molto elegante, ma ora la `let-` funziona:
```
code:  (let- [[] []] nada) 
    -->  nada
code:  (let- [[a b c] [1 2 3]] [a b c]) 
    -->  [1 2 3]
code:  (let- [[a b c & cs] (range 10)] [a b c cs]) 
    -->  [0 1 2 (3 4 5 6 7 8 9)]
code:  (let- [{a :a b :b c :c} {:a 1 :b 2 :c 3}] [a b c]) 
    -->  [1 2 3]
code:  (let- [{a :a b :b [x y & zs] :c} {:a 1 :b 2 :c (range 10)}] [a b x y zs]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9)]
code:  (let- [{a :a b :b [x y & zs] :c d :d :or {:d 1000}} {:a 1 :b 2 :c (range 10)}] [a b x y zs d]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9) 1000]
code:  (let- [{a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}} {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}] [a b x y zs d g h]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9) 1000 100 200]
```

Funziona anche questo:
```
pyclj > (let- [a 10 b a] b)
10
```

Ok, ho dovuto fare ancora una piccola modifica, ed è ancora meno elegante, ma credo di avercela fatta. Ora funziona tutto:
```
code:  (destruct (quote []) []) 
    -->  ()
code:  (destruct (quote [a b c]) [1 2 3]) 
    -->  (a (nth [1 2 3] 0) b (nth [1 2 3] 1) c (nth [1 2 3] 2))
code:  (destruct (quote [a b c & cs]) (range 10)) 
    -->  (a (nth (take [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] 3) 0) b (nth (take [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] 3) 1) c (nth (take [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] 3) 2) cs (drop [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] 3))
code:  (destruct (quote {a :a b :b c :c}) {:a 1 :b 2 :c 3}) 
    -->  ['a', 1, 'b', 2, 'c', 3]
code:  (destruct (quote {a :a b :b [x y & zs] :c}) {:a 1 :b 2 :c (range 10)}) 
    -->  ['a', 1, 'b', 2, 'x', ['nth', ['take', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 0], 'y', ['nth', ['take', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 1], 'zs', ['drop', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2]]
code:  (destruct (quote {a :a b :b [x y & zs] :c d :d :or {:d 1000}}) {:a 1 :b 2 :c (range 10)}) 
    -->  ['a', 1, 'b', 2, 'x', ['nth', ['take', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 0], 'y', ['nth', ['take', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 1], 'zs', ['drop', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 'd', 1000]
code:  (destruct (quote {a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}}) {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}) 
    -->  ['a', 1, 'b', 2, 'x', ['nth', ['take', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 0], 'y', ['nth', ['take', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 1], 'zs', ['drop', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 2], 'd', 1000, 'g', 100, 'h', 200]
code:  (let- [[] []] nada) 
    -->  nada
code:  (let- [[a b c] [1 2 3]] [a b c]) 
    -->  [1 2 3]
code:  (let- [[a b c & cs] (range 10)] [a b c cs]) 
    -->  [0 1 2 (3 4 5 6 7 8 9)]
code:  (let- [{a :a b :b c :c} {:a 1 :b 2 :c 3}] [a b c]) 
    -->  [1 2 3]
code:  (let- [{a :a b :b [x y & zs] :c} {:a 1 :b 2 :c (range 10)}] [a b x y zs]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9)]
code:  (let- [{a :a b :b [x y & zs] :c d :d :or {:d 1000}} {:a 1 :b 2 :c (range 10)}] [a b x y zs d]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9) 1000]
code:  (let- [{a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}} {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}] [a b x y zs d g h]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9) 1000 100 200]
code:  (def list-of-things (range 10 20)) 
    -->  [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
code:  (let- [[a b c & cs] list-of-things] [a b c cs]) 
    -->  [10 11 12 (13 14 15 16 17 18 19)]
code:  (let [list-of-things (range 10)] (let- [[a b c & cs] list-of-things] [a b c cs])) 
    -->  [0 1 2 (3 4 5 6 7 8 9)]
code:  (defn uh-oh [list-of-things] (let- [[a b c & cs] list-of-things] [a b c cs])) 
    -->  <function _function.<locals>.fn at 0x100c1c4a0>
code:  (uh-oh (range 10)) 
    -->  [0 1 2 (3 4 5 6 7 8 9)]
code:  (let- [list-of-things (range 10)] list-of-things) 
    -->  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

E il codice è questo:
```
(def destruct-associative nil)
(def destruct-sequential nil)
(defn destruct [bindings values]
  (when bindings
    (cond (sequential? bindings)
          (destruct-sequential bindings values)

          (map? bindings)
          (destruct-associative bindings values)

          :else
          [bindings values])))


(defn destruct-sequential [binding-seq val-seq]
  (defn variadic? [bindings]
    (and (>= (count bindings) 2) (= '& (nth bindings (- (count bindings) 2)))))
  (if (variadic? binding-seq)
    (let [n-fixed-values (- (count binding-seq) 2)
          variadic-sym (last binding-seq)
          variadic-value (list 'drop val-seq n-fixed-values)
          var-binding (list variadic-sym variadic-value)
          val-seq (list 'take val-seq n-fixed-values)
          binding-seq (take binding-seq n-fixed-values)]
      (concat  (apply concat (map-indexed (fn [i v] (vector v `(nth ~val-seq ~i))) binding-seq))  var-binding))
    (apply concat (map-indexed (fn [i v] (vector v `(nth ~val-seq ~i))) binding-seq))))




(defn destruct-associative [binding-map val-map]
  (let [default-map (get binding-map :or)
        keys-bindings (get binding-map :keys)
        binding-map (if keys-bindings
                      (apply hash-map (interleave keys-bindings
                                                  (map keyword keys-bindings)))
                      binding-map)
        binding-map (if default-map (dissoc binding-map :or) binding-map)
        m (select-keys val-map (vals binding-map))]
    (mapcat (fn [b v] (destruct b (get m v (get default-map (symbol v)))))
            (keys binding-map)
            (vals binding-map))))

(defmacro ->>
  [x & xs]
  (loop [x x, forms xs]
    (if forms
      (let [form (first forms)
            threaded (if (list? form)
                       (with-meta `(~(first form) ~@(next form)  ~x) (meta form))
                       (list form x))]
        (recur threaded (next forms)))
      x)))


(defmacro let- [binding-vector & body]
  (apply list
         'let*
         (->> binding-vector
              (partition 2)
              (mapcat (fn [bindings] (destruct (first bindings)
                                               (second bindings))))
              vec)
         body))

```

Ora potrei rinominare la `let-` come `let` e provare a modificare nello stesso modo `fn` e `loop`.
La let sembrava funzionare, per cui ho iniziato a lavorare sulla fn.
Questa versione mi sembra buona:
```
(defmacro fn-- [params & body] 
  `(fn* [& vals] 
        (do
          (println "vals=" vals)
          (let [[~@params] vals]
            (do ~@body)))))
```
... ma non funziona, perchè in effetti la let non funziona.
`(macroexpand (fn-- [[x y]] (+ x y)))`  torna: `(fn* [& vals] (do (let [[[x y]] vals] (do (+ x y)))))`, che sembra corretto, ma `(macroexpand (let [[[x y]] [[1 2]]] (+ x y)))` torna: `(let* [[x y] (nth [[1 2]] 0)] (do (+ x y)))`, che è giusto a metà. Mettendo quegli `nth` ho rotto qualcosa.

In effetti mancava un pezzo: la destruct-sequential deve restare ricorsiva.
Ora è così:
```
(defn destruct-sequential [binding-seq val-seq]
  (defn variadic? [bindings]
    (and (>= (count bindings) 2) (= '& (nth bindings (- (count bindings) 2)))))
  (let* [bindings (if (variadic? binding-seq)
                    (let* [n-fixed-values (- (count binding-seq) 2)
                           variadic-sym (last binding-seq)
                           variadic-value (list 'drop val-seq n-fixed-values)
                           var-binding (list variadic-sym variadic-value)
                           val-seq (list 'take val-seq n-fixed-values)
                           binding-seq (take binding-seq n-fixed-values)]
                          (concat  (apply concat (map-indexed (fn [i v] (vector v `(nth ~val-seq ~i))) binding-seq))  var-binding))
                    (apply concat (map-indexed (fn [i v] (vector v `(nth ~val-seq ~i))) binding-seq)))
         bindings-pairs (partition 2 bindings)]
        (mapcat (fn [p] (apply destruct p)) bindings-pairs)))
```
Non è particolarmente elegante, 'sta cosa degli `nth` non mi piace. Ho guardato l'implementazione di **bobbi-lisp** ed è completamente diversa, ma comunque *pesante*, forse non si può proprio semplificare più di tanto.
Comunque, per ora, andiamo avanti così.

Ora questa:
```
(defmacro fn-- [params & body] 
  `(fn* [& vals] 
        (let [[~@params] vals]
          (do ~@body))))
```
sembra andare:
```
pyclj > ((fn-- [[x y] z] (* z (+ x y))) [1 2] 3)
9
```
Potrei rinominarla `fn`, ma prima dobbiamo chiarire il rapporto tra *multiarity* e *destructuring*, perchè ad oggi abbiamo due definizioni diverse di `fn` che implementano le due diverse funzionalità. Bisogna integrarle.
C'è inoltre da considerare il rapporto tra multiarity e destructuring per sè. Una funzione tipo:
```
(defn aaa 
    ([[x y]] (aaa x y))
    ([{x :x y :y}] (aaa x y))
    ([x y] (+ x y))
    )
```
É legale ? In Clojure non lo è. Nella mia implementazione potrebbe diventarlo, ma per il momento decido di non farlo.
Anzi, come ulteriore semplificazione non accetto destructuring e multiarity insieme.

## Restart
No, l'uso di `nth` per ovviare all'eval è una strada senza uscita. Semplicemente non funziona per cose tipo: `[{x :x}]` in questo caso la destruct associative riceve come val-seq `(nth [{x :x}] 0)` e non sa come uscirne.
Ho rimesso, intanto, l'eval nella `let` e, nella gestione dei variadic della destruct-sequential trasformo in vettore il `next` della val-seq.
Facciamo un check per vedere cosa funziona e cosa no.
Ora la situazione è questa:
```
code:  (destruct (quote []) []) 
    -->  ()
code:  (destruct (quote [a b c]) [1 2 3]) 
    -->  (a 1 b 2 c 3)
code:  (destruct (quote [a b c & cs]) (range 10)) 
    -->  (a 0 b 1 c 2 cs [3 4 5 6 7 8 9])
code:  (destruct (quote {a :a b :b c :c}) {:a 1 :b 2 :c 3}) 
    -->  ['a', 1, 'b', 2, 'c', 3]
code:  (destruct (quote {a :a b :b [x y & zs] :c}) {:a 1 :b 2 :c (range 10)}) 
    -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9]]
code:  (destruct (quote {a :a b :b [x y & zs] :c d :d :or {:d 1000}}) {:a 1 :b 2 :c (range 10)}) 
    -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9], 'd', 1000]
code:  (destruct (quote {a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}}) {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}) 
    -->  ['a', 1, 'b', 2, 'x', 0, 'y', 1, 'zs', [2, 3, 4, 5, 6, 7, 8, 9], 'd', 1000, 'g', 100, 'h', 200]
code:  (let [[] []] nada) 
    -->  nada
code:  (let [[a b c] [1 2 3]] [a b c]) 
    -->  [1 2 3]
code:  (let [[a b c & cs] (range 10)] [a b c cs]) 
    -->  [0 1 2 [3 4 5 6 7 8 9]]
code:  (let [{a :a b :b c :c} {:a 1 :b 2 :c 3}] [a b c]) 
    -->  [1 2 3]
code:  (let [{a :a b :b [x y & zs] :c} {:a 1 :b 2 :c (range 10)}] [a b x y zs]) 
    -->  [1 2 0 1 [2 3 4 5 6 7 8 9]]
code:  (let [{a :a b :b [x y & zs] :c d :d :or {:d 1000}} {:a 1 :b 2 :c (range 10)}] [a b x y zs d]) 
    -->  [1 2 0 1 [2 3 4 5 6 7 8 9] 1000]
code:  (let [{a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}} {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}] [a b x y zs d g h]) 
    -->  [1 2 0 1 [2 3 4 5 6 7 8 9] 1000 100 200]
code:  (def list-of-things (range 10 20)) 
    -->  [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
code:  (let [[a b c & cs] list-of-things] [a b c cs]) 
    -->  [10 11 12 [13 14 15 16 17 18 19]]
code:  (let [list-of-things (range 10)] (let [[a b c & cs] list-of-things] [a b c cs])) 
    -->  [10 11 12 [13 14 15 16 17 18 19]]
code:  (defn uh-oh [list-of-things] (let [[a b c & cs] list-of-things] [a b c cs])) 
    -->  <function _function.<locals>.fn at 0x1048bc360>
code:  (uh-oh (range 10)) 
    -->  [10 11 12 [13 14 15 16 17 18 19]]
code:  (let [list-of-things (range 10)] list-of-things) 
    -->  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```
Insomma, sembra andare tutto.

## fn
Provo a definire la `fn--` così:
```
(defmacro fn-- [params & body]
  `(fn* [& args]
        (let [[~@params] args]
          (do ~@body))))
```
e non gli piace:
```
pyclj > ((fn-- [[x y]] (+ x y)) [1 2])
Exception: 'args' not found
   executing: (do (eval (read-string input)))
ni
```
la macroexpand viene così: `(fn* [& args] (let [[[x y]] args] (do (+ x y))))`
a me non sembra sbagliata, ma provo questo: `(let* [args [1 2]] (let [[[x y]] args] (do (+ x y))))`
Di nuovo dice che non trova `args`.
Se provo questo `(let* [args [1 2]] (let* [x (first args) y (second args)] (do (+ x y))))`, funziona. Quindi il problema è la `let`.
Questa: `(let [[x y] [1 2]] (+ x y))` funziona.
Questa:
```
pyclj > (def args [1 2])
[1 2]
pyclj > (let [[x y] args] (+ x y))
3
```
anche.
Questa: `(let [args [1 2]] (let [[x y] args] (+ x y)))` anche.

In effetti c'era solo un livello di `[]` in più.
La `fn--` definita così:
```
(defmacro fn-- [params & body]
  `(fn* [& args]
        (let [~@params args]
          (do ~@body))))
```
sembra andare:
```
pyclj > ((fn-- [[x y]] (+ x y)) [1 2])
3
```
Questa no:
```
pyclj > ((fn-- [[{x :x y :y}]] (+ x y)) [{:x 1 :y 2}])
Exception: argument of type 'int' is not iterable
   executing: (do (eval (read-string input)))
nil
```

Questa neanche:
```
pyclj > ((fn-- [{x :x y :y}] (+ x y)) {:x 1 :y 2})
Exception: unsupported operand type(s) for +: 'NoneType' and 'NoneType'
   executing: (do (eval (read-string input)))
nil

```
Succedono stranissime cose:
```
pyclj > ((fn-- [[x y]] (+ x y)) [1 2])
3
pyclj > ((fn-- [[{x :x y :y}]] (+ x y)) [{:x 1 :y 2}])
Exception: argument of type 'int' is not iterable
   executing: (do (eval (read-string input)))
nil
pyclj > (macroexpand (fn-- [[{x :x y :y}]] (+ x y)) )
(fn* [& args] (let [[{x :x y :y}] args] (do (+ x y))))
pyclj > ((fn-- [{x :x y :y}] (+ x y)) {:x 1 :y 2})
Exception: unsupported operand type(s) for +: 'NoneType' and 'NoneType'
   executing: (do (eval (read-string input)))
nil
pyclj > ((fn-- [[x y]] (+ x y)) [1 3])
3
pyclj > ((fn-- [[x y]] (+ x y)) [2 3])
3
pyclj > ((fn-- [[x y]] (+ x y)) [2 7])
3
pyclj > (macroexpand (fn-- [[x y]] (+ x y)))
(fn* [& args] (let [[x y] args] (do (+ x y))))
pyclj > args
[1 2]
pyclj > (def args {:x 5 :y 8})
{:x 5 :y 8}
pyclj > ((fn-- [{x :x y :y}] (+ x y)) [2 7])
13
```
Insomma, sembra non trovare l'`args` definito dalla funzione ma va a prendere quello definito globalmente.
In effetti non stava funzionando neanche qui:
```
code:  (let [list-of-things (range 10)] (let [[a b c & cs] list-of-things] [a b c cs])) 
    -->  [10 11 12 [13 14 15 16 17 18 19]]
code:  (defn uh-oh [list-of-things] (let [[a b c & cs] list-of-things] [a b c cs])) 
    -->  <function _function.<locals>.fn at 0x1048bc360>
code:  (uh-oh (range 10)) 
    -->  [10 11 12 [13 14 15 16 17 18 19]]
```
Continuava a usare il (range 10 20) definito globalmente.

## Altra strada

Il problema, direi, è che essendo `let` una macro, il parametro `binding-vector` non viene valutato. D'altra parte, se non fosse una macro e venisse valutato dovremmo mettere sotto `quote` la parte *binding*, ad es. {x :x y :y}.
Detta così, con l'`eval` sulla parte *values* dovrebbe funzionare. Non funziona perchè questa `eval` viene eseguita al momento sbagliato.
Forse la soluzione è una macro che crea una funzione che chiama destruct coi suoi parametri.

Provato così:
```
(def let< (fn* [binding-vector & body]
               (do
                 (println "let< binding-vector=" binding-vector)
                 (eval (apply list
                              'let*
                              (->> binding-vector
                                   (partition 2)
                                   (mapcat (fn* [bindings] (destruct (first bindings) (eval (second bindings)))))
                                   vec)
                              (list (cons 'do body)))))))

(defmacro let [binding-vector & body]
  (apply list 
         'let<
         (->> binding-vector
              (partition 2)
              (mapcat (fn* [bindings] (vector `~(first bindings) (second bindings)))))
         (list `(quote ~@body))))
  

```
Ma funziona come quella di prima. 
## Altra ancora
Però penso di aver capito meglio il suggerimento dell'articolo. Ritorno su quella strada.
Ma prima un piccolo ragionamento:
L'approccio suggerito alla fine dell'articolo mira a generare con la macro `let` il tipo di codice che produrrei a mano per destrutturare un dato.
Ad esempio, se dovessi estrarre gli elementi di questa struttura: `[1 {:x 2 :y [3 4]}]` per ottenere qualcosa tipo `a 1 x 2 b 3 c 4` quello che produrrebbe la destructure dell'articolo sarebbe, supponendo di chiamare quel dato AA: 
```
a (nth AA 0) 
x (get (nth AA 1) :x) 
c (nth (get (nth AA 1) :y) 0)
d (nth (get (nth AA 1) :y) 1)
```
che indubbiamente funzionerebbe, ma oltre a essere poco elegante (cosa forse ininfluente perchè sarebbe codice generato dalla macro e non visto da nessuno), sarebbe forse migliorabile anche sul piano performance.
Di fatto se davvero dovessi scrivere a mano quel codice scriverei:
```
a (get-in AA [0])
x (get-in AA [1 :x])
c (get-in AA [1 :y 0])
d (get-in AA [1 :y 1])
```
Che non so se sia più performante, ma sicuramente più chiaro. E avrebbe sicuramente il vantaggio che i path della get-in si possono generare a partire dal binding, senza ancora aver bisogno dei valori (cosa importante per la macro `fn`).
Per implementarla così mi mancano:
- implementazione della get-in (cosa che comunque volevo aggiungere)
- rendere i vettori associativi (cosa comunque da fare)
## Rendere i vettori associativi
Il problema è questo:
```
pyclj > (def vv [1 2])
[1 2]
pyclj > (vv 1)
Exception: 'Vector' object is not callable
   executing: (do (eval (read-string input)))
```
Ad oggi i vettori non sono *callable*. Devono diventarlo. E, già che ci siamo devono diventarlo anche gli hash_dict e le keyword.
Ok, fatto, ora posso scrivere:
```
pyclj > (:x {:x 3 :y 4})
3
pyclj > (:y {:x 3 :y 4})
4
pyclj > ({:x 5 :y 6} :y)
6
pyclj > ([1 2 3] 1)
2
```
è bastato aggiungere al fondo del grosso switch dell'interprete:
```
                elif types._vector_Q(f):
                    return f[el[1]]
                elif  types._hash_map_Q(f):
                    return f[el[1]]
                elif types._keyword_Q(f):
                    return el[1][f]
```
Non testo, per il momento, se `el[1]` sia del tipo giusto. Se in caso di errori verranno fuori messaggi troppo sibiliini aggiungerò in controllo.

### Implementare `get-in`
Guardando l'implementazione clojure della `get-in`, vedo che è implementata in modo quasi triviale nel caso senza valore di default:
```
([m ks]
     (reduce1 get m ks))
```
L'implementazione col valore di default è leggermente più complessa, ma si potrebbe adottare. Il problema è che è una funzione multi-arity, userebbe quindi la nuova `fn`, che a sua volta userebbe la `destruct`, che a sua volta potrebbe usare la `get-in`. Non se se davvero rischi di innescare loop infiniti, ma per non rischiare, e anche perchè sta diventando un mattone piuttosto di base potrei implementarla direttamente in python.

Ok, la get-in funziona:
```
code:  (let* [AA [1 {:x 2 :y [3 4]}] a (get-in AA [0]) x (get-in AA [1 :x]) c (get-in AA [1 :y 0]) d (get-in AA [1 :y 1])] [a x c d]) 
    -->  [1 2 3 4]
```
Penso che update-in si possa implementare solo in lisp, per quanto riguarda la assoc-in vedremo. Comunque aspetto di avere un set di test decenti prima di farlo.
### Ora proviamo a implementare la destruct così.
Questa cosa funziona:
```
(def bindings '[a {x :x [c d] :y}])
(def values [1 {:x 2 :y [3 4]}])

(def get-paths-sequential)
(def get-paths-associative)
(def get-paths (fn* [bindings current-path]
                 (when bindings
                   (cond (sequential? bindings)
                         (get-paths-sequential bindings current-path)
                 
                         (map? bindings)
                         (get-paths-associative bindings current-path)
                 
                         :else
                         [bindings current-path]))))

(def get-paths-sequential (fn* [bindings current-path]
                               (map-indexed (fn* [i b] (get-paths b (conj current-path i))) bindings)))
                            
(def get-paths-associative (fn* [binding-map current-path]
                                (let* [ks (keys binding-map)
                                       vs (vals binding-map)]
                                      (mapcat (fn* [k v] (get-paths k (conj current-path v))) ks vs))))
```
e produce questo:
```

code:  (get-paths-sequential (quote [a b c]) []) 
    -->  [['a', [0]], ['b', [1]], ['c', [2]]]
code:  (get-paths-associative (quote {x :x y :y}) []) 
    -->  ['x', ['ʞx'], 'y', ['ʞy']]
code:  (get-paths (quote x) [3 :x]) 
    -->  [x [3 :x]]
code:  (get-paths (quote [a {b :x}]) []) 
    -->  [['a', [0]], ['b', [1, 'ʞx']]]
code:  (get-paths (quote [a {[b c] :x}]) []) 
    -->  [['a', [0]], [['b', [1, 'ʞx', 0]], ['c', [1, 'ʞx', 1]]]]
code:  (get-paths (quote {[a {[b c] :x}] :z e :e}) []) 
    -->  [['a', ['ʞz', 0]], [['b', ['ʞz', 1, 'ʞx', 0]], ['c', ['ʞz', 1, 'ʞx', 1]]], 'e', ['ʞe']]
```
Ad ogni simbolo trovato nel binding viene associato il path da dare alla `get-in` per ricavare il valore di quel simbolo da un valore con lo stesso formato.
Ci si potrebbe già implementare una `let`. Però non gestisce ancora nè i **variadic** nel caso delle sequenze ne **:or** e **:keys** nel caso associativo.
Vediamo se riesco ad aggiungerli.
### Variadic seq
Modificando la get-paths-sequential così:
```
(def get-paths-sequential (fn* [binding-seq current-path]
                               (do
                                 (def variadic? (fn* [bindings]
                                                     (and (>= (count bindings) 2) (= '& (nth bindings (- (count bindings) 2))))))
                                 (if (variadic? binding-seq)
                                   (let* [n-fixed-values (- (count binding-seq) 2)
                                         variadic-sym (last binding-seq)
                                         binding-seq (take binding-seq n-fixed-values)]
                                     (conj  (vec (map-indexed (fn* [i b] (get-paths b (conj current-path i))) binding-seq))  [variadic-sym [(negate n-fixed-values)]]))
                                   (map-indexed (fn* [i b] (get-paths b (conj current-path i))) binding-seq)))))
 ```
Si ottiene questo:
```code:  (get-paths-sequential (quote [a b & c]) []) 
    -->  [[a [0]] [b [1]] [c [-2]]]
```
Con quel `c` definito così basta prendere la parte precedente del path (in questo caso vuota, quindi tutto il valore senza fare get-in) e fare (drop (negate -2)) per ottenere gli argomenti richiesti.
Però pone già il problema di doversi chiedere per ogni argomento se fare o no la get-in.

Vediamo di tirar fuori `:or` e `:keys`.

Ok, questa sembra andare:
```
(def get-paths-sequential)
(def get-paths-associative)
(def get-paths (fn* [bindings current-path]
                 (when bindings
                   (cond (sequential? bindings)
                         (get-paths-sequential bindings current-path)
                 
                         (map? bindings)
                         (get-paths-associative bindings current-path)
                 
                         :else
                         [bindings current-path]))))

(def get-paths-sequential (fn* [binding-seq current-path]
                               (do
                                 (def variadic? (fn* [bindings]
                                                     (and (>= (count bindings) 2) (= '& (nth bindings (- (count bindings) 2))))))
                                 (if (variadic? binding-seq)
                                   (let* [n-fixed-values (- (count binding-seq) 2)
                                         variadic-sym (last binding-seq)
                                         binding-seq (take binding-seq n-fixed-values)]
                                     (conj  (vec (map-indexed (fn* [i b] (get-paths b (conj current-path i))) binding-seq))  [variadic-sym [(negate n-fixed-values)]]))
                                   (map-indexed (fn* [i b] (get-paths b (conj current-path i))) binding-seq)))))
                            
(def get-paths-associative (fn* [binding-map current-path]
                                (let* [default-map (get binding-map :or)
                                       keys-bindings (get binding-map :keys)
                                       binding-map (if keys-bindings
                                                     (apply hash-map (interleave keys-bindings
                                                                                 (map keyword keys-bindings)))
                                                     binding-map)
                                       binding-map (if default-map (dissoc binding-map :or) binding-map)
                                       ks (keys binding-map)
                                       vs (vals binding-map)
                                       f-get-path (fn* [k v]
                                                    (if (contains? default-map v)
                                                      (conj (get-paths k (conj current-path v)) (default-map v))
                                                      (get-paths k (conj current-path v))))]
                                      (vec (map f-get-path ks vs)))))

```
Sembra gestire sia `&` che `:or` che `:keys`
```
code:  (get-paths-sequential (quote [a b c]) []) 
    -->  [['a', [0]], ['b', [1]], ['c', [2]]]
code:  (get-paths-associative (quote {x :x y :y}) []) 
    -->  [[x [:x]] [y [:y]]]
code:  (get-paths (quote x) [3 :x]) 
    -->  [x [3 :x]]
code:  (get-paths (quote [a {b :x}]) []) 
    -->  [['a', [0]], [['b', [1, 'ʞx']]]]
code:  (get-paths (quote [a {[b c] :x}]) []) 
    -->  [['a', [0]], [[['b', [1, 'ʞx', 0]], ['c', [1, 'ʞx', 1]]]]]
code:  (get-paths (quote {[a {[b c] :x}] :z e :e}) []) 
    -->  [[['a', ['ʞz', 0]], [[['b', ['ʞz', 1, 'ʞx', 0]], ['c', ['ʞz', 1, 'ʞx', 1]]]]] [e [:e]]]
code:  (get-paths (quote [a b & c]) []) 
    -->  [[a [0]] [b [1]] [c [-2]]]
code:  (get-paths (quote {x :x y :y :or {:y 33}}) []) 
    -->  [[x [:x]] [y [:y] 33]]
code:  (get-paths (quote {:keys [x y z]}) []) 
    -->  [[x [:x]] [y [:y]] [z [:z]]]
```

Ora posso usarla per farne una `let`.
Ho trovato un bug logico nell'implementazione della `:or`
Pensavo di usare il default get-in, e nei casi semplici avrebbe funzionato.
Questa situazione: `[a {x :x y :y :or {:y 9}}] [3 {:x 4}]` sarebbe stata trasformata in:
```
(let* [a (get-in [3 {:x 4}] [0])
       x (get-in [3 {:x 4}] [1 :x])
       y (get-in [3 {:x 4}] [1 :y] 9)])
```
... che va bene. Ma questa: `[a {x :x [y z] :yz :or {:yz [9 8]}}] [3 {:x 4}]` non poteva funzionare.
Per risolvere ho modificato la `get-paths-associative` in modo che il binding sopra ritorni:
`[[a [0]] [x [1 :x]] [y [1 [:yz [9 8]] 0]] [z [1 [:yz [9 8]] 1]]]`
In pratica il path della `y` ([y [1 [:yz [9 8]] 0]]) è un path che la get-in standard non riconoscerebbe. L'idea è che se nel path è presente un vettore questo contenga, come secondo elemento, il default dello step in corso.
La implemento direttamente in python perchè è molto di base.
```
pyclj > (get-in [1 {:x 4 :y 5} 3] [1 :y])
5
pyclj > (get-in [1 {:x 4 :y 5} 3] [1 [:z 66]])
66
pyclj > (get-in [1 {:x 4 :y 5 :z 44} 3] [1 [:z 66]])
44
pyclj > (get-in [1 {:x 4 :y 5 :zz [44 45]} 3] [1 [:z [66 67]] 1])
67
pyclj > (get-in [1 {:x 4 :y 5 :z [44 45]} 3] [1 [:z [66 67]] 1])
45
```

Ok, funziona tutto e direi che abbiamo la let. Ora potremmo implementare `fn` e `loop` e poi aggiungere le **trailing maps** e `:as`
## fn
Un implementazione molto semplice della `fn` (solo per gestire il destructuring) potrebbe essere questa:
```
(defmacro fn [params & body]
         `(fn* [& vals]
               (let [[~@params] vals]
                 (do ~@body))))
```
Ma non mi piace perchè farebbe diventare tutte le funzioni variadiche (anche quelle che non usano il destructuring)

Implementata così:
```
(def make-p-v-list (fn* [params] (mapcat (fn* [n] [(params n) (symbol (str "val" n))]) (range (count params)))))
(def make-v-list (fn* [params] (mapcat (fn* [n] [(symbol (str "val" n))]) (range (count params)))))

(defmacro fn-- [params & body]
  `(fn* [~@(make-v-list params)]
        (let [~@(make-p-v-list params)]
          (do ~@body))))
```
Funziona e non ha questo problema:
```
pyclj > ((fn-- [x y] (+ x y)) 3 4)
7
pyclj > ((fn-- [[x y]] (+ x y)) [3 4])
7
pyclj > (macroexpand (fn-- [[x y]] (+ x y)))
(fn* [val0] (let [[x y] val0] (do (+ x y))))
pyclj > (macroexpand (fn-- [a [x y]] (+ a x y)))
(fn* [val0 val1] (let [a val0 [x y] val1] (do (+ a x y))))
pyclj > ((fn-- [a [x y]] (+ a x y)) 5 [2 3])
10
```
Ora però va integrata col multi-arity.
Implementata così:
```
; Multi Arity Functions
(defmacro fn+ [params & xs]
  (if (every? list? (cons params xs))
    (let* [make-pair (fn* [params-and-body]
                      (let* [params (first params-and-body)
                            body (rest params-and-body)
                            variadic? (some (fn* [par] (= (str par) "&")) params )
                            k (if variadic? -1 (count params))]
                        [k [params `(do ~@body)]]))
          maf-dict (apply hash-map (apply concat (map make-pair (cons params xs))))]
      `(fn** ~maf-dict))
    `(fn-- ~params  ~@xs)))
```
Si ottiene una semi integrazione, nel senso che nel caso multi-arity non c'è destructuring, ma per le funzioni semplici c'è.
Vorrei che ci fosse il destructuring, ma è più complesso: bisogna inserire parte del codice della `fn--` nel `maf-dict`.
Potrebbe andare così:
```
(defmacro fn+ [params & xs]
  (if (every? list? (cons params xs))
    (let* [make-pair (fn* [params-and-body]
                      (let* [params (first params-and-body)
                            body (rest params-and-body)
                            variadic? (some (fn* [par] (= (str par) "&")) params )
                            k (if variadic? -1 (count params))]
                        [k `[~@(make-v-list params) (let [~@(make-p-v-list params)]
                                                      (do ~@body))]]))
          maf-dict (apply hash-map (apply concat (map make-pair (cons params xs))))]
      `(fn** ~maf-dict))
    `(fn-- ~params  ~@xs)))
```
Che sembra promettente, ma non funziona:
```
pyclj > (macroexpand (fn+ [x y] (+ x y)))
(fn* [val0 val1] (let [x val0 y val1] (do (+ x y))))
pyclj > (macroexpand (fn+ ([x y] (+ x y)) ([[x y]] (recur x y))  ) )
(fn** {2 [val0 val1 (let [x val0 y val1] (do (+ x y)))] 1 [val0 (let [[x y] val0] (do (recur x y)))]})
pyclj > ( (fn+ ([x y] (+ x y)) ([[x y]] (recur x y))) [3 4] )
_multi_arity_function. maf_dict={2: ['val0', 'val1', ['let', ['x', 'val0', 'y', 'val1'], ['do', ['+', 'x', 'y']]]], 1: ['val0', ['let', [['x', 'y'], 'val0'], ['do', ['recur', 'x', 'y']]]]}
Exception: 'val0' not found
```
Mancavano le `[]` intorno ai parametri, ora va:
```
(defmacro fn+ [params & xs]
  (if (every? list? (cons params xs))
    (let* [make-pair (fn* [params-and-body]
                      (let* [params (first params-and-body)
                            body (rest params-and-body)
                            variadic? (some (fn* [par] (= (str par) "&")) params )
                            k (if variadic? -1 (count params))]
                        [k `[[~@(make-v-list params)] (let [~@(make-p-v-list params)]
                                                      (do ~@body))]]))
          maf-dict (apply hash-map (apply concat (map make-pair (cons params xs))))]
      `(fn** ~maf-dict))
    `(fn-- ~params  ~@xs)))

pyclj > (macroexpand (fn+ ([x y] (+ x y)) ([[x y]] (recur x y))  ) )
(fn** {2 [[val0 val1] (let [x val0 y val1] (do (+ x y)))] 1 [[val0] (let [[x y] val0] (do (recur x y)))]})
pyclj > ( (fn+ ([x y] (+ x y)) ([[x y]] (recur x y))) [3 4] )
_multi_arity_function. maf_dict={2: [['val0', 'val1'], ['let', ['x', 'val0', 'y', 'val1'], ['do', ['+', 'x', 'y']]]], 1: [['val0'], ['let', [['x', 'y'], 'val0'], ['do', ['recur', 'x', 'y']]]]}
7
```
Non sono molto sicuro dei variadic, bisogna fare un bel po' di test ...
Infatti la gestione dei variadic è molto compromessa, anche nella `fn--`
```
pyclj > (macroexpand (fn+ ([& v] (apply + v)) ([[x y]] (recur x y))))
(fn** {-1 [[val0 val1] (let [& val0 v val1] (do (apply + v)))] 1 [[val0] (let [[x y] val0] (do (recur x y)))]})
pyclj > (macroexpand (fn-- [& v] (apply + v)))
(fn* [val0 val1] (let [& val0 v val1] (do (apply + v))))
pyclj > 
```

Cos' va:
```
(defmacro fn+ [params & xs]
  (if (every? list? (cons params xs))
    (let* [make-pair (fn* [params-and-body]
                      (let* [params (first params-and-body)
                            body (rest params-and-body)
                            vp (split-variadic params)
                            variadic-param (first vp)
                            fixed-params (second vp)
                            v-list (make-v-list fixed-params)
                            v-list (if variadic-param (vec (concat v-list ['& variadic-param])) v-list) 
                            k (if variadic-param -1 (count params))]
                        [k `[~v-list (let [~@(make-p-v-list fixed-params)]
                                                      (do ~@body))]]))
          maf-dict (apply hash-map (apply concat (map make-pair (cons params xs))))]
      `(fn** ~maf-dict))
    `(fn-- ~params  ~@xs)))
```

Corretto ancora qualcosa, e messo un po' in forma la mini test framework.
Importato qualche test da clojurescript, tolti i *testing*, che non ho ancora implementato.
Ora *destructuring_tests.clj è questo:
```
(deftest test-destructuring
  (is (= [2 1] (let [[a b] [1 2]] [b a])))
  (is (= #{1 2} (let [[a b] [1 2]] #{a b})))
  (is (= [1 2] (let [{a :a b :b} {:a 1 :b 2}] [a b])))
  (is (= [1 2] (let [{:keys [a b]} {:a 1 :b 2}] [a b])))
  (is (= [1 2 [1 2]] (let [[a b :as v] [1 2]] [a b v])))
  (is (= [1 42] (let [{:keys [a b] :or {b 42}} {:a 1}] [a b])))
  (is (= [1 nil] (let [{:keys [a b] :or {c 42}} {:a 1}] [a b])))
  (is (= [2 1] (let [[a b] '(1 2)] [b a])))
  (is (= {1 2} (let [[a b] [1 2]] {a b})))
  (is (= [2 1] (let [[a b] (seq [1 2])] [b a])))
  (let [{:keys [:a :b]} {:a 1 :b 2}]
    (is (= 1 a))
    (is (= 2 b))))
```
e se eseguo i test viene fuori questo:
```
pyclj > (load-file "./tests/destructuring_tests.clj")
./tests/destructuring_tests.clj
pyclj > (run-test test-destructuring)
-  {:type :pass :message nil :expected (= [2 1] (let [[a b] [1 2]] [b a])) :actual true}
-  {:type :pass :message nil :expected (= (set 1 2) (let [[a b] [1 2]] (set a b))) :actual true}
-  {:type :pass :message nil :expected (= [1 2] (let [{a :a b :b} {:a 1 :b 2}] [a b])) :actual true}
-  {:type :pass :message nil :expected (= [1 2] (let [{:keys [a b]} {:a 1 :b 2}] [a b])) :actual true}
-  {:type :fail :message nil :expected (= [1 2 [1 2]] (let [[a b :as v] [1 2]] [a b v])) :actual false}
-  {:type :fail :message nil :expected (= [1 42] (let [{:keys [a b] :or {b 42}} {:a 1}] [a b])) :actual false}
-  {:type :pass :message nil :expected (= [1 nil] (let [{:keys [a b] :or {c 42}} {:a 1}] [a b])) :actual true}
-  {:type :pass :message nil :expected (= [2 1] (let [[a b] (quote (1 2))] [b a])) :actual true}
-  {:type :fail :message nil :expected (= {1 2} (let [[a b] [1 2]] {a b})) :actual false}
-  {:type :pass :message nil :expected (= [2 1] (let [[a b] (seq [1 2])] [b a])) :actual true}
-  {:type :error :message nil :expected (= 1 a) :actual {'err': Exception("'a' not found"), 'a1': ['let', ['value__', ['=', 1, 'a']], ['if', 'value__', ['do-report', {'ʞtype': 'ʞpass', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 1, 'a']], 'ʞactual': 'value__'}], ['do-report', {'ʞtype': 'ʞfail', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 1, 'a']], 'ʞactual': 'value__'}]]], 'ast_info': [['a', ['./tests/destructuring_tests.clj', (13, 10)]], [['=', 1, 'a'], ['./tests/destructuring_tests.clj', (13, 2)]], [['let*', ['value__', ['=', 1, 'a']], ['do', ['if', 'value__', ['do-report', {'ʞtype': 'ʞpass', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 1, 'a']], 'ʞactual': 'value__'}], ['do-report', {'ʞtype': 'ʞfail', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 1, 'a']], 'ʞactual': 'value__'}]]]], None]], 'python_traceback': 'Traceback (most recent call last):\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 165, in EVAL\n    return EVAL(a1, env)\n           ^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 116, in EVAL\n    let_env.set(a1[i], EVAL(a1[i+1], let_env))\n                       ^^^^^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 224, in EVAL\n    el = eval_ast(ast, env)\n         ^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 71, in eval_ast\n    return types._list(*map(lambda a: EVAL(a, env), ast))\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 71, in <lambda>\n    return types._list(*map(lambda a: EVAL(a, env), ast))\n                                      ^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 91, in EVAL\n    return eval_ast(ast, env)\n           ^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 69, in eval_ast\n    return env.get(ast)\n           ^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/env.py", line 33, in get\n    raise Exception("\'" + key + "\' not found")\nException: \'a\' not found\n'}}
-  {:type :error :message nil :expected (= 2 b) :actual {'err': Exception("'b' not found"), 'a1': ['let', ['value__', ['=', 2, 'b']], ['if', 'value__', ['do-report', {'ʞtype': 'ʞpass', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 2, 'b']], 'ʞactual': 'value__'}], ['do-report', {'ʞtype': 'ʞfail', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 2, 'b']], 'ʞactual': 'value__'}]]], 'ast_info': [['b', ['./tests/destructuring_tests.clj', (14, 10)]], [['=', 2, 'b'], ['./tests/destructuring_tests.clj', (14, 2)]], [['let*', ['value__', ['=', 2, 'b']], ['do', ['if', 'value__', ['do-report', {'ʞtype': 'ʞpass', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 2, 'b']], 'ʞactual': 'value__'}], ['do-report', {'ʞtype': 'ʞfail', 'ʞmessage': None, 'ʞexpected': ['quote', ['=', 2, 'b']], 'ʞactual': 'value__'}]]]], None]], 'python_traceback': 'Traceback (most recent call last):\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 165, in EVAL\n    return EVAL(a1, env)\n           ^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 116, in EVAL\n    let_env.set(a1[i], EVAL(a1[i+1], let_env))\n                       ^^^^^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 224, in EVAL\n    el = eval_ast(ast, env)\n         ^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 71, in eval_ast\n    return types._list(*map(lambda a: EVAL(a, env), ast))\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 71, in <lambda>\n    return types._list(*map(lambda a: EVAL(a, env), ast))\n                                      ^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 91, in EVAL\n    return eval_ast(ast, env)\n           ^^^^^^^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/interpreter.py", line 69, in eval_ast\n    return env.get(ast)\n           ^^^^^^^^^^^^\n  File "/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/env.py", line 33, in get\n    raise Exception("\'" + key + "\' not found")\nException: \'b\' not found\n'}}
nil
```

Il primo fail riguarda il fatto che non ho implementato `:as` `(= [1 2 [1 2]] (let [[a b :as v] [1 2]] [a b v]))`
Il secondo il fatto che la `:or` deve fare un merge. `(= [1 42] (let [{:keys [a b] :or {b 42}} {:a 1}] [a b]))`
Il terzo non lo capisco. Torna `{a 2}` invece di `{1 2}`. Da debuggare. `(= {1 2} (let [[a b] [1 2]] {a b}))`
L'ultimo è un errore che deriva dal fatto che probabilmente ho capito male come deve funzionare la :keys.
Questo `(let [{:keys [a b]} {:a 1 :b 2}] [a b])` funziona, ma a quanto pare deve funzionare questo: `(let [{:keys [:a :b]} {:a 1 :b 2}] [a b])`. O meglio, devono funzionare tutti e due (in clojure è così).

Comincio dalla `:as`.
La `take` e la `drop` avevano i parametri al contrario. Corretti.
Aggiunta la `:as` ai sequential. E sembra andare:
```
pyclj > (let [[a b & c :as v] [1 2 3 4]] [a b c v])
[1 2 (3 4) [1 2 3 4]]
```
Aggiunta la `:as` anche alle associative, e sembra andare:
```
pyclj > (let [{x :x :as all} {:x 2 :y 3}] [x all])
[2 {:x 2 :y 3}]
```
Bene, vediamo il problema dell'`:or`.
Questo: 
```
pyclj > (let [{:keys [a b] :or {:b 42}} {:a 1}] [a b])
[1 42]
```
Funziona. Quindi il problema è che non accetta `:or {b 42}` (ha il problema inverso delle `:keys`, bisogna in entrambi i casi accettare sia simboli che keywords).
O no ?
In clojure viene fuori questo:
```
user=> (let [{:keys [a b] :or {:b 42}} {:a 1}] [a b])
Syntax error macroexpanding clojure.core/let at (REPL:1:1).
:b - failed: simple-symbol? at: [:bindings :form :map-destructure :or 0] spec: :clojure.core.specs.alpha/or
{:keys [a b], :or {:b 42}} - failed: simple-symbol? at: [:bindings :form :local-symbol] spec: :clojure.core.specs.alpha/local-name
{:keys [a b], :or {:b 42}} - failed: vector? at: [:bindings :form :seq-destructure] spec: :clojure.core.specs.alpha/seq-binding-form
user=> (let [{:keys [a b] :or {b 42}} {:a 1}] [a b])
[1 42]
user=> (let [{:keys [:a :b] :or {b 42}} {:a 1}] [a b])
[1 42]
user=> (let [{:keys [:a :b] :or {:b 42}} {:a 1}] [a b])
Syntax error macroexpanding clojure.core/let at (REPL:1:1).
:b - failed: simple-symbol? at: [:bindings :form :map-destructure :or 0] spec: :clojure.core.specs.alpha/or
{:keys [:a :b], :or {:b 42}} - failed: simple-symbol? at: [:bindings :form :local-symbol] spec: :clojure.core.specs.alpha/local-name
{:keys [:a :b], :or {:b 42}} - failed: vector? at: [:bindings :form :seq-destructure] spec: :clojure.core.specs.alpha/seq-binding-form
user=>
```
in pratica `:keys` accetta sia simboli che keyword, mentre `:or` accetta solo simboli. Che strano.
Inoltre non funziona questo:
```
user=> (let [{(let [{:keys ["a" :b] :or {b 42}} {:a 1}] [a b])
Syntax error macroexpanding clojure.core/let at (REPL:1:1).
"a" - failed: ident? at: [:bindings :form :map-destructure :keys] spec: :clojure.core.specs.alpha/keys
{:keys ["a" :b], :or {b 42}} - failed: simple-symbol? at: [:bindings :form :local-symbol] spec: :clojure.core.specs.alpha/local-name
{:keys ["a" :b], :or {b 42}} - failed: vector? at: [:bindings :form :seq-destructure] spec: :clojure.core.specs.alpha/seq-binding-form
```
che invece io avrei reso possibile se sequivo la prima cosa che mi è venuta in mente (chiamare `(keyword sym)` intorno a ogni *key*).
Mi sa che faccio lo stesso così, e lascio aperte tutte le possibilità (compresa `:or {:b 42}`)
No, ho capito meglio:
```
user=> (let [{(let [{a :a b :b :or {b 42}} {:a 1}] [a b])
[1 42]
user=> (let [{(let [{a :a pippo :b :or {b 42}} {:a 1}] [a pippo])
[1 nil]
user=> (let [{(let [{a :a pippo :b :or {pippo 42}} {:a 1}] [a pippo])
[1 42]
```
la hash-map passata alla `:or` fa riferimento ai simboli, non alle keys della mappa da destrutturare. Mi sembra una scelta del menga.
Infatti in clojure non funziona (e non può funzionare) questo: `(let [{x :x [y z] :yz :or {:yz [88 89]}} {:x 3}] (+ x y))`, mi sa che per il momento lascio la mia implementazione. Gli :or usano le keyword, e le :keys no.

Alla fine, fatte le dovute correzioni ai test rimane solo questa che non funziona:
```
pyclj > (let [[a b] [1 2]] {a b})
{a 2}
```
In clojure torna {1 2}.
Mettendo un vettore funziona anche a me:
```
pyclj > (let [[a b] [1 2]] [a b])
[1 2]
```
Quindi il problema non è strettamente legato al destructuring. È un problema che ha la `let*`
```
pyclj > (let [a 1 b 2] [a b])
[1 2]
pyclj > (let [a 1 b 2] {a b})
{a 2}
pyclj > (let* [a 1 b 2] {a b})
{a 2}
```
Sembra non faccia l'eval delle key di un'hash-map.
L'ho aggiunta a `eval_ast`, nell'interprete.
```
    elif types._hash_map_Q(ast):
        return types.Hash_Map((EVAL(k, env), EVAL(v, env)) for k, v in ast.items())
 ```
Ora va:
```
pyclj > (let [[a b] [1 2]] {a b})
{1 2}
```
Ma ho un vago ricordo di aver letto qualcosa a riguardo nelle note del *mal*. Boh, se dà problemi da qualche parte ci ritorno.
## loop
Credo si possa passare a implementare il destructuring nella `loop`. Dovrebbe essere identico a `let`.
No, non è uguale alla `let`.
Il problema è che sulla `recur` il destructuring non viene più applicato. È necessario che il destructuring venga fatto nel body.

Così:
```
(defmacro loop [bindings & xs] 
  (let* [pairs (vec (partition 2 bindings))
         loop-bindings (vec (map first pairs))
         values (vec (map second pairs))
         names (vec (map (fn* [i] (symbol (str "val" i))) (range (count loop-bindings))))]
        `(loop* [~@(mapcat (fn* [n v] [n v]) names values)]
           (let [~@(mapcat (fn* [n v] [n v]) loop-bindings names)]
             (do ~@xs)))))
```
Sembra funzionare:
```
pyclj > (loop [[x y] [1 2] z 3] (println x y z) (if (< y 0) x (recur [(inc x) (dec y)] (* 3 z))))
1 2 3
2 1 9
3 0 27
4 -1 81
4
```

Tutti questi "val0" "val1" .... che sto mettendo rischiano di collidere coi nomi utente ? Forse no, se vengono fuori problemi ci ritorno. Clojure ha qualche meccanismo per generare nomi temporanei ma non lo conosco bene, qualcosa con `#` alla fine, magari indago.

Per ora passerei alle **trailing maps**
## Keyword arguments
Partiamo dagli esempi di [questo](https://clojure.org/guides/destructuring) articolo: 

Questa: 
``` 
(defn configure [val options]
   (let [{:keys [debug verbose] :or {:debug false, :verbose false}} options]
     (str "val = " val " debug = " debug " verbose = "  verbose)))
(configure 12 {:debug true})
```
ovviamente funziona e torna `val = 12 debug = true verbose = false`.
Ma questa: `(configure 12 :debug true)` dà errore.
Bisogna, da qualche parte, riconoscere che gli ultimi elementi del binding sono **coppie keyword-valore** e raccoglierle in una hash-map.

Potrebbe essere una cosa del genere:
```
(def compact-key-val-trailing-pairs (fn* [vals]
                                         (loop* [vals vals
                                                 hm {}
                                                 resvals []
                                                 k nil
                                                 has-kv-pair? false]
                                                (cond
                                                  (and (< (count vals) 1) k)  (throw "Odd number of trailing key-value pairs")
                                                  (empty? vals) (if (empty? hm) resvals (conj resvals hm))
                                                  (keyword? (first vals)) (recur (rest vals) hm resvals (first vals) true)
                                                  k (recur (rest vals) (assoc hm k (first vals)) resvals nil has-kv-pair?)
                                                  (map? (first vals)) (recur (rest vals) (merge hm (first vals)) resvals nil has-kv-pair?)
                                                  has-kv-pair? (throw "Non trailing key-value pairs")
                                                  (empty? hm) (recur (rest vals) {} (conj resvals (first vals)) nil false)
                                                  true (recur (rest vals) {} (conj resvals hm (first vals)) nil false)))))
```
Ma mi manca la `merge`
Ho provato a prenderla dal sorgente di clojure, ma non ho la reduce1.
Provando a giocarci vedo che la mia `map` non funziona sulle hash-maps:
```
pyclj > (map (fn [v] (do (println v) v)) {:a 1 :b 2})
:a
:b
(:a :b)
```
Mentre in clojure:
```
user=> (map (fn [v] (do (println v) v)) {:a 1 :b 2})
([:a 1]
[:b 2]
[:a 1] [:b 2])
```
(fa un po' cagare anche clojure nella print)

Rivedo la mia `map`.
Ok, map funziona e la `compact-key-val-trailing-pairs` sembra fare quello che deve:
```
code:  (compact-key-val-trailing-pairs (quote [])) 
    -->  []
code:  (compact-key-val-trailing-pairs (quote [:a 1])) 
    -->  [{:a 1}]
code:  (compact-key-val-trailing-pairs (quote [23 :a 1])) 
    -->  [23 {:a 1}]
code:  (compact-key-val-trailing-pairs (quote [23 {:A 3 :B 27} 41 {:b 33 :c 44} :a 1])) 
    -->  [23 {:A 3 :B 27} 41 {:b 33 :c 44 :a 1}]
```
Ora dobbiamo vedere come usarla. A questo punto ho, anzitutto, il dubbio se clojure applichi questo meccanismo solo alle `fn` o in generale a tutti i casi di destructuring. Provo.
Direi che lo fa dovunque c'è destructuring:
```
user=> (let [[val & {:keys [a b] :or {a 1 b 2} :as opts}] [21 :a 1]] [a opts])
[1 {:a 1}]
```
... ma è molto più semplice di quanto credevo: si applica solo ai variadic.
## Rewind
Alla fine veniva un po' troppo complicata la gestione dei trailing maps.
Ho modificato il tutto in modo che la get-paths (rinominata `get-r-paths`) non torni più dei paths da dare in pasto alla `get-in` ma direttamente il codice che sarà usato nella `let`.
Inoltre nei vari passaggi vengono prodotte le coppie nome-valore relative ad ogni passo di destructuring. Nel caso sia preente l'`:as` il nome è quello dato dall'utente, se questo non è presente viene usato un nome autogenerato.
Ad esempio, `(let [[x y] [3 4]] (+ x y))` produce: `(let* [__as_1 [3 4] x (nth __as_1 0) y (nth __as_1 1)] (do (+ x y))`
mentre, se si aggiunge l'`:as`, come in `(let [[x y :as xv_vector] [3 4]] (+ x y)))` il codice prodotto diventa: `(let* [xv_vector [3 4] x (nth xv_vector 0) y (nth xv_vector 1)] (do (+ x y)))`

Così sembrano passare tutti i test:
```
code:  (get-r-paths-sequential (quote [a b c]) (quote pippo) 3) 
    -->  [[__as_3 pippo] [a (nth __as_3 0)] [b (nth __as_3 1)] [c (nth __as_3 2)]]
code:  (get-r-paths-associative (quote {x :x y :y}) (quote pippo) 3) 
    -->  [[__as_3 pippo] [x (get __as_3 :x)] [y (get __as_3 :y)]]
code:  (get-r-paths (quote x) (quote pippo) 5) 
    -->  [[x pippo]]
code:  (get-r-paths (quote [a {b :x}]) (quote foo) 0) 
    -->  [[__as_1 foo] [a (nth __as_1 0)] [__as_3 (nth __as_1 1)] [b (get __as_3 :x)]]
code:  (get-r-paths (quote [a {[b c] :x}]) (quote foo) 0) 
    -->  [[__as_1 foo] [a (nth __as_1 0)] [__as_3 (nth __as_1 1)] [__as_5 (get __as_3 :x)] [b (nth __as_5 0)] [c (nth __as_5 1)]]
code:  (get-r-paths (quote {[a {[b c] :x}] :z e :e}) (quote foo) 0) 
    -->  [[__as_1 foo] [__as_3 (get __as_1 :z)] [a (nth __as_3 0)] [__as_5 (nth __as_3 1)] [__as_7 (get __as_5 :x)] [b (nth __as_7 0)] [c (nth __as_7 1)] [e (get __as_1 :e)]]
code:  (get-r-paths (quote [a b & c]) (quote foo) 0) 
    -->  [[__as_1 foo] [a (nth __as_1 0)] [b (nth __as_1 1)] [c (drop 2 __as_1)]]
code:  (get-r-paths (quote {x :x y :y :or {:y 33}}) (quote foo) 0) 
    -->  [[__as_1 foo] [x (get __as_1 :x)] [y (get __as_1 :y 33)]]
code:  (get-r-paths (quote {:keys [x y z]}) (quote foo) 0) 
    -->  [[__as_1 foo] [x (get __as_1 :x)] [y (get __as_1 :y)] [z (get __as_1 :z)]]
code:  (get-r-paths (quote [a {x :x [y z] :yz :or {:yz [9 8]}}]) (quote foo) 0) 
    -->  [[__as_1 foo] [a (nth __as_1 0)] [__as_3 (nth __as_1 1)] [x (get __as_3 :x)] [__as_5 (get __as_3 :yz [9 8])] [y (nth __as_5 0)] [z (nth __as_5 1)]]
code:  (let [x 3 y 4] (+ x y)) 
    -->  7
code:  (let [[x y] [3 4]] (+ x y)) 
    -->  7
code:  (let [{x :x [y z] :yz} {:x 3 :yz [4 5]}] (+ x y)) 
    -->  7
code:  (let [{x :x [y z] :yz :or {:yz [88 89]}} {:x 3}] (+ x y)) 
    -->  91
code:  (let [{x :x [y z] :yz :or {:yz [88 89] :x 4}} {}] (+ x y)) 
    -->  92
code:  (let [{:keys [x y]} {:x 7 :y 2}] (+ x y)) 
    -->  9
code:  (let [{:keys [x y] :or {:x 7 :y 2}} {}] (+ x y)) 
    -->  9
code:  (let [[a & v] [1 2 3]] (- (apply + v) a)) 
    -->  4
code:  (let [[x {a :a b :b :as y} & {:keys [o1 o2] :as v}] [3 {:a 32 :b 44} :o1 5 :o2 6]] [x a b y o1 o2 v]) 
    -->  [3 32 44 {:a 32 :b 44} 5 6 {:o1 5 :o2 6}]
code:  ((fn ([x y] (+ x y)) ([[x y]] (recur x y))) [3 4]) 
    -->  7
code:  ((fn ([& v] (apply + v)) ([[x y]] (recur x y))) [3 4]) 
    -->  7
code:  ((fn ([& v] (apply + v)) ([[x y]] (recur x y))) [3 4 5]) 
    -->  7
code:  (destruct (quote []) []) 
    -->  [[__as_1 []]]
code:  (destruct (quote [a b c]) [1 2 3]) 
    -->  [[__as_1 [1 2 3]] [a (nth __as_1 0)] [b (nth __as_1 1)] [c (nth __as_1 2)]]
code:  (destruct (quote [a b c & cs]) (range 10)) 
    -->  [[__as_1 (0 1 2 3 4 5 6 7 8 9)] [a (nth __as_1 0)] [b (nth __as_1 1)] [c (nth __as_1 2)] [cs (drop 3 __as_1)]]
code:  (destruct (quote {a :a b :b c :c}) {:a 1 :b 2 :c 3}) 
    -->  [[__as_1 {:a 1 :b 2 :c 3}] [a (get __as_1 :a)] [b (get __as_1 :b)] [c (get __as_1 :c)]]
code:  (destruct (quote {a :a b :b [x y & zs] :c}) {:a 1 :b 2 :c (range 10)}) 
    -->  [[__as_1 {:a 1 :b 2 :c (0 1 2 3 4 5 6 7 8 9)}] [a (get __as_1 :a)] [b (get __as_1 :b)] [__as_3 (get __as_1 :c)] [x (nth __as_3 0)] [y (nth __as_3 1)] [zs (drop 2 __as_3)]]
code:  (destruct (quote {a :a b :b [x y & zs] :c d :d :or {:d 1000}}) {:a 1 :b 2 :c (range 10)}) 
    -->  [[__as_1 {:a 1 :b 2 :c (0 1 2 3 4 5 6 7 8 9)}] [a (get __as_1 :a)] [b (get __as_1 :b)] [__as_3 (get __as_1 :c)] [x (nth __as_3 0)] [y (nth __as_3 1)] [zs (drop 2 __as_3)] [d (get __as_1 :d 1000)]]
code:  (destruct (quote {a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}}) {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}) 
    -->  [[__as_1 {:a 1 :b 2 :c (0 1 2 3 4 5 6 7 8 9) :e {:g 100 :h 200}}] [a (get __as_1 :a)] [b (get __as_1 :b)] [__as_3 (get __as_1 :c)] [x (nth __as_3 0)] [y (nth __as_3 1)] [zs (drop 2 __as_3)] [d (get __as_1 :d 1000)] [__as_3 (get __as_1 :e)] [g (get __as_3 :g)] [h (get __as_3 :h)]]
code:  (let [[] []] nada) 
    -->  nada
code:  (let [[a b c] [1 2 3]] [a b c]) 
    -->  [1 2 3]
code:  (let [[a b c & cs] (range 10)] [a b c cs]) 
    -->  [0 1 2 (3 4 5 6 7 8 9)]
code:  (let [{a :a b :b c :c} {:a 1 :b 2 :c 3}] [a b c]) 
    -->  [1 2 3]
code:  (let [{a :a b :b [x y & zs] :c} {:a 1 :b 2 :c (range 10)}] [a b x y zs]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9)]
code:  (let [{a :a b :b [x y & zs] :c d :d :or {:d 1000}} {:a 1 :b 2 :c (range 10)}] [a b x y zs d]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9) 1000]
code:  (let [{a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}} {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}] [a b x y zs d g h]) 
    -->  [1 2 0 1 (2 3 4 5 6 7 8 9) 1000 100 200]
code:  (def list-of-things (range 10 20)) 
    -->  (10 11 12 13 14 15 16 17 18 19)
code:  (let [[a b c & cs] list-of-things] [a b c cs]) 
    -->  [10 11 12 (13 14 15 16 17 18 19)]
code:  (let [list-of-things (range 10)] (let [[a b c & cs] list-of-things] [a b c cs])) 
    -->  [0 1 2 (3 4 5 6 7 8 9)]
code:  (defn uh-oh [list-of-things] (let [[a b c & cs] list-of-things] [a b c cs])) 
    -->  <function _function.<locals>.fn at 0x102dcade0>
code:  (uh-oh (range 10)) 
    -->  [0 1 2 (3 4 5 6 7 8 9)]
code:  (let [list-of-things (range 10)] list-of-things) 
    -->  (0 1 2 3 4 5 6 7 8 9)
code:  (defn configure [val & {:keys [debug verbose] :or {:debug false :verbose false} :as options}] (str val =  val  debug =  debug  verbose =  verbose)) 
    -->  <function _function.<locals>.fn at 0x102dcb420>
code:  (configure 12 {:debug true}) 
    -->  val = 12 debug = true verbose = false
code:  (configure 12 :debug true) 
    -->  val = 12 debug = true verbose = false
code:  (defn ma-configure ([val & {:keys [debug verbose] :or {:debug false :verbose false} :as options}] (str val =  val  debug =  debug  verbose =  verbose)) ([] (ma-configure 17 :verbose true))) 
    -->  <function _multi_arity_function.<locals>.fn at 0x102fcf920>
code:  (ma-configure) 
    -->  val = 17 debug = false verbose = true
code:  (ma-configure 21) 
    -->  val = 21 debug = false verbose = false
code:  (ma-configure 21 :debug true) 
    -->  val = 21 debug = true verbose = false
code:  (ma-configure 21 {:verbose true}) 
    -->  val = 21 debug = false verbose = true
code:  (merge {:a 1 :b 2 :c 3} {:b 10 :d 20} {:a 11 :x 87}) 
    -->  {:a 11 :b 10 :c 3 :d 20 :x 87}
code:  (compact-key-val-trailing-pairs (quote [])) 
    -->  {}
code:  (compact-key-val-trailing-pairs (quote [:a 1])) 
    -->  {:a 1}
code:  (compact-key-val-trailing-pairs (quote [23 :a 1])) 
    -->  {:a 1}
code:  (compact-key-val-trailing-pairs (quote [23 {:A 3 :B 27} 41 {:b 33 :c 44} :a 1])) 
    -->  {:b 33 :c 44 :a 1}
```
Ok, non sono tests, ma quello è il programma del prossimo passo.
