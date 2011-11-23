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

import csv
try:
    import MySQLdb
    import datetime # only used with MySQL
    import re # only used with MySQL
except ImportError:
    pass


class MyCSV(csv.Dialect):
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_ALL


class Table(object):
    def __init__(self, headers=[], dash='-', pipe='|', plus='+',
                 input_encoding='utf8', output_encoding='utf8', from_csv=None,
                 from_mysql=None):
        self.headers = headers
        self.dash = dash
        self.pipe = pipe
        self.plus = plus
        self.input_encoding = input_encoding
        self.output_encoding = output_encoding
        self.csv_filename = None
        self.rows = []
        self.types = {}
        if from_csv:
            self._import_from_csv(from_csv)
        elif from_mysql:
            self._get_mysql_config(from_mysql)
            self._import_from_mysql()

    def _convert_to_unicode(self, element):
        if isinstance(element, (str, unicode)):
            return element.decode(self.input_encoding)
        else:
            return unicode(element)

    def _organize_data(self):
        result = []
        result.append([self._convert_to_unicode(x) for x in self.headers])
        for row in self.rows:
            if isinstance(row, dict):
                row_data = []
                for header_name in self.headers:
                    if header_name not in row:
                        row[header_name] = ''
                    row_data.append(self._convert_to_unicode(row[header_name]))
            else:
                row_data = [self._convert_to_unicode(info) for info in row]
            result.append(row_data)
        self.data = result

    def _define_maximum_column_sizes(self):
        self.max_size = {}
        for column in zip(*self.data):
            self.max_size[column[0]] = max([len(x) for x in column])

    def _make_line_from_row_data(self, row_data):
        return '%s %s %s' % (self.pipe, (' %s ' % self.pipe).join(row_data),
                             self.pipe)

    def __unicode__(self):
        self._organize_data()
        if len(self.data) == 1 and not self.data[0]:
            return unicode()
        self._define_maximum_column_sizes()
        unicode_headers, rows = self.data[0], self.data[1:]

        dashes = [self.dash * (self.max_size[x] + 2) for x in unicode_headers]
        centered_headers = [x.center(self.max_size[x]) for x in unicode_headers]
        split_line = self.plus + self.plus.join(dashes) + self.plus
        header_line = self._make_line_from_row_data(centered_headers)

        result = [split_line, header_line, split_line]
        for row in rows:
            row_data = []
            for i, info in enumerate(row):
                data = info.rjust(self.max_size[unicode_headers[i]])
                row_data.append(data)
            result.append(self._make_line_from_row_data(row_data))
        if self.rows:
            result.append(split_line)
        return '\n'.join(result)

    def __str__(self):
        return self.__unicode__().encode(self.output_encoding)

    def _import_from_csv(self, file_name_or_pointer):
        if isinstance(file_name_or_pointer, (str, unicode)):
            self.csv_filename = file_name_or_pointer
            fp = open(file_name_or_pointer, 'r')
        else:
            fp = file_name_or_pointer
        self.fp = fp
        reader = csv.reader(fp)
        data = list(reader)  # reader is an iterator
        if self.csv_filename:
            fp.close()
        self.headers = []
        self.rows = []
        if data:
            headers = data[0]
            self.headers, self.rows = data[0], data[1:]

    def _get_mysql_config(self, connection_str):
        colon_index = connection_str.index(':')
        at_index = connection_str.index('@')
        slash_index = connection_str.index('/')
        second_slash_index = connection_str.index('/', slash_index + 1)
        self.mysql_username = connection_str[:colon_index]
        self.mysql_password = connection_str[colon_index + 1:at_index]
        self.mysql_hostname = connection_str[at_index + 1:slash_index]
        self.mysql_port = 3306
        if ':' in self.mysql_hostname:
            data = self.mysql_hostname.split(':')
            self.mysql_hostname = data[0]
            self.mysql_port = int(data[1])
        self.mysql_database = connection_str[slash_index + 1:second_slash_index]
        self.mysql_table = connection_str[second_slash_index + 1:]

    def _connect_to_mysql(self):
        self.mysql_connection = MySQLdb.connect(user=self.mysql_username,
                passwd=self.mysql_password, host=self.mysql_hostname,
                port=self.mysql_port, db=self.mysql_database)
        self.cursor = self.mysql_connection.cursor()

    def _identify_type_of_data(self):
        columns = zip(*self.rows)
        date_regex = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
        datetime_regex = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2} '
                                    '[0-9]{2}:[0-9]{2}:[0-9]{2}$')
        for i, column in enumerate(columns):
            column_types = [int, float, datetime.date, datetime.datetime, str]
            cant_be = set()
            for value in column:
                try:
                    converted = int(value)
                    if str(converted) != str(value):
                        raise ValueError('It is float')
                except ValueError:
                    cant_be.add(int)
                try:
                    converted = float(value)
                except ValueError:
                    cant_be.add(float)
                if datetime_regex.match(str(value)) is None:
                    cant_be.add(datetime.datetime)
                if date_regex.match(str(value)) is None:
                    cant_be.add(datetime.date)
            for removed_type in cant_be:
                column_types.remove(removed_type)
            self.types[self.headers[i]] = column_types[0]

    def _import_from_mysql(self):
        self._connect_to_mysql()
        self.cursor.execute('SELECT * FROM ' + self.mysql_table)
        self.headers = [x[0] for x in self.cursor.description]
        self.rows = [row for row in self.cursor.fetchall()]
        self.mysql_connection.close()

    def to_mysql(self, connection_string):
        self._get_mysql_config(connection_string)
        self._connect_to_mysql()
        if self.headers:
            columns_and_types = ['%s TEXT' % header for header in self.headers]
            sql = 'CREATE TABLE IF NOT EXISTS %s (%s)' % \
                  (self.mysql_table, ', '.join(columns_and_types))
            self.mysql_connection.query(sql)
        for row in self.rows:
            values_with_quotes = ', '.join(['"%s"' % value for value in row])
            sql = 'INSERT INTO %s VALUES (%s)' % (self.mysql_table,
                                                  values_with_quotes)
            self.mysql_connection.query(sql)
        self.mysql_connection.close()

    def to_csv(self, filename):
        self._organize_data()
        encoded_data = [[info.encode(self.output_encoding) for info in row] \
                        for row in self.data]
        fp = open(filename, 'w')
        writer = csv.writer(fp, dialect=MyCSV)
        writer.writerows(encoded_data)
        fp.close()

    def to_text_file(self, filename):
        self._organize_data()
        fp = open(filename, 'w')
        fp.write(self.__str__())
        fp.close()
