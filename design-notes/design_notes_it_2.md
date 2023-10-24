# coords
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
