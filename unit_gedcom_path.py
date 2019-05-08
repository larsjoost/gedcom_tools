import unittest

import gedcom_path

class IndividualDoubles(unittest.TestCase):

    def test_get_doubles(self):
        y = gedcom_path.IndividualDoubles()
        x = ["Lone", "Peder", "Anne", "Lars", "Pande", "Niels", "Leif", "Lars J"]
        assert({'Anne': ['Pande'], 'Lars': ['Lars J']} == y.get_doubles(x, 3))
        
if __name__ == '__main__':
    unittest.main()
