#
# Manage registers in a hardware design
#
# Copyright (C) 2008  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
Parses the register database, loading the database.
"""

import xml.parsers.expat

from regenerate.db import Register, BitField


text2field = {
    "read-only": BitField.TYPE_READ_ONLY,
    "read-write": BitField.TYPE_READ_WRITE,
    }


class IpXactParser(object):
    """
    Parses the XML file, loading up the register database.
    """

    def __init__(self, dbase):
        self._db = dbase
        self._reg = None
        self._field = None
        self._fld_start = 0
        self._fld_width = 0
        self._token_list = []
        self._in_maps = False
        self._block_offset = 0
        self._block_list = [0]
        self._in_field_reset = False
        self._in_reg_reset = False
        self._reg_reset = (False, 0)

    def import_data(self, input_file):
        """
        Parses the specified input file.
        """
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        with open(input_file) as f:
            parser.ParseFile(f)
        crossreference(self._db)

    def start_element(self, tag, attrs):
        """
        Called every time an XML element begins
        """
        self._token_list = []
        mname = 'start_' + tag.replace(":", "_")
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def end_element(self, tag):
        """
        Called every time an XML element end
        """
        text = ''.join(self._token_list)
        mname = 'end_' + tag.replace(":", "_")
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)

    def characters(self, data):
        """
        Called with segments of the character data. This is not predictable
        in how it is called, so we must collect the information for assembly
        later.
        """
        self._token_list.append(data)

    def start_spirit_register(self, attrs):
        self._reg = Register()

    def end_spirit_register(self, text):
        self._db.add_register(self._reg)
        self._reg = None
        self._reg_reset = (False, 0)

    def end_spirit_addressOffset(self, text):
        if self._reg:
            self._reg.address = int(text, 0) + self._block_offset

    def end_spirit_addressBlock(self, text):
        self._block_offset = self._block_list.pop()

    def end_spirit_baseAddress(self, text):
        self._block_list.append(self._block_offset)
        self._block_offset = self._block_offset + int(text, 0)

    def end_spirit_size(self, text):
        size = int(text, 0)
        if self._reg:
            self._reg.width = size

    def start_spirit_reset(self, attrs):
        if self._field:
            self._in_field_reset = True
        elif self._reg:
            self._in_reg_reset = True

    def end_spirit_reset(self, text):
        self._in_field_reset = False
        self._in_reg_reset = False

    def end_spirit_value(self, text):
        if self._in_field_reset:
            if self._field:
                self._field.reset_value = int(text, 16)
                self._field.reset_type = BitField.RESET_NUMERIC
        elif self._in_reg_reset:
            self._reg_reset = (True, int(text,16))

    def start_spirit_field(self, attrs):
        self._field = BitField()

    def end_spirit_field(self, text):
        if not self._field.field_name.startswith("RESERVED"):
            self._field.start_position = self._fld_start
            self._field.stop_position = self._fld_start + self._fld_width - 1
            self._reg.add_bit_field(self._field)
            if self._reg_reset[0]:
                self._field.reset_value = (self._reg_reset[1] >> self._fld_start) & ((1 << self._field.width) - 1)
                self._field.reset_type = BitField.RESET_NUMERIC

        self._field = None

    def end_spirit_access(self, text):
        if self._field:
            self._field.field_type = text2field.get(text,
                                                    BitField.TYPE_READ_ONLY)

    def end_spirit_name(self, text):
        if self._field:
            self._field.field_name = text.upper()
        elif self._reg:
            self._reg.register_name = text.replace('_', ' ')
            self._reg.token = text.upper()
        elif not self._in_maps and not self._db.descriptive_title:
            self._db.descriptive_title = text.strip()

    def end_spirit_description(self, text):
        if self._field:
            self._field.description = text.strip()
        elif self._reg:
            self._reg.description = text.strip()

    def end_spirit_bitOffset(self, text):
        self._fld_start = int(text, 0)

    def end_spirit_bitWidth(self, text):
        self._fld_width = int(text, 0)

    def start_spirit_memoryMaps(self, attrs):
        self._in_maps = True

    def end_spirit_memoryMaps(self, text):
        self._in_maps = False


import re


def crossreference(db):
    names = sorted([reg.register_name
                    for reg in db.get_all_registers()],
                   key=len, reverse=True)

    re_list = [r'([^`])({0}) ((R|r)egister)'.format(name) for name in names]

    for reg in db.get_all_registers():
        for regex in re_list:
            reg.description = re.sub(regex, r'\1`\2`_ \3', reg.description)
        for field in reg.get_bit_fields():
            for regex in re_list:
                field.description = re.sub(regex, r'\1`\2`_ \3',
                                           field.description)
