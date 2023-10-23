(ns reader-tests)

(deftest read-integer
  (is (= 42 (read-string "42")))
  (is (= +42 (read-string "+42")))
  (is (= -42 (read-string "-42")))

  (is (= 0 (read-string "0")))

  (is (= 042 (read-string "042")))
  (is (= +042 (read-string "+042")))
  (is (= -042 (read-string "-042")))

  ;;hex
  (is (= 0x42e (read-string "0x42e")))
  (is (= +0x42e (read-string "+0x42e")))
  (is (= -0x42e (read-string "-0x42e")))

  ;;oct
  ;(is (== 511 (js/parseInt "777" 8) (read-string "0777")))
  ;(is (== -511 (js/parseInt "-777" 8) (read-string "-0777")))
  ;(is (== 1340 (js/parseInt "02474" 8) (read-string "02474")))
  ;(is (== -1340 (js/parseInt "-02474" 8) (read-string "-02474")))
  ;(is (nan? (read-string "09")))

  ;;radix
  ;(is (== 42 (js/parseInt "16" 36) (read-string "36r16")))
  ;(is (== 42 (js/parseInt "101010" 2) (read-string "2r101010")))
  )

(deftest read-floating
  (is (= 42.23 (read-string "42.23")))
  (is (= +42.23 (read-string "+42.23")))
  (is (= -42.23 (read-string "-42.23")))

  (is (= 42.2e3 (read-string "42.2e3")))
  (is (= +42.2e+3 (read-string "+42.2e+3")))
  (is (= -42.2e-3 (read-string "-42.2e-3"))))

(deftest read-ratio
  (is (= 4/2 (read-string "4/2")))
  (is (= 4/2 (read-string "+4/2")))
  (is (= -4/2 (read-string "-4/2"))))

(deftest read-symbol
  (is (= 'foo (read-string "foo")))
  (is (= 'foo/bar (read-string "foo/bar")))
  (is (= '*+!-_? (read-string "*+!-_?")))
  (is (= 'abc:def:ghi (read-string "abc:def:ghi")))
  (is (= 'abc.def/ghi (read-string "abc.def/ghi")))
  (is (= 'abc/def.ghi (read-string "abc/def.ghi")))
  (is (= 'abc:def/ghi:jkl.mno (read-string "abc:def/ghi:jkl.mno")))
  (is (symbol? (read-string "alphabet")))
  (is (= "foo//" (str (read-string "foo//"))))
  (is (nan? (read-string "##NaN")))
  ;(is (= js/Number.POSITIVE_INFINITY (read-string "##Inf")))
  ;(is (= js/Number.NEGATIVE_INFINITY (read-string "##-Inf")))
  )

(deftest read-specials
  (is (= 'nil nil))
  (is (= 'false false))
  (is (= 'true true)))

(deftest read-char
  (is (= \f (read-string "\\f")))
  (is (= \u0194 (read-string "\\u0194")))
  (is (= \o123 (read-string "\\o123")))
  (is (= \newline (read-string "\\newline")))
  (is (= (char 0) (read-string "\\o0")))
  (is (= (char 0) (read-string "\\o000")))
  (is (= (char 0377) (read-string "\\o377")))
  (is (= \A (read-string "\\u0041")))
  (is (= \@ (read-string "\\@")))
  (is (= (char 0xd7ff) (read-string "\\ud7ff")))
  (is (= (char 0xe000) (read-string "\\ue000")))
  (is (= (char 0xffff) (read-string "\\uffff")))
  #_(is (= "�" (read-string "\\ud800"))))