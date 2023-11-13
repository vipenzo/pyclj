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
