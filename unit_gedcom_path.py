import unittest

import gedcom_path

class IndividualDoubles(unittest.TestCase):

    def test_is_int(self):
        y = gedcom_path.LineParser()
        t = "0 HEAD"
        s = t.split()
        assert(y.is_int(s[0]))
        
if __name__ == '__main__':
    unittest.main()
