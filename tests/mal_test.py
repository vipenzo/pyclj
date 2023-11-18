import unittest
from mal.boot import BOOT
RE, REP, REPL = BOOT()

class TestMal(unittest.TestCase):

    def test_REP(self):
        self.assertEqual(REP("(+ 4 7)"), '11')  
        

if __name__ == '__main__':
    unittest.main()