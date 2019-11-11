from unittest import TestCase

from calculator import Calculator

class TestCalculator(TestCase):
    def test_add(self):
        self.calculator = Calculator()
        self.assertEqual(self.calculator.add(3, 4), 7)

    def test_multiply(self):
        self.calculator = Calculator()
        self.assertEqual(self.calculator.multiply(3, 4), 12)
