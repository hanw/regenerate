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

import gtk
import gobject
from columns import EditableColumn
from regenerate.db import GroupMapData, GroupData


class InstanceModel(gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    (ID_COL, BASE_COL, SORT_COL, RPT_COL, RPT_OFF_COL,
     FORMAT_COL, HDL_COL) = range(7)

    def __init__(self):
        gtk.TreeStore.__init__(self, str, str, gobject.TYPE_UINT64, str,
                               str, str, str)

    def change_id(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstanceModel.ID_COL, text)

    def change_format(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstanceModel.FORMAT_COL, text)

    def change_hdl(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstanceModel.HDL_COL, text)

    def change_base(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            self.set_value(node, InstanceModel.SORT_COL, int(text, 16))
            self.set_value(node, InstanceModel.BASE_COL, text)
        except ValueError:
            return

    def change_repeat(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            int(text)
            self.set_value(node, InstanceModel.RPT_COL, text)
        except ValueError:
            return

    def change_repeat_offset(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            value = int(text, 16)
            self.set_value(node, InstanceModel.RPT_OFF_COL, "%x" % value)
        except ValueError:
            return

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        node = self.append(None, row=('', '0', 0, "", "", ""))
        return self.get_path(node)

    def append_instance(self, inst):
        """
        Adds the specified instance to the InstanceList
        """
        self.append(row=(inst[0], "%08x" % inst[1], inst[1], "1", "0", ""))

    def get_values(self):
        """
        Returns the list of instance tuples from the model.
        """
        return [(val[0], int(val[1], 16)) for val in self if val[0]]


class InstanceList(object):

    def __init__(self, obj, id_changed, base_changed, repeat_changed,
                 repeat_offset_changed, format_changed, hdl_changed):
        self.__obj = obj
        self.__col = None
        self.__project = None
        self.__model = None
        self.__build_instance_table(id_changed, base_changed, repeat_changed,
                                    repeat_offset_changed, format_changed,
                                    hdl_changed)
        self.__enable_dnd()
        self.__obj.set_sensitive(False)

    def __enable_dnd(self):
        self.__obj.enable_model_drag_dest([('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT |
                                          gtk.gdk.ACTION_MOVE)
        self.__obj.connect('drag-data-received',
                           self.__drag_data_received_data)

        self.__obj.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK, [('text/plain', 0, 0)],
            gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.__obj.connect('drag-data-get', self.drag_data_get)

    def drag_data_get(self, treeview, context, selection, target_id, etime):
        tselection = treeview.get_selection()
        model, tree_iter = tselection.get_selected()
        data = model.get_value(tree_iter, 0)
        selection.set(selection.target, 8, data)

    def __drag_data_received_data(self, treeview, context, x, y, selection,
                                  info, etime):
        model = treeview.get_model()
        data = selection.data
        drop_info = treeview.get_dest_row_at_pos(x, y)
        row_data = [data, "0", 0, "1", "0", ""]
        if drop_info:
            path, position = drop_info
            if len(path) == 1:
                node = self.__model.get_iter(path)
                self.__model.append(node, row_data)
            else:
                parent = self.__model.get_iter((path[0],))
                node = self.__model.get_iter(path)
                if (position == gtk.TREE_VIEW_DROP_BEFORE
                    or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                    self.__model.insert_before(parent, node, row_data)
                else:
                    model.insert_after(parent, node, row_data)

    def set_project(self, project):
        self.__project = project
        self.__obj.set_sensitive(True)
        self.__populate()

    def __populate(self):
        if self.__project is None:
            return
        for item in self.__project.get_grouping_list():
            hval = "%x" % item.base
            node = self.__model.append(None, row=(item.name, hval, item.base,
                                                  "", "", "", item.hdl))
            for entry in self.__project.get_group_map(item[0]):
                self.__model.append(node, (entry.set, "%x" % entry.offset,
                                           entry.offset, "%d" % entry.repeat,
                                           "%x" % entry.repeat_offset,
                                           entry.format, entry.hdl))

    def __build_instance_table(self, id_changed, base_changed, repeat_changed,
                               repeat_offset_changed, format_changed,
                               hdl_changed):
        column = EditableColumn('Subsystem/Instance', id_changed,
                                InstanceModel.ID_COL)
        column.set_sort_column_id(InstanceModel.ID_COL)
        self.__obj.append_column(column)
        self.__col = column

        column = EditableColumn('Address base (hex)', base_changed,
                                InstanceModel.BASE_COL)
        column.set_sort_column_id(InstanceModel.SORT_COL)
        self.__obj.append_column(column)

        column = EditableColumn('Repeat', repeat_changed,
                                InstanceModel.RPT_COL)
        self.__obj.append_column(column)

        column = EditableColumn('Repeat Offset (hex)', repeat_offset_changed,
                                InstanceModel.RPT_OFF_COL)
        self.__obj.append_column(column)

        column = EditableColumn('ID Format', format_changed,
                                InstanceModel.FORMAT_COL)
        column.set_min_width(175)
        column.set_sort_column_id(InstanceModel.FORMAT_COL)
        self.__obj.append_column(column)

        column = EditableColumn('HDL Path', hdl_changed,
                                InstanceModel.HDL_COL)
        column.set_min_width(250)
        column.set_sort_column_id(InstanceModel.HDL_COL)
        self.__obj.append_column(column)
        self.__col = column

    def set_model(self, model):
        self.__obj.set_model(model)
        self.__model = model

    def get_groups(self):
        tree_iter = self.__model.get_iter_first()
        groups = []
        group_map = {}
        while tree_iter is not None:
            gname = self.__model.get_value(tree_iter, InstanceModel.ID_COL)
            base = self.__model.get_value(tree_iter, InstanceModel.SORT_COL)
            hdl = self.__model.get_value(tree_iter, InstanceModel.HDL_COL)

            groups.append(GroupData(gname, base, hdl))
            group_map[gname] = []

            child = self.__model.iter_children(tree_iter)
            while child:
                name = self.__model.get_value(child, InstanceModel.ID_COL)
                base = self.__model.get_value(child, InstanceModel.SORT_COL)
                rpt = int(self.__model.get_value(child, InstanceModel.RPT_COL))
                offset_str = self.__model.get_value(child,
                                                    InstanceModel.RPT_OFF_COL)
                offset = int(offset_str, 16)
                fmt = self.__model.get_value(child, InstanceModel.FORMAT_COL)
                hdl = self.__model.get_value(child, InstanceModel.HDL_COL)
                group_map[gname].append(
                    GroupMapData(name, base, rpt, offset, fmt, hdl))
                child = self.__model.iter_next(child)
            tree_iter = self.__model.iter_next(tree_iter)
        return (groups, group_map)

    def new_instance(self):
        self.__obj.set_cursor(self.__model.new_instance(),
                              focus_column=self.__col, start_editing=True)

    def get_selected_instance(self):
        return self.__obj.get_selection().get_selected()
