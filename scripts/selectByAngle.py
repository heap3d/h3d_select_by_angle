#!/usr/bin/python
# ================================
# (C)2019-2022 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# selectByAngle.py
# select polygons by normal angle threshold
# ================================

# command line arguments: selectByAngle %1
# %1: set - set mode, open dialog to set threshold angle
# %1: once - expand selection by 1 step

import modo
import lx
import modo.constants as c

USERVAL_NAME_ANGLE = "h3d_sba_thresholdAngle"
USERVAL_NAME_RUNNING = "h3d_sba_runningOnce"


class PolygonSelector:
    def __init__(self, polygons=[], threshold=5):
        self.polygons = polygons
        self.threshold = threshold
        # set selection dict
        self.selection = dict()
        for poly in polygons:
            self.add_to_selection(poly)
        # set preselection_dict
        self.preselection = self.selection.copy()
        # set edge_of_selection dict
        self.edge_of_selection = dict()
        # set failed pairs list
        self.failed_pairs = []

    def add_to_failed(self, poly1, poly2):
        """add polygons in ascneding order"""
        if not all((poly1, poly2)):
            return
        if poly1.index < poly2.index:
            self.failed_pairs.append((poly1, poly2))
        else:
            self.failed_pairs.append((poly2, poly1))

    def in_failed_pairs(self, poly1, poly2):
        """check in ascending order"""
        if poly1.index < poly2.index:
            return (poly1, poly2) in self.failed_pairs
        else:
            return (poly2, poly1) in self.failed_pairs

    def add_to_selection(self, in_polygon):
        """add polygon to selection dict"""
        self.selection[in_polygon.id] = in_polygon

    def add_to_preselection(self, in_polygon):
        self.preselection[in_polygon.id] = in_polygon

    def is_selected(self, in_polygon):
        """check if polygon selected by mark"""
        result = in_polygon.id in self.selection
        return result

    def is_pre_selected(self, in_polygon):
        result = in_polygon.id in self.preselection
        return result

    def is_on_selection_edge(self, in_polygon):
        result = in_polygon.id in self.edge_of_selection
        return result

    def can_select_by_angle(self, in_polygon, new_poly):
        """compare two polygon normals"""
        in_vector = modo.Vector3(in_polygon.normal)
        compare_vector = modo.Vector3(new_poly.normal)
        if compare_vector == in_vector:
            return True
        try:
            compare_angle = compare_vector.angle(in_vector)
        except ValueError:
            return True

        r_value = compare_angle <= self.threshold
        return r_value

    def selection_expand_fill(self):
        # expand selection by one step first
        # self.selection_expand_once()

        self.edge_of_selection = self.preselection.copy()
        self.selection.update(self.edge_of_selection)
        self.preselection.clear()

        while self.edge_of_selection:
            for polygon in self.edge_of_selection.values():
                for pre_polygon in polygon.neighbours:
                    # if not in pre-selection dict
                    if self.is_pre_selected(pre_polygon):
                        continue
                    # if not in selection dict
                    if self.is_on_selection_edge(pre_polygon):
                        continue
                    if self.is_selected(pre_polygon):
                        continue
                    # if in normal angle threshold
                    if not self.can_select_by_angle(polygon, pre_polygon):
                        continue
                    # if in failed_pairs list
                    if self.in_failed_pairs(polygon, pre_polygon):
                        continue
                    # add to pre-selection dict
                    self.add_to_preselection(pre_polygon)

            for polygon in self.preselection.values():
                polygon.select()

            self.edge_of_selection = self.preselection.copy()
            self.selection.update(self.edge_of_selection)
            self.preselection.clear()

    def selection_expand_once(self):
        for polygon in self.selection.values():
            for pre_polygon in polygon.neighbours:
                # if not in pre-selection dict
                if self.is_pre_selected(pre_polygon):
                    continue
                # if not in selection dict
                if self.is_selected(pre_polygon):
                    continue
                # if in normal angle threshold
                if not self.can_select_by_angle(polygon, pre_polygon):
                    continue
                # add to pre-selection dict
                self.add_to_preselection(pre_polygon)

        for polygon in self.preselection.values():
            polygon.select()


def get_selected_polygons(meshes):
    polygons = []
    for mesh in meshes:
        for poly in mesh.geometry.polygons.selected:
            polygons.append(poly)

    return polygons


def main():
    print("")
    print("start...")

    if not lx.args():
        # selection expand fill
        print("expand fill")
        threshold = lx.eval("user.value {} ?".format(USERVAL_NAME_ANGLE))
        meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)
        polygons = get_selected_polygons(meshes)
        poly_selector = PolygonSelector(polygons=polygons, threshold=threshold)
        poly_selector.selection_expand_fill()

        print("Selection expand fill - done.")
        return

    if lx.args()[0] == "set":
        # set selection threnshold angle
        try:
            lx.eval("user.value %s" % USERVAL_NAME_ANGLE)
        except RuntimeError:
            print("User abort.")

        print("Selection treshold angle set - done.")
        return

    if lx.args()[0] == "once":
        # selection expand once
        print("expand once")
        threshold = lx.eval("user.value {} ?".format(USERVAL_NAME_ANGLE))
        meshes = modo.Scene().selectedByType(itype=c.MESH_TYPE)
        polygons = get_selected_polygons(meshes)
        poly_selector = PolygonSelector(polygons=polygons, threshold=threshold)
        poly_selector.selection_expand_once()

        print("Selection expand once - done.")
        return

    print("done.")


if __name__ == "__main__":
    main()
