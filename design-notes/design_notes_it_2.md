# better diagnostics
Il goal corrente è di dotare l’interprete della possibilità di segnalare eventuali errori mostrando le coordinate (filename, se esiste e riga e colonna) della definizione che causa l’errore o l’eccezione.
## il problema
La difficoltà, che rende l’aggiunta di questa funzionalità particolarmente onerosa, è che l’informazione relativa al filename e alla posizione nel file di ogni elemento sintattico si perde molto prima che il codice venga interpretato.
Nell’implementazione mal la funzione load-file è questa:
(def! load-file 
        (fn* [f] 
            (eval (read-string 
                    (str "(do " (slurp f) "nil)" ) )))))
Come si vede la variabile f, che contiene il filename non viene propagata. Gli eventuali errori saranno trovati durante l’analisi lessicale (fatta da read-string) o durante l’esecuzione (eval) e non potranno far riferimento al nome file. Riga e colonna, poi, possono essere riconosciute solo dalla read-string che riceve come stringa l’intero contenuto del file.
## propagazione del nome file
La load-file viene riscritta così:
(def! load-file 
        (fn* [f] 
            (let* [content (slurp f)
                  old-file (set-current-file f)]
                (do 
                    (try*
                        (eval (read-string (str "(do " content "\nnil)")))
                        (catch* e (print_exception e)))
                    (set-current-file old-file)))))
 Uso ancora le versioni \* di fn e let perché vengono definite in core.mal (che viene caricato con load-file), e non sono quindi ancora disponibili.
La funzione **set-current-file** è definita in reader.py e semplicemente memorizza l’informazione in una variabile globale, tornando il valore precedente.
## propagare riga e colonna delle definizioni
### riscritto il tokenizer
Associare l’informazione di riga e colonna viene fatto riscrivendo il tokenizer di reader.py (ora si chiama coords_tokenize). La nuova versione non ritorna una lista di token ma una lista di tuple nel formato `[token, riga, colonna]`_
La lista dei token è utilizzata solo da read-string, per cui queste modifiche restano locali a questo file.
### modificare l'ast (o, meglio, non farlo)
Ora viene il bello: l’informazione (file, riga, colonna) associata ad ogni token deve essere trasferita agli elementi dell’AST, ma bisogna farlo in modo da non dover modificare troppo l’interprete (Eval). Serve quindi un modo di associare questa informazione agli elementi dell’AST facendo in modo che questo possano essere usati come prima da Eval.
Python offre sostanzialmente due modi di fare questo: metadati e attributi. Il problema è che tutti e due non sono disponibili per i tipi base (numeri, stringhe, booleani etc …). Decido di non rendere tacciabili questi valori e offrire la funzionalità solo per gli altri elementi del linguaggio (quelli rappresentati da classi Python).
Implementata per I symbols e funziona.
Ho aggiunto alla classe Reader le funzioni *filepath* e *coords* e le uso nella *read_atom* in questo modo:
`set_coords(_symbol(token), reader)`
La funzione *set_coords* legge dal reader filename, riga e colonna dell’ultimo token parsato e li associa all’attributo __coords__ dell’oggetto.
Ho aggiunto quindi a core.py la funzione *get-coords* che torna questo attributo, se presente.
Ora dopo il parsing del file ‘destruct.mal’ che contiene, ad esempio, la definizione:




(def a '(1 2 3 4 5))
(def sss 'foo)
(def b [5 6 7 8])

Posso scrivere  `(get-coords sss)`e ottenere:
 `['destruct.mal', (6, 11)]`
### Ora bisogna farlo funzionare per gli altri elementi.
#### sequences. 
Aggiunto:
```
 ast = set_coords(ast, reader)
```
Alla funzione *read_sequence* di reader.py, ma ho dovuto assicurarmi che tutti quelli che la chiamano usino `_list()` e non `list()`. A quanto pare le liste in python non possono avere attributi, mentre `_list()` torna un’istanza della classe List().
Ora *get-coords* funziona, nel caso del file sopra, per *a* ed *sss*, ma non per *b*. Non capisco perchè.
#### wrong way: restart
Ok, forget!, stavo sbagliando approccio. Tutto quello che mi serve è associare ad ogni simbolo che finisce in un Env le sue coordinate. Alla fine era più semplice del previsto e probabilmente si può implementare meglio, ma almeno funziona.
Ho aggiunto a env.py, nella classe env il dizionario self.coords che conterrà associazioni tra keys e coords.
Aggiunto a Env il metodo get_coords, che data una key e se quella key ha coordinate le ritorna._Aggiunto all’interprete la special form “get-coord” (tolta quella da core.py), che ha un parametro (key). La get-coord cerca nella pila corrente degli env quale ha la key e se la trova ritorna le sue coordinate. Ora di ogni oggetto riesco a ottenere le coordinate. Ad esempio:
```
pyclj > (get-coords defn)
['/Users/vipenzo/Documents/Progetti/Blender/pyclj/mal/core.mal', (123, 11)]
``````
… che è proprio dove viene definito **defn**.

#### Ora bisogna usare questa informazione nelle eccezioni.
Ci sono quattro posti in cui possono avvenire eccezioni:

1. Errori di implementazione python

    Non ci interessano granchè qui. Il traceback di python ci porta sull'errore

2. Errori lessicali riconosciuti dal reader
    Dobbiamo passare l'informazione delle coordinate all'eccezione
    Fatto e funziona.
    C'è un piccolo problema, viene fuori ad esempio non chiudendo una parentesi, il reader se ne accorge all'EOF e segnala come posizione dell'errore una posizione che è un po' oltre la lunghezza effettiva del file. Il problema nasce dal fatto che la stringa passata alla read-string non è solo il contenuto del file, questo viene incapsulato in "(do <content> \n nil)", per forzare l'interprete a eseguire tutto il file e ritornare nil come valore. Ce lo teniamo, sarebbe troppo lavoro rispetto all'utilità.
    Comunque non mi piace che se ne accorga solo a EOF, ovviare a questo sarebbe molto meglio.
3. Eccezioni generate dal codice utente
    Bisogna lavorare sull'implementazione della try*/catch* per fornire l'informazione coordinate (che sta da qualche parte, probabilmente nella lista che contiene la try*)
4. La get di Env (in env.py) genera un'eccezione quando si prova a fare get di un simbolo che non esiste.
    Non si può risolvere in Env. Non ci sono informazioni utili, bisogna intercettare l'Exception dal chiamante, che dovrebbe essere sempre l'interprete (credo).
    A rigore **Env.get** non dovrebbe mai essere chiama se non dopo aver verificato con una **find** che l'elemento ci sia. 

Ho messo un po' di stampe di debug e analizzato meglio il codice dell'interprete, e credo si possa dire questo:
- gli ast che arrivano al loop interno di EVAL hanno quasi tutti le coordinate
- fanno eccezione quelli che iniziano con quote, quasiquote, cons, concat, in pratica quelli generati da macro
- la parte di macroexpand è da rivedere (chiama env.get senza fare prima find, direi proprio che è un baco)
- la parte prima del loop (quella che chiama ast_eval ha bisogno di qualche precauzione, da lavorarci)
- la sequenza iniziale (creata da load-file), (do (read-file content) nil), va dotata di coordinate fake (probabilmente è la stessa cura da fare al resto.)

Proviamo questa strada:
1. Aggiunta la funzione **propagate_coords** che copia le coordinate da un elemento dell'ast a un altro
2. Chiamata nella defmacro! per copiare nella lista che rappresenta l'espansione della macro le coordinate le coordinate del simbolo a cui sarà associata

## NO
Mi sto rendendo conto che probabilmente non è la via giusta.
Sto tentando di associare ad ogni elemento dell'AST le coordinate, ma diventa un'impresa titanica, perchè pezzi dell'AST vengono costruiti in tantissimi posti: è proprio la caratteristica del Lisp questa flessibilità. Su questa strada rischio di fare un lavoro enorme e che paga poco.

Rifocalizziamo quello che vorrei ottenere:
1. Poter ottenere, dato il nome di una funzione dove è stata definita.
    e questa funzionalità l'abbiamo già ottenuta semplicemente associano le coordinate ai simboli nell'env.
2. A fronte di un eccezione che si verifica runtime poter indicare, con la massima precisione possibile dov'è l'errore
3. Avere, sempre nel caso di eccezione runtime uno stack-trace *clojure*, cioè la lista delle chiamate che ha portato all'errore

Ora, se ci accontentassimo, sia per il punto 2 che per il 3 di avere semplicemente il nome della funzione il problema avrebbe una soluzione piuttosto semplice: associare le coordinate a ogni funzione e all'atto della chiamata mettere nell'env un elemento che dica qual'è la funzione in corso. Peraltro questa cosa c'è già, ho dovuto farla per implementare la *recur*. Al momento sia le chiamate di funzioni che i *loop* mettono nell'env un elemento **__recur_target__**, basterebbe aggiungere a questo le coordinate della funzione e, nella gestione dell'eccezione potrei ricostruire lo stack trace percorrendo all'indietro la lista degli env.

Sarebbe interessante aggiungere dove, in una funzione, la successiva viene chiamata. In effetti questa informazione ce l'ho già: le chiamate a funzione sono liste e queste hanno già, nella maggior parte dei casi, le coordinate associate. Restano fuori le chiamate prodotte dalle macro o similari. Potrei accontentarmi. 

Quindi, in soldoni, aggiungo alle funzioni, in un attributo **__coords__** le coordinate della definizione della funzione e nel __recur_target__ le coordinate della chiamata.
Proviamo.
Ok, c'era un grosso problema di fondo in questo ragionamento: l'env disponibile durante la **catch** è quello del momento della definizione della **try**, non quello dell'esecuzione della funzione.
Un modo di ovviare sarebbe di richiudere in un try/catch tutto il body dell'EVAL, o in alternativa il body del while(True), in quest'ultimo caso avremmo un tracciamento molto più fine. Il catch dovrebbe aggiungere l'informazione di codice in esecuzione (ast) e eventuali coordinate allo stack trace e continuare la gestione dell'eccezione con una raise. Se non si verificano eccezioni l'overhead dovrebbe essere minimo.
Provo a metterlo dentro a while(True).

Sembra funzioni!
Ora facendo load-file di questo file (sto usando destruct.mal come file temporaneo per prove):
```



(defn bad-code []
  (println "I'm going to do a bad thing")
  (println "really")
  (println "really bad")
  (/ 5 0)
  (println "Ok, I did it")
  )

(def a '(1 2 3 4 5))
(def sss 'foo)
(def aaa 33)
(bad-code)
(def b [5 6 7 8])```

ottengo:
```
I'm going to do a bad thing
really
really bad
Exception: division by zero
   executing: (eval (read-string (str (do  content 
nil))))
   lisp traceback: 
   - (/ 5 0) - ['destruct.mal', (7, 22)]
   - (do (println "I'm going to do a bad thing") (println "really") (println "really bad") (/ 5 0) (println "Ok, I did it")) - nil
   - (do (defn bad-code [] (println "I'm going to do a bad thing") (println "really") (println "really bad") (/ 5 0) (println "Ok, I did it")) (def a (quote (1 2 3 4 5))) (def sss (quote foo)) (def aaa 33) (bad-code) (def b [5 6 7 8]) nil) - ['destruct.mal', (18, 4)]
   - (eval (read-string (str "(do " content "\nnil)"))) - ['__BOOT__', (7, 2)]
```

Le coordinate nei file sono imprecise, bisogna lavorarci ancora un po' ma non è male.
Vorrei poi fare una profilazione con e senza per vedere che impatto ha sulle performance, ma non mi aspetto grosse sorprese.
Forse il problema più grosso è  uesta linea:
```(do (println "I'm going to do a bad thing") (println "really") (println "really bad") (/ 5 0) (println "Ok, I did it")) - nil```
Quella *do* non esiste nel sorgente: è l'espansione della macro *defn* ed + senza coordinate, sarebbe bello riuscire a riportare il nome della funzione e la sua posizione.

Creo un file open_issues.md e ci metto le cose che restano da fare. Chiudo questo capitolo, per ora. Si può essere già soddisfatti.

