; see 'design_notes_it_4.md' in design-notes

(def start (assoc (vec (map (fn [x] 0) (range 25))) 0 1))

(defn sinistra [n]
  (if (and (> n 0) (= (quot n 5) (quot (dec n) 5))) (dec n) nil))

(defn destra [n]
  (if (= (quot n 5) (quot (inc n) 5)) (inc n) nil))

(defn su [n]
  (if (> (- n 5) 0) (- n 5) nil))

(defn giù [n]
  (if (< (+ n 5) 25) (+ n 5) nil))

(defn not-nil? [x] (not (nil? x)))

(defn calc-moves [tavola path n]
  (let [pos (first path)
        moves [(su pos) (giù pos) (destra pos) (sinistra pos)]
        possibili (filter not-nil? moves)
        non-occupati (filter (fn [v] (= 0 (nth tavola v))) possibili)]
    (if (empty? non-occupati)
      nil
      (vec (map (fn [new-pos] 
                  {:tavola (assoc tavola new-pos n) :path (cons new-pos path)}
                  ) non-occupati)))))


(defn gioca [n stato]
  (let [step (loop [res (set [])
                    ramo (first stato)
                    altri (rest stato)]
               (if (nil? ramo)
                 (vec res)
                 (recur (reduce (fn [acc x] (if (nil? x) acc (conj acc x))) 
                                res 
                                (calc-moves (get ramo :tavola) (get ramo :path) n)) (first altri) (rest altri))))]
    (println "*** n=" n " step dimension=" (count step))
    (if (< n 25)
      (gioca (inc n) step)
      step)))



(defn good-sol [sol pos] (= 25 (nth (get sol :tavola) pos)))

(defn rc [n] (str "(riga " (inc (quot n 5)) " colonna " (inc (mod n 5)) ")"))

(defn print-table [sol] (let [t  (partition 5 (get sol :tavola))] (dotimes [n 5] (println (nth t n)))))

(defn cn [n soluzioni] (count (filter #(good-sol % n) soluzioni)))

(let [soluzioni (time (gioca 3 (calc-moves start [0] 2)))]
  (println "Soluzione = " (some #(good-sol % 3) soluzioni))
  (dotimes [n 25] (println "per uscita a " (rc n) " ci sono " (cn n soluzioni) " soluzioni"))
  )
