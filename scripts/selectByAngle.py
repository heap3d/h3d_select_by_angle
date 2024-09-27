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

from collections.abc import Iterable, Callable

import modo
import lx
import modo.constants as c

from h3d_utilites.scripts.h3d_utils import get_user_value
from h3d_utilites.scripts.h3d_debug import H3dDebug


USERVAL_NAME_ANGLE = "h3d_sba_thresholdAngle"
USERVAL_NAME_RUNNING = "h3d_sba_runningOnce"

ARG_ONCE = 'once'
ARG_FILL = None
ARG_SET = 'set'
ARG_ONCE_MATERIAL = 'oncematerial'
ARG_FILL_MATERIAL = 'fillmaterial'
ARG_ONCE_MATERIAL_THROUGH = 'oncematerialthrough'
ARG_FILL_MATERIAL_THROUGH = 'fillmaterialthrough'
ARG_CONTRACT_ONCE = 'contractonce'


class PolygonSelector:
    def __init__(self, polygons: Iterable[modo.MeshPolygon], angle: float):
        """
        Args:
            polygons (Iterable[modo.MeshPolygon]): selected polygons
            angle (float): angle threshold
        """
        self.angle = angle
        self.selection = {p.id: p for p in polygons}
        self.preselection: dict[int, modo.MeshPolygon] = dict()
        self.recent_preselection = self.get_selection_rim()
        self.current_ptags: tuple[str] = self.get_current_ptags()
        self.deselection: dict[int, modo.MeshPolygon] = dict()

    def get_selection_rim(self) -> dict[int, modo.MeshPolygon]:
        """
        gets polygons selection boundary

        Returns:
            dict[int, modo.MeshPolygon]: polygons in the selection boundary
        """
        selection_rim: dict[int, modo.MeshPolygon] = dict()
        for polygon in self.selection.values():
            for neighbor in polygon.neighbours:
                if neighbor.id not in self.selection:
                    selection_rim[polygon.id] = polygon
        return selection_rim

    def get_current_ptags(self) -> tuple[str]:
        """
        Creates tuple of material tags for selected polygons

        Returns:
            tuple[str]: collection of ptags
        """
        tags = set()
        for polygon in self.selection.values():
            tags.add(polygon.materialTag)
        return tuple(tags)

    def preselection_expand_fill(self, validator: Callable):
        """
        expands polygon preselection
        Args:
            validator (Callable): function to validate preselection expansion
        """
        while self.recent_preselection:
            self.preselection_expand_once(validator)

    def preselection_expand_once(self, validator: Callable):
        """
        expand polygon preselection by one step
        Args:
            validator (Callable): function to validate preselection expansion
        """
        expanded_preselection: dict[int, modo.MeshPolygon] = dict()
        for polygon in self.recent_preselection.values():
            for pre_polygon in polygon.neighbours:
                if pre_polygon.id in self.selection:
                    continue
                if pre_polygon.id in self.preselection:
                    continue
                if not validator(self, polygon, pre_polygon):
                    continue
                expanded_preselection[pre_polygon.id] = pre_polygon
        self.preselection.update(expanded_preselection)
        self.recent_preselection = expanded_preselection

    def can_select_by_angle(self, old_polygon: modo.MeshPolygon, new_polygon: modo.MeshPolygon) -> bool:
        """
        Checks if the in_polygon can be selected by angle

        Args:
            in_polygon (modo.MeshPolygon): polygon to check
            new_poly (modo.MeshPolygon): polygon to compare angle between normals

        Returns:
            bool: True if angle between normals of the in_polygon and the new_poly less than threshold angle,
                    False otherwise
        """
        in_vector = modo.Vector3(old_polygon.normal)
        compare_vector = modo.Vector3(new_polygon.normal)
        if compare_vector == in_vector:
            return True
        try:
            compare_angle = compare_vector.angle(in_vector)
        except ValueError:
            return True

        r_value = compare_angle <= self.angle
        return r_value

    def can_select_by_angle_material(self, old_polygon: modo.MeshPolygon, new_polygon: modo.MeshPolygon) -> bool:
        """
        Checks if the in_polygon can be selected by current ptags

        Args:
            in_polygon (modo.MeshPolygon): polygon to check
            new_poly (modo.MeshPolygon): polygon to compare

        Returns:
            bool: True if similar ptags and angle between normals of the in_polygon and the new_poly less
            than threshold angle, False otherwise
        """
        if old_polygon.materialTag != new_polygon.materialTag:
            return False
        return self.can_select_by_angle(old_polygon, new_polygon)

    def can_select_by_angle_material_through(
            self,
            old_polygon: modo.MeshPolygon,
            new_polygon: modo.MeshPolygon
            ) -> bool:
        """
        Checks if the in_polygon can be selected by current ptags

        Args:
            in_polygon (modo.MeshPolygon): polygon to check
            new_poly (modo.MeshPolygon): polygon to compare

        Returns:
            bool: True if similar ptags and angle between normals of the in_polygon and the new_poly less
            than threshold angle, False otherwise
        """
        if new_polygon.materialTag not in self.current_ptags:
            return False
        return self.can_select_by_angle(old_polygon, new_polygon)

    def selection_contract_once(self, validator: Callable):
        """
        Contracts polygon selection using current material limitation

        Args:
            validator (Callable): function to validate selection contraction
        """
        polygons_selection_rim = self.get_selection_rim()
        printi(polygons_selection_rim.values(), 'polygons_selection_rim:')
        for polygon in polygons_selection_rim.values():
            printd(f'{polygon=}')
            if any(validator(self, polygon, polygon_naightbour)
                   for polygon_naightbour in polygon.neighbours
                   if polygon_naightbour not in self.selection.values()):
                self.deselection[polygon.id] = polygon

        printi(self.deselection.values(), 'self.deselection:')
        for polygon in self.deselection.values():
            polygon.deselect()


def main():
    print("")
    print("start...")

    action = {
        ARG_ONCE: cmd_expand_once,
        ARG_FILL: cmd_expand_fill,
        ARG_SET: cmd_set_angle_userval,
        ARG_ONCE_MATERIAL: cmd_expand_once_material,
        ARG_FILL_MATERIAL: cmd_expand_fill_material,
        ARG_ONCE_MATERIAL_THROUGH: cmd_expand_once_material_through,
        ARG_FILL_MATERIAL_THROUGH: cmd_expand_fill_material_through,
        ARG_CONTRACT_ONCE: cmd_contract_once,
    }

    args = lx.args()
    if not args:
        cmd_expand_fill()
    else:
        action.get(args[0], cmd_expand_fill)()

    print("done.")


def cmd_expand_fill():
    """
    Command to expand the polygon selection
    """
    selection_action(PolygonSelector.preselection_expand_fill, PolygonSelector.can_select_by_angle)


def selection_action(action: Callable, validator: Callable):
    """Do specific selection action

    Args:
        action (Callable): function to execute
    """
    selector = get_polygon_selector()
    action(selector, validator)
    select_polygons(selector.preselection.values())


def select_polygons(polygons: Iterable[modo.MeshPolygon]):
    """
    Adds specified polygons to current polygon selection

    Args:
        polygons (Iterable[modo.MeshPolygon]): collection of polygons to add to the selection
    """
    for polygon in polygons:
        polygon.select()


def cmd_expand_once():
    """
    Command to expand the polygon selection by one step
    """
    selection_action(PolygonSelector.preselection_expand_once, PolygonSelector.can_select_by_angle)


def get_polygon_selector() -> PolygonSelector:
    """
    Initialize and return PolygonSelector instance

    Raises:
        ValueError: if self.angle is None

    Returns:
        PolygonSelector: initialized class instance
    """
    angle = get_user_value(USERVAL_NAME_ANGLE)
    meshes = get_selected_meshes()
    polygons = get_selected_polygons(meshes)
    if not angle:
        raise ValueError('angle is None')
    polygon_selector = PolygonSelector(polygons=polygons, angle=angle)
    return polygon_selector


def get_selected_meshes() -> Iterable[modo.Mesh]:
    """
    Selects meshes for selected polygons, workaround for selected polygons with no selected mesh items

    Returns:
        Iterable[modo.Mesh]: collection of meshes where polygons are selected
    """
    for mesh in modo.Scene().meshes:
        if not (polygons := mesh.geometry.polygons):
            continue
        if polygons.selected:
            mesh.select()
    meshes: Iterable[modo.Mesh] = modo.Scene().selectedByType(itype=c.MESH_TYPE)

    return meshes


def get_selected_polygons(meshes: Iterable[modo.Mesh]) -> list[modo.MeshPolygon]:
    """
    Gets selected polygons for specified meshes

    Args:
        meshes (Iterable[modo.Mesh]): collection of meshes

    Returns:
        list[modo.MeshPolygon]: list of selected polygons
    """
    polygons: list[modo.MeshPolygon] = []
    for mesh in meshes:
        for poly in mesh.geometry.polygons.selected:   # type: ignore
            polygons.append(poly)

    return polygons


def cmd_set_angle_userval():
    """
    Command to set angle modo user value
    """
    try:
        lx.eval("user.value %s" % USERVAL_NAME_ANGLE)
    except RuntimeError:
        pass


def cmd_expand_fill_material():
    selection_action(PolygonSelector.preselection_expand_fill, PolygonSelector.can_select_by_angle_material)


def cmd_expand_fill_material_through():
    selection_action(PolygonSelector.preselection_expand_fill, PolygonSelector.can_select_by_angle_material_through)


def cmd_expand_once_material():
    selection_action(PolygonSelector.preselection_expand_once, PolygonSelector.can_select_by_angle_material)


def cmd_expand_once_material_through():
    selection_action(PolygonSelector.preselection_expand_once, PolygonSelector.can_select_by_angle_material_through)


def cmd_contract_once():
    selection_action(PolygonSelector.selection_contract_once, PolygonSelector.can_select_by_angle_material)


if __name__ == "__main__":
    h3dd = H3dDebug(enable=False, file=modo.Scene().filename + '.log')
    printd = h3dd.print_debug
    printi = h3dd.print_items

    main()
