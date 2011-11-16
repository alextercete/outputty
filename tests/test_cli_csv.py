#!/usr/bin/env python
# coding: utf-8

# Copyright 2011 Álvaro Justen
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import os
import tempfile
from textwrap import dedent
from utils import execute, sh, OUTPUTTY_EXECUTABLE


class TestOutputtyCli(unittest.TestCase):
    def test_outputty_with_table_should_receive_data_from_stdin(self):
        output = execute('--table', 'a\n')
        self.assertEquals(output, dedent('''
        +---+
        | a |
        +---+
        ''').strip() + '\n')

    def test_outputty_should_pretty_print_table_from_csv_data_in_stdin(self):
        output = execute('--table', 'a,b\n1,2\n')
        self.assertEquals(output, dedent('''
        +---+---+
        | a | b |
        +---+---+
        | 1 | 2 |
        +---+---+
        ''').strip() + '\n')

    def test_receive_csv_data_in_stdin_and_save_in_a_csv_file(self):
        temp_fp = tempfile.NamedTemporaryFile(delete=False)
        temp_fp.close()
        output = execute('--table --to-csv ' + temp_fp.name, 'a,b\n1,2\n')
        temp_fp = open(temp_fp.name)
        csv_contents = temp_fp.read()
        os.remove(temp_fp.name)
        self.assertEquals(csv_contents, dedent('''
        "a","b"
        "1","2"
        ''').strip() + '\n')

    def using_to_csv_parameter_without_filename_should_print_to_stdout(self):
        output = execute('--table --to-csv', 'a,b\n1,2\n')
        self.assertEquals(output, dedent('''
        "a","b"
        "1","2"
        ''').strip() + '\n')

    def test_from_csv_without_filename_should_ignore_this_option(self):
        output = execute('--table --from-csv', 'a,b\n1,2\n')
        self.assertEquals(output, dedent('''
        +---+---+
        | a | b |
        +---+---+
        | 1 | 2 |
        +---+---+
        ''').strip() + '\n')

    def test_from_csv_with_filename_should_print_correctly_data(self):
        temp_fp = tempfile.NamedTemporaryFile(delete=False)
        temp_fp.write("spam,eggs\nham,spam\neggs,ham")
        temp_fp.close()
        output = execute('--table --from-csv ' + temp_fp.name)
        self.assertEquals(output, dedent('''
        +------+------+
        | spam | eggs |
        +------+------+
        |  ham | spam |
        | eggs |  ham |
        +------+------+
        ''').strip() + '\n')

    def test_from_csv_with_wrong_filename_returns_1_and_stderr_not_empty(self):
        process = sh(OUTPUTTY_EXECUTABLE  + ' --table --from-csv doesnt-exist')
        self.assertEquals(process.returncode, 1)

        expected_error = "[Errno 2] No such file or directory: 'doesnt-exist'\n"
        self.assertEquals(process.err, expected_error)
        
    def test_from_csv_without_permissions_returns_1_and_stderr_not_empty(self):
        process = sh(OUTPUTTY_EXECUTABLE  + ' --table --from-csv /root/test',
                     finalize=False)
        process.stdin.write('a,b\n1,2')
        process.stdin.close()
        process.wait()

        self.assertEquals(process.returncode, 1)
        expected_error = "[Errno 13] Permission denied: '/root/test'\n"
        self.assertEquals(process.stderr.read(), expected_error)
        
    def test_to_csv_without_permissions_returns_2_and_stderr_not_empty(self):
        process = sh(OUTPUTTY_EXECUTABLE  + ' --table --to-csv /root/test',
                     finalize=False)
        process.stdin.write('a,b\n1,2')
        process.stdin.close()
        process.wait()

        self.assertEquals(process.returncode, 2)
        expected_error = "[Errno 13] Permission denied: '/root/test'\n"
        self.assertEquals(process.stderr.read(), expected_error)
