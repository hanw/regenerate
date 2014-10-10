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
Provides both the GTK ListStore and ListView for the bit fields.
"""

import gtk
from regenerate.db import BitField, TYPES
from columns import EditableColumn, ComboMapColumn

TYPE2STR = [(t.description, t.type) for t in sorted(TYPES)]
(BIT_TITLE, BIT_SIZE, BIT_SORT, BIT_EXPAND, BIT_MONO) = range(5)


class BitModel(gtk.ListStore):
    """
    The GTK list store model for the bit fields. This model is added to the
    ListView to provide the data for the bitfields.
    """

    RESET2STR = (
        ("Constant", BitField.RESET_NUMERIC),
        ("Input Port", BitField.RESET_INPUT),
        ("Parameter", BitField.RESET_PARAMETER))

    (ICON_COL, BIT_COL, NAME_COL, TYPE_COL, RESET_COL,
     RESET_TYPE_COL, SORT_COL, FIELD_COL) = range(8)

    def __init__(self):
        """
        Initialize the base class with the object types that we are going to
        be adding to the model.
        """
        gtk.ListStore.__init__(self, str, str, str, str, str, str,
                               int, object)

    def append_field(self, field):
        """
        Adds the field to the model, filling out the fields in the model.
        """
        data = [None,
                bits(field),
                field.field_name,
                TYPE2STR[field.field_type][0],
                get_field_reset_data(field),
                self.RESET2STR[field.reset_type][0],
                field.lsb,
                field]

        node = self.append(row=data)
        return self.get_path(node)

    def get_bitfield_at_path(self, path):
        """
        Returns the field object associated with a ListModel path.
        """
        return self[path][-1]


class BitList(object):
    """
    Bit Field display representation. We can't inherit from the ListModel,
    since it is generated by glade. So this object connects to the list
    model through the list model parameter passed into the constructor.
    """

    BIT_COLS = (
        # Title, Size, Sort, Expand, Monospace
        ('', 20, -1, False, False),
        ('Bits', 60, BitModel.SORT_COL, False, True),
        ('Name', 125, BitModel.NAME_COL, True, False),
        ('Type', 325, -1, True, False),
        ('Reset', 100, -1, False, True),
        ('Reset Type', 75, -1, False, False),
        )

    def __init__(self, obj, combo_edit, text_edit, selection_changed):
        """
        Creates the object, connecting it to the ListView (obj). Three
        callbacks are associated with the object.

        combo_edit - called when the type combo is edited
        text_edit - called when a text field is edited
        selection_changed - called when the selected field is changed
        """
        self.__obj = obj
        self.__col = None
        self.__model = None
        self.__build_bitfield_columns(combo_edit, text_edit)
        self.__obj.get_selection().connect('changed', selection_changed)

    def set_model(self, model):
        """
        Associates a List Model with the list view.
        """
        self.__model = model
        self.__obj.set_model(model)

    def __build_bitfield_columns(self, combo_edit, text_edit):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """
        for (i, col) in enumerate(self.BIT_COLS):
            if i == BitModel.TYPE_COL:
                column = ComboMapColumn(col[BIT_TITLE], combo_edit,
                                        TYPE2STR, i)
            elif i == BitModel.RESET_TYPE_COL:
                column = ComboMapColumn(col[BIT_TITLE], combo_edit,
                                        BitModel.RESET2STR, i)
            elif i == BitModel.ICON_COL:
                renderer = gtk.CellRendererPixbuf()
                column = gtk.TreeViewColumn("", renderer, stock_id=i)
            else:
                column = EditableColumn(col[BIT_TITLE], text_edit, i,
                                        col[BIT_MONO])
            if i == BitModel.BIT_COL:
                self.__col = column
            if col[BIT_SORT] >= 0:
                column.set_sort_column_id(col[BIT_SORT])
            column.set_min_width(col[BIT_SIZE])
            column.set_expand(col[BIT_EXPAND])
            column.set_resizable(True)
            self.__obj.append_column(column)

    def get_selected_row(self):
        """
        Returns the path of the selected row
        """
        value = self.__obj.get_selection().get_selected_rows()
        if value:
            return value[1]
        else:
            return None

    def select_row(self, path):
        """
        Selectes the row associated with the path
        """
        if path:
            self.__obj.get_selection().select_path(path)

    def select_field(self):
        """
        Returns the field object associated with selected row.
        """
        data = self.__obj.get_selection().get_selected()
        if data:
            (store, node) = data
            if node:
                return store.get_value(node, BitModel.FIELD_COL)
        return None

    def add_new_field(self, field):
        """
        Adds a new field to the model, and sets editing to begin
        """
        path = self.__model.append_field(field)
        self.__obj.set_cursor(path, focus_column=self.__col,
                              start_editing=True)


def bits(field):
    """
    Returns a text representation of the bit field range
    """
    if field.lsb == field.msb:
        return "{0:d}".format(field.lsb)
    else:
        return "{0:d}:{1:d}".format(field.msb, field.lsb)


def reset_value(field):
    """
    Returns a string representation of the reset value.
    """
    strval = "{0:x}".format(field.reset_value)
    return strval.zfill(field.width / 4)


def get_field_reset_data(field):
    """
    Converts the fields reset value/type into a displayable value.
    """
    if field.reset_type == BitField.RESET_NUMERIC:
        reset = reset_value(field)
    elif field.reset_type == BitField.RESET_INPUT:
        reset = field.reset_input
    else:
        reset = field.reset_parameter
    return reset
