import unittest

import gedcom_path

class IndividualDoubles(unittest.TestCase):

    def test_is_int(self):
        y = gedcom_path.LineParser()
        t = "0 HEAD"
        s = t.split()
        assert(y.is_int(s[0]))

    def test_parse_date(self):
        y = gedcom_path.DateParser()
        print(y.parse("1989"))
        print(y.parse("ABT 1989"))
        
if __name__ == '__main__':
    unittest.main()
