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
DefsWriter - Writes out Verilog defines representing the register addresses
"""

from writer_base import WriterBase     # IGNORE:W0403

HEADER = [
    "`ifdef $M$_DEFS\n",
    "`else\n",
    "`define $M$_DEFS 1\n",
    "\n",
    ]

TRAILER = [
    ""
    "`endif"
    ""
    ]


class VerilogDefines(WriterBase):
    """
    Writes out Verilog defines representing the register addresses
    """

    def __init__(self, dbase):
        WriterBase.__init__(self, dbase)
        self._ofile = None

    def write_def(self, reg, prefix, offset):
        """
        Writes the definition in the format of:

        `define register (address)
        """
        address = reg.address
        name = reg.token
        if not name:
            name = "ADDR%04x" % address
        name = "%s%s" % (prefix, name)

        self._ofile.write("`define %-30s (32'h%x)\n" %
                          (name, (address + offset)))

    def write(self, filename):
        """
        Writes the output file
        """
        try:
            self._ofile = open(filename, "w")
        except IOError as msg:
            import gtk
            errd = gtk.MessageDialog(type=gtk.MESSAGE_ERROR)
            errd.set_markup("Could not create %s" % filename)
            errd.format_secondary_text(str(msg))
            errd.run()
            return
        except:
            import gtk
            errd = gtk.MessageDialog(type=gtk.MESSAGE_ERROR)
            errd.set_markup("Could not create %s" % filename)
            errd.run()
            return

        self._write_comment_header(self._ofile, 'site_verilog.inc',
                                   comment_char='//')

        self.write_header(self._ofile, HEADER)

        for reg_key in self._dbase.get_keys():
            self.write_def(self._dbase.get_register(reg_key), self._prefix,
                           self._offset)
        self._ofile.write('\n')

        for line in TRAILER:
            self._ofile.write('%s\n' % line.replace('$M$', self._module))
        self._ofile.close()
