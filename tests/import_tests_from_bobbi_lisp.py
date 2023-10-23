

import os, json

def slurp_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def make_test(name, exercise, test):
    f"""def test_{name}(self):\n
        REP({exercise})\n\n
        self.assertEqual(REP("(+ 4 7)"), '11')"""
def import_tests():
    test_dir = os.path.dirname(os.path.realpath(__file__))
    exercises_file_path = os.path.join(test_dir, "exercises.json")
    tests_file_path = os.path.join(test_dir, "tests.json")
    print(f"test_file_path={tests_file_path}")
    tests = slurp_json(tests_file_path)
    exercises = slurp_json(exercises_file_path)
    keys = list(exercises.keys())
    
    test = 
    
    n = 1
    print(keys[n])
    print(f"exercises[{n}]={exercises[keys[n]]}")
    print(f"test[{n}]={tests[keys[n]+'_test']}")


def test_REP(self):
        self.assertEqual(REP("(+ 4 7)"), '11')

if __name__ == '__main__':
    import_tests()