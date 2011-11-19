#!/usr/bin/env python
# coding: utf-8
"""
Tests for histogram module
"""
import unittest
from histogram import Histogram
from numpy.random import seed
from numpy.random import normal
from textwrap import dedent


class TestTableTxt(unittest.TestCase):
    def test_horizontal_histogram(self):
        seed(1234) # Setting the seed to get repeatable results
        d = normal(size=1000)
        h = Histogram(d, bins=10)
        expected = dedent('''
        265      |
                 ||
                |||
                ||||
               ||||||
        -3.56          2.76
        ''').strip()
        self.assertEquals(h.horizontal(5), expected)

    def test_vertical_histogram(self):
        seed(1234) # Setting the seed to get repeatable results
        d = normal(size=1000)
        h = Histogram(d, bins=10)
        expected = dedent('''\
                              265

        -3.56:
        -2.93:
        -2.30: ||
        -1.67: ||||
        -1.03: ||||||||||
        -0.40: |||||||||||||||
        0.23 : ||||||||||||
        0.87 : ||||||
        1.50 : |||
        2.13 :''')
        self.assertEquals(h.vertical(15), expected)
