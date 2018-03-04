import unittest
import log_analyzer

class SimpleTest(unittest.TestCase):

    def test_median(self):
        self.assertEqual(log_analyzer.median([1,2,3]), 2)

    def test_already_parsed(self):
        self.assertEqual(log_analyzer.already_parsed('./tmp'), False,'Повторный запуск парсера')

    def test_line_counter(self):
        self.assertNotEqual(log_analyzer.line_counter('./log'),0)

    # Указан несуществующий путь, возвращает нулевое количество записей в логе
    def test_line_counter_zero(self):
        self.assertEqual(log_analyzer.line_counter('./logs'),0)

    def test_report_generate(self):
        self.assertTrue(log_analyzer.report_generate('./reports',' '))

if __name__ == '__main__':
    unittest.main()