# Tests
Ok, Ora che l'implementazione di **pyclj** è sufficientemente completa (almeno è al punto in cui penso sia sufficiente per **turtlemal**, dovroò aggiungere una serie di funzioni di utilizzo comune, ma per il resto mi fermo qui), è ora di pensare ai test per renderla un po' più robusta.
Quello che vorrei fare è:
- dotarla di un test framework interno (c'è già in embrione, ma va migliorato) in modo da poter importare test esistenti per clojure
- integrarla con la piattaforma di test python supportata da VS Code, in modo da poter eseguire i test e valutare il risultato don VS Code.

## Stato Corrente
Vediamo dove siamo. Ora in `tests` ho un file `destructuring_tests.clj` che posso eseguire così:
```
pyclj > (load-file "./tests/destructuring_tests.clj")
./tests/destructuring_tests.clj
pyclj > (run-test test-destructuring)
-  {:type :pass :message nil :expected (= [2 1] (let [[a b] [1 2]] [b a])) :actual true}
-  {:type :pass :message nil :expected (= (set 1 2) (let [[a b] [1 2]] (set a b))) :actual true}
-  {:type :pass :message nil :expected (= [1 2] (let [{a :a b :b} {:a 1 :b 2}] [a b])) :actual true}
-  {:type :pass :message nil :expected (= [1 2] (let [{:keys [a b]} {:a 1 :b 2}] [a b])) :actual true}
-  {:type :pass :message nil :expected (= [1 2 [1 2]] (let [[a b :as v] [1 2]] [a b v])) :actual true}
-  {:type :pass :message nil :expected (= [1 42] (let [{:keys [a b] :or {:b 42}} {:a 1}] [a b])) :actual true}
-  {:type :pass :message nil :expected (= [1 nil] (let [{:keys [a b] :or {:c 42}} {:a 1}] [a b])) :actual true}
-  {:type :pass :message nil :expected (= [2 1] (let [[a b] (quote (1 2))] [b a])) :actual true}
-  {:type :pass :message nil :expected (= {1 2} (let [[a b] [1 2]] {a b})) :actual true}
-  {:type :pass :message nil :expected (= [2 1] (let [[a b] (seq [1 2])] [b a])) :actual true}
-  {:type :pass :message nil :expected (= 1 a) :actual true}
-  {:type :pass :message nil :expected (= 2 b) :actual true}
nil
```

Il contenuto del file è questo:
```
(deftest test-destructuring
  (is (= [2 1] (let [[a b] [1 2]] [b a])))
  (is (= #{1 2} (let [[a b] [1 2]] #{a b})))
  (is (= [1 2] (let [{a :a b :b} {:a 1 :b 2}] [a b])))
  (is (= [1 2] (let [{:keys [a b]} {:a 1 :b 2}] [a b])))
  (is (= [1 2 [1 2]] (let [[a b :as v] [1 2]] [a b v])))
  (is (= [1 42] (let [{:keys [a b] :or {:b 42}} {:a 1}] [a b])))
  (is (= [1 nil] (let [{:keys [a b] :or {:c 42}} {:a 1}] [a b])))
  (is (= [2 1] (let [[a b] '(1 2)] [b a])))
  (is (= {1 2} (let [[a b] [1 2]] {a b})))
  (is (= [2 1] (let [[a b] (seq [1 2])] [b a])))
  (let [{:keys [a b]} {:a 1 :b 2}]
    (is (= 1 a))
    (is (= 2 b))))
```

Qualche considerazione:
1. I test sono presi da clojurescript, ma non ho potuto importarli direttamente perchè:
    - mancano i namespace
    - manca "testing" e probabilmente altro, non ricordo
    - La mia implementazione della destructure è leggermente diversa, per cui alcuni fallivano.
    Dovrei trovare un modo per importare i file originali, flaggare quali è previsto che non passino
1. Il test viene lanciato a mano dalla REPL, vorrei lanciarlo da VS Code e vedere i risultati lì.
1. In caso di fail del test dovremo vedere come gestire le informazioni. In caso di pass bisogna che questo diventi un **pass** anche per python/VS Code.

Partiamo dal secondo punto.
Scritto il programmino `refresh_clj_tests.py` che prende tutti i file che finiscono per "_tests.clj" nella directory "./tests" e crea il file `autogenerated_test.clj`.
Questo file, al momento è fatto così:
```
###########################################################
### Do not edit: generated by tests/refresh_clj_tests.py ##
###########################################################

import unittest
from mal.boot import BOOT
REP, REPL = BOOT()


class reader_tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        REP('(load-file "./tests/reader_tests.clj")')

    @classmethod
    def tearDownClass(cls):
        print("End.")

    
    def test_read_integer(self):
        self.assertEqual(REP("(run-test read-integer)"), 143)  


    def test_read_floating(self):
        self.assertEqual(REP("(run-test read-floating)"), 143)  


    def test_read_ratio(self):
        self.assertEqual(REP("(run-test read-ratio)"), 143)  


    def test_read_symbol(self):
        self.assertEqual(REP("(run-test read-symbol)"), 143)  


    def test_read_specials(self):
        self.assertEqual(REP("(run-test read-specials)"), 143)  


    def test_read_char(self):
        self.assertEqual(REP("(run-test read-char)"), 143)  



class destructuring_tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        REP('(load-file "./tests/destructuring_tests.clj")')

    @classmethod
    def tearDownClass(cls):
        print("End.")

    
    def test_test_destructuring(self):
        self.assertEqual(REP("(run-test test-destructuring)"), 143)  
```

Contiene quindi una classe per ogni file e un test per ogni "(deftest)". Il riconoscimento è molto rozzo fatto in questo modo, uno dei primi limiti che mi vengono in mente è che la parte clojure deve andare a capo dopo "(deftest testname". Un modo, forse migliore, sarebbe di caricare i test con una REP("(load-file ...))" e poi ricavare la lista dei test deferenziando l'atom `deftests`. Ma intanto provo così.
Il file viene riconosciuto correttamente da VS Code e mi ritrovo la lista dei test nel pannello test e li posso eseguire tutti o uno alla volta.
Ovviemente falliscono tutti, perchè confronta il risultato con 143.

Ora, per prima cosa vorrei che quanto prodotto dalla `do-report` arrivasse direttamente a python senza tradurlo in stringa. Questo è impossibile con la `REP`, che per definizione fa "READ, EVALUATE, PRINT", mi serve una `RE` che faccia solo le prime due, in modo che python riceva direttamente il dato. Provo a crearla in boot.py.
Fatto, ora la integro nei test.

Bene, messo su il tutto e sembra andare. È molto comodo per i test che passano, meno per quelli che falliscono, perchè il framework python non riesce a dare indicazioni sul fail avvenuto in clojure. Probabilmente la `is` andrebbe implementata meglio.
E manca comunque il `testing`, che non saprei bene dove inserire.
Lo tengo così, per il momento. Aggiungo un po' di test adattandoli a mano e poi vediamo.

Ho implementato queste macro:
```
(defmacro debug-eval [& vals]
  `(let* [f (fn [x]
              (println "code: " (str x) "\n    --> " (eval x)))]
         (map f  '~vals)))

(defmacro strquote [x] (if (and (list? x) (= 'quote (first x))) (apply str " '" (rest x)) (str x)))

(defmacro debug-eval-to-test [testname & vals]
  (do
    (println "(deftest " testname )
    (let [f (fn [x]
              (let [y (eval x)
                    x (if (list? x) (map strquote x) x)]
                (println "    (is (= "  x (str " '" y) "))")))]
      (map f  vals)
      (println ")"))))
```
Sono abbastanza comode: uso `debug-eval` per provare le nuove cose e quando il risultato è soddisfacente le congelo in tests con `debug-eval-to-test`, è un modo per creare test di non regressione. Nei casi più lineari funziona. in alcuni bisogna intervenire manualmente.
