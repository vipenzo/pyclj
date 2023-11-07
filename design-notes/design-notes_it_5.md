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

