#!/usr/bin/python
# ================================
# (C)2019-2024 Dmytro Holub
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

from h3d_utilites.scripts.h3d_utils import get_user_value


USERVAL_NAME_ANGLE = "h3d_sba_thresholdAngle"
USERVAL_NAME_RUNNING = "h3d_sba_runningOnce"

ARG_FILL = None
ARG_ONCE = 'once'
ARG_SET = 'set'
ARG_FILL_MATERIAL = 'fillmaterial'
ARG_ONCE_MATERIAL = 'oncematerial'


def expand_fill():
    """
    Expands the polygon selection using the angle stored in the modo custom value
    """
    angle = get_user_value(USERVAL_NAME_ANGLE)
    meshes = get_selected_meshes()
    polygons = get_selected_polygons(meshes)
    if not angle:
        raise ValueError('angle is None')
    poly_selector = PolygonSelector(polygons=polygons, angle=angle)
    poly_selector.selection_expand_fill()


def expand_once():
    """
    Expands the polygon selection by one step, using the angle stored in the custom modo value
    """
    angle = get_user_value(USERVAL_NAME_ANGLE)
    meshes = get_selected_meshes()
    polygons = get_selected_polygons(meshes)
    if not angle:
        raise ValueError('angle is None')
    poly_selector = PolygonSelector(polygons=polygons, angle=angle)
    poly_selector.selection_expand_once()


def set_angle_userval():
    """
    Sets angle modo user value
    """
    try:
        lx.eval("user.value %s" % USERVAL_NAME_ANGLE)
    except RuntimeError:
        pass


def get_selected_meshes() -> list[modo.Mesh]:
    """
    Selects meshes for selected polygons, workaround for selected polygons with no selected mesh items

    Returns:
        list[modo.Mesh]: list of meshes where polygons are selected
    """
    for mesh in modo.Scene().meshes:
        if not (polygons := mesh.geometry.polygons):
            continue
        if polygons.selected:
            mesh.select()
    meshes: list[modo.Mesh] = modo.Scene().selectedByType(itype=c.MESH_TYPE)

    return meshes


def get_selected_polygons(meshes: list[modo.Mesh]) -> list[modo.MeshPolygon]:
    """
    Gets selected polygons for specified meshes

    Args:
        meshes (list[modo.Mesh]): list of meshes

    Returns:
        list[modo.MeshPolygon]: list of selected polygons
    """
    polygons: list[modo.MeshPolygon] = []
    for mesh in meshes:
        for poly in mesh.geometry.polygons.selected:   # type: ignore
            polygons.append(poly)

    return polygons


class PolygonSelector:
    def __init__(self, polygons: list[modo.MeshPolygon], angle: float):
        """
        Args:
            polygons (list[modo.MeshPolygon]): selected polygons
            angle (float): angle threshold
        Fields:
            polygons
            angle
            selection
            preselection
            edge_of_selection
        """
        self.polygons = polygons
        self.angle = angle
        self.selection = dict()
        for poly in polygons:
            self.add_to_selection(poly)
        self.preselection = self.selection.copy()

        # TODO self.edge_of_selection smart initialization
        self.edge_of_selection = dict()

    def selection_expand_fill(self):
        """
        expands polygon selection
        """
        self.edge_of_selection = self.preselection.copy()
        self.selection.update(self.edge_of_selection)
        self.preselection.clear()

        while self.edge_of_selection:
            for polygon in self.edge_of_selection.values():
                for pre_polygon in polygon.neighbours:
                    if self.is_pre_selected(pre_polygon):
                        continue
                    if self.is_on_selection_edge(pre_polygon):
                        continue
                    if self.is_selected(pre_polygon):
                        continue
                    if not self.can_select_by_angle(polygon, pre_polygon):
                        continue
                    self.add_to_preselection(pre_polygon)

            for polygon in self.preselection.values():
                polygon.select()

            self.edge_of_selection = self.preselection.copy()
            self.selection.update(self.edge_of_selection)
            self.preselection.clear()

    def select_polygons(self, polygons: list[modo.MeshPolygon]):
        """
        Adds specified polygons to current polygon selection

        Args:
            polygons (list[modo.MeshPolygon]): list of polygons to add to the selection
        """
        for polygon in polygons:
            polygon.select()

    def selection_expand_once(self):
        """
        expand polygon selection by one step
        """
        for polygon in self.selection.values():
            for pre_polygon in polygon.neighbours:
                if self.is_pre_selected(pre_polygon):
                    continue
                if self.is_selected(pre_polygon):
                    continue
                if not self.can_select_by_angle(polygon, pre_polygon):
                    continue
                self.add_to_preselection(pre_polygon)

        for polygon in self.preselection.values():
            polygon.select()

    def add_to_selection(self, in_polygon: modo.MeshPolygon):
        """adds polygon to selection dict"""
        self.selection[in_polygon.id] = in_polygon

    def is_pre_selected(self, in_polygon: modo.MeshPolygon) -> bool:
        """
        Checks if the polygon in the preselection dict

        Args:
            in_polygon (modo.MeshPolygon): polygon to check

        Returns:
            bool: True if polygon in the preselection dict, False otherwise
        """
        result = in_polygon.id in self.preselection
        return result

    def is_on_selection_edge(self, in_polygon: modo.MeshPolygon) -> bool:
        """
        Checks if the polygon in the selection edge dict

        Args:
            in_polygon (modo.MeshPolygon): polygon to check

        Returns:
            bool: True if the polygon in the selection edge dict, False otherwise
        """
        result = in_polygon.id in self.edge_of_selection
        return result

    def is_selected(self, in_polygon: modo.MeshPolygon) -> bool:
        """
        Checks if the polygon is selected

        Args:
            in_polygon (modo.MeshPolygon): polygon to check

        Returns:
            bool: True if the polygon is in the selection dict, False otherwise
        """
        result = in_polygon.id in self.selection
        return result

    def can_select_by_angle(self, in_polygon: modo.MeshPolygon, new_poly: modo.MeshPolygon) -> bool:
        """
        Checks if the in_polygon can be selected by angle

        Args:
            in_polygon (modo.MeshPolygon): polygon to check
            new_poly (modo.MeshPolygon): polygon to compare angle between normals

        Returns:
            bool: True if angle between normals of the in_polygon and the new_poly less than threshold angle,
                    False otherwise
        """
        in_vector = modo.Vector3(in_polygon.normal)
        compare_vector = modo.Vector3(new_poly.normal)
        if compare_vector == in_vector:
            return True
        try:
            compare_angle = compare_vector.angle(in_vector)
        except ValueError:
            return True

        r_value = compare_angle <= self.angle
        return r_value

    def add_to_preselection(self, in_polygon: modo.MeshPolygon):
        """
        adds the polygon to the preselection dict
        """
        self.preselection[in_polygon.id] = in_polygon


def main():
    print("")
    print("start...")

    action = {
        ARG_FILL: expand_fill,
        ARG_ONCE: expand_once,
        ARG_SET: set_angle_userval,
    }

    action.get(lx.args(), expand_fill)()

    print("done.")


if __name__ == "__main__":
    main()
