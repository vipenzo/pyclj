(defn min-sec-ms [ms]
  (let [sec (quot ms 1000)
        ms  (mod ms 1000)
        min (quot sec 60)
        sec (mod sec 60)]
    (str min ":" sec "-" ms)))