import unittest
import log_analyzer

class SimpleTest(unittest.TestCase):

    def test_median(self):
        self.assertEqual(log_analyzer.median([1,2,3]), 2)

    # Указан несуществующий путь, возвращает None
    def test_parsing(self):
        self.assertEqual(log_analyzer.parsing('./logs',100),None)

    def test_report_generate(self):
        self.assertTrue(log_analyzer.report_generate_new('./reports',' '))

if __name__ == '__main__':
    unittest.main()