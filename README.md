# pyclj
Extension of the 'python' implementation of kanaka/mal to make it more Clojure-like

Extensions:
- Added slurp
- Added fn, let, defn  
- Forced functions parameter list to be a Vector
- Made Vector and Hash_Map hashable (they can now be used as keys in dictionaries)
- Added PI, is_close, abs, sin, cos, tan, asin, acos, atan, sqrt, python_atan2, atan2, to_degrees, to_radians. No math namespace, added to repl env.
- Added default arg to get. (get {:a 3} :b 33) returns 33.
- Added range (not yet (range) without arguments), select-keys, mapcat, interleave, partition
- Added inc, dec, second, while, dotimes, reduce, comment, when, next, destruct (works on basic cases and not yet integrated into let, fn, defn)
- Added map-indexed, loop, recur (works both on loop and functions)



How to use it:
- Execute mal_repl.py to get a repl prompt.
