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

(deftest  test-get-paths
  (is (=  (get-r-paths-sequential  '[a b c]  'pippo 3)  '[[__as_3 pippo] [a (nth __as_3 0)] [b (nth __as_3 1)] [c (nth __as_3 2)]]))
  (is (=  (get-r-paths-associative  '{x :x y :y}  'pippo 3)  '[[__as_3 pippo] [x (get __as_3 :x)] [y (get __as_3 :y)]]))
  (is (=  (get-r-paths  'x  'pippo 5)  '[[x pippo]]))
  (is (=  (get-r-paths  '[a {b :x}]  'foo 0)  '[[__as_1 foo] [a (nth __as_1 0)] [__as_3 (nth __as_1 1)] [b (get __as_3 :x)]]))
  (is (=  (get-r-paths  '[a {[b c] :x}]  'foo 0)  '[[__as_1 foo] [a (nth __as_1 0)] [__as_3 (nth __as_1 1)] [__as_5 (get __as_3 :x)] [b (nth __as_5 0)] [c (nth __as_5 1)]]))
  (is (=  (get-r-paths  '{[a {[b c] :x}] :z e :e}  'foo 0)  '[[__as_1 foo] [__as_3 (get __as_1 :z)] [a (nth __as_3 0)] [__as_5 (nth __as_3 1)] [__as_7 (get __as_5 :x)] [b (nth __as_7 0)] [c (nth __as_7 1)] [e (get __as_1 :e)]]))
  (is (=  (get-r-paths  '[a b & c]  'foo 0)  '[[__as_1 foo] [a (nth __as_1 0)] [b (nth __as_1 1)] [c (drop 2 __as_1)]]))
  (is (=  (get-r-paths  '{x :x y :y :or {:y 33}}  'foo 0)  '[[__as_1 foo] [x (get __as_1 :x)] [y (get __as_1 :y 33)]]))
  (is (=  (get-r-paths  '{:keys [x y z]}  'foo 0)  '[[__as_1 foo] [x (get __as_1 :x)] [y (get __as_1 :y)] [z (get __as_1 :z)]]))
  (is (=  (get-r-paths  '[a {x :x [y z] :yz :or {:yz [9 8]}}]  'foo 0)  '[[__as_1 foo] [a (nth __as_1 0)] [__as_3 (nth __as_1 1)] [x (get __as_3 :x)] [__as_5 (get __as_3 :yz [9 8])] [y (nth __as_5 0)] [z (nth __as_5 1)]])))

(deftest tests-let
  (is (= 7 (let [x 3 y 4] (+ x y))))
  (is (= 7 (let [[x y] [3 4]] (+ x y))))
  (is (= 7 (let [{x :x [y z] :yz} {:x 3 :yz [4 5]}] (+ x y))))
  (is (= 91 (let [{x :x [y z] :yz :or {:yz [88 89]}} {:x 3}] (+ x y))))
  (is (= 92 (let [{x :x [y z] :yz :or {:yz [88 89] :x 4}} {}] (+ x y))))
  (is (= 9 (let [{:keys [x y]} {:x 7 :y 2}] (+ x y))))
  (is (= 9 (let [{:keys [x y] :or {:x 7 :y 2}} {}] (+ x y))))
  (is (= 4 (let [[a & v] [1 2 3]] (- (apply + v) a))))
  (is (= [3 32 44 {:a 32 :b 44} 5 6 {:o1 5 :o2 6}]
         (let [[x {a :a b :b :as y} & {:keys [o1 o2] :as v}]
               [3 {:a 32 :b 44} :o1 5 :o2 6]]
           [x a b y o1 o2 v]))))

(deftest  test-fn
    (is (=  ((fn ([x y] (+ x y)) ([[x y]] (recur x y))) [3 4])  '7 ))
    (is (=  ((fn ([& v] (apply + v)) ([[x y]] (recur x y))) [3 4])  '7 ))
    (is (=  ((fn ([& v] (apply + v)) ([[x y]] (recur x y))) [3 4 5])  '7 )))

(deftest  test-destruct
    (is (=  (destruct  '[] [])  '[[__as_1 []]] ))
    (is (=  (destruct  '[a b c] [1 2 3])  '[[__as_1 [1 2 3]] [a (nth __as_1 0)] [b (nth __as_1 1)] [c (nth __as_1 2)]] ))
    (is (=  (destruct  '[a b c & cs] (range 10))  '[[__as_1 (0 1 2 3 4 5 6 7 8 9)] [a (nth __as_1 0)] [b (nth __as_1 1)] [c (nth __as_1 2)] [cs (drop 3 __as_1)]] ))
    (is (=  (destruct  '{a :a b :b c :c} {:a 1 :b 2 :c 3})  '[[__as_1 {:a 1 :b 2 :c 3}] [a (get __as_1 :a)] [b (get __as_1 :b)] [c (get __as_1 :c)]] ))
    (is (=  (destruct  '{a :a b :b [x y & zs] :c} {:a 1 :b 2 :c (range 10)})  '[[__as_1 {:a 1 :b 2 :c (0 1 2 3 4 5 6 7 8 9)}] [a (get __as_1 :a)] [b (get __as_1 :b)] [__as_3 (get __as_1 :c)] [x (nth __as_3 0)] [y (nth __as_3 1)] [zs (drop 2 __as_3)]] ))
    (is (=  (destruct  '{a :a b :b [x y & zs] :c d :d :or {:d 1000}} {:a 1 :b 2 :c (range 10)})  '[[__as_1 {:a 1 :b 2 :c (0 1 2 3 4 5 6 7 8 9)}] [a (get __as_1 :a)] [b (get __as_1 :b)] [__as_3 (get __as_1 :c)] [x (nth __as_3 0)] [y (nth __as_3 1)] [zs (drop 2 __as_3)] [d (get __as_1 :d 1000)]] ))
    (is (=  (destruct  '{a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}} {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}})  '[[__as_1 {:a 1 :b 2 :c (0 1 2 3 4 5 6 7 8 9) :e {:g 100 :h 200}}] [a (get __as_1 :a)] [b (get __as_1 :b)] [__as_3 (get __as_1 :c)] [x (nth __as_3 0)] [y (nth __as_3 1)] [zs (drop 2 __as_3)] [d (get __as_1 :d 1000)] [__as_3 (get __as_1 :e)] [g (get __as_3 :g)] [h (get __as_3 :h)]] )))

(deftest  test-let-2
    (is (=  (let [[] []] 'nada)  'nada ))
    (is (=  (let [[a b c] [1 2 3]] [a b c])  '[1 2 3] ))
    (is (=  (let [[a b c & cs] (range 10)] [a b c cs])  '[0 1 2 (3 4 5 6 7 8 9)] ))
    (is (=  (let [{a :a b :b c :c} {:a 1 :b 2 :c 3}] [a b c])  '[1 2 3] ))
    (is (=  (let [{a :a b :b [x y & zs] :c} {:a 1 :b 2 :c (range 10)}] [a b x y zs])  '[1 2 0 1 (2 3 4 5 6 7 8 9)] ))
    (is (=  (let [{a :a b :b [x y & zs] :c d :d :or {:d 1000}} {:a 1 :b 2 :c (range 10)}] [a b x y zs d])  '[1 2 0 1 (2 3 4 5 6 7 8 9) 1000] ))
    (is (=  (let [{a :a b :b [x y & zs] :c d :d {:keys [g h]} :e :or {:d 1000}} {:a 1 :b 2 :c (range 10) :e {:g 100 :h 200}}] [a b x y zs d g h])  '[1 2 0 1 (2 3 4 5 6 7 8 9) 1000 100 200] )))

(deftest  test-let-strange
  (defn uh-oh [list-of-things] (let [[a b c & cs] list-of-things] [a b c cs]))
  (def list-of-things (range 10 20))
  (is (=  (let [[a b c & cs] list-of-things] [a b c cs])  '[10 11 12 (13 14 15 16 17 18 19)]))
  (is (=  (let [list-of-things (range 10)] (let [[a b c & cs] list-of-things] [a b c cs]))  '[0 1 2 (3 4 5 6 7 8 9)]))
  (is (=  (uh-oh (range 10))  '[0 1 2 (3 4 5 6 7 8 9)]))
  (is (=  (let [list-of-things (range 10)] list-of-things)  '(0 1 2 3 4 5 6 7 8 9))))

(deftest  test-trailing-maps
    (defn configure [val & {:keys [debug verbose] :or {:debug false :verbose false} :as options}] [val debug verbose])
    (is (=  (configure 12 {:debug true})  [12 true false]))
    (is (=  (configure 12 :debug true)  [12 true false] ))
    (defn ma-configure 
      ([val & {:keys [debug verbose] :or {:debug false :verbose false} :as options}] 
       [val debug verbose]) 
      ([] 
       (ma-configure 17 :verbose true)))
    (is (=  (ma-configure)  [17 false true] ))
    (is (=  (ma-configure 21)  [21 false false] ))
    (is (=  (ma-configure 21 :debug true)  [21 true false] ))
    (is (=  (ma-configure 21 {:verbose true})  [21 false true] )))

(deftest  test-merge
    (is (=  (merge {:a 1 :b 2 :c 3} {:b 10 :d 20} {:a 11 :x 87})  '{:a 11 :b 10 :c 3 :d 20 :x 87} )))

(deftest  test-compact-key-val-trailing-pairs
    (is (=  (compact-key-val-trailing-pairs  '[])  '{} ))
    (is (=  (compact-key-val-trailing-pairs  '[:a 1])  '{:a 1} ))
    (is (=  (compact-key-val-trailing-pairs  '[23 :a 1])  '{:a 1} ))
    (is (=  (compact-key-val-trailing-pairs  '[23 {:A 3 :B 27} 41 {:b 33 :c 44} :a 1])  '{:b 33 :c 44 :a 1} )))


