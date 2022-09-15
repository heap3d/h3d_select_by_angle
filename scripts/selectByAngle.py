#!/usr/bin/python
# ================================
# (C)2019-2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# selectByAngle.py
# version 3.2
# select polygons by normal angle threshold
# ================================

# command line arguments: selectByAngle %1 %2
# %1: set - set mode, open dialog to set threshold angle
# %1: runningOnce - true if running one step
# %2: thresholdAngle - threshold angle between normals to select

import modo
import math
import lx

safeLimit = 500
runningOnce = True
userValAngleName = 'h3d_sba_thresholdAngle'
userValAngleUsername = 'angle'
userValRunningName = 'h3d_sba_runningOnce'
selectionPolyDict = {}
preSelectionPolyDict = {}
edgeOfSelectionPolyDict = ()


def add_poly_to_selection(in_polygon):  # add polygon to selection dict
    selectionPolyDict[in_polygon.id] = in_polygon


def add_poly_to_pre_selection(in_polygon):
    preSelectionPolyDict[in_polygon.id] = in_polygon


def is_poly_selected(in_polygon):  # check if polygon selected by mark
    result = in_polygon.id in selectionPolyDict
    return result


def is_poly_pre_selected(in_polygon):
    result = in_polygon.id in preSelectionPolyDict
    return result


def is_poly_on_the_edge_of_selection(in_polygon):
    result = in_polygon.id in edgeOfSelectionPolyDict
    return result


def can_select_by_angle(in_polygon, new_poly):  # compare two polygon normals
    in_vector = modo.Vector3(in_polygon.normal)
    compare_vector = modo.Vector3(new_poly.normal)
    if compare_vector == in_vector:
        return True
    try:
        compare_angle = compare_vector.angle(in_vector)
    except ValueError:
        return True
    r_value = compare_angle <= thresholdRad
    return r_value


print()
print('Running...')
scene = modo.scene.current()

print('')
print('start...')

if len(lx.args()) > 0:
    if lx.args()[0] == 'set':
        try:
            lx.eval('user.value %s' % userValAngleName)
        except RuntimeError:
            modo.dialogs.alert(title='threshold angle', message='error setting user value', dtype='error')
        print('selection angle rads threshold set to', lx.eval('user.value "%s" ?value' % userValAngleName))
        print('Done.')
        exit()
    else:
        runningOnceString = lx.args()[0]
        runningOnce = 'true' in runningOnceString.lower()
        if len(lx.args()) > 1:
            lx.eval('user.value "%s" %s' % (userValAngleName, lx.args()[1]))

thresholdRad = lx.eval('user.value "%s" ?value' % userValAngleName)
thresholdAngle = thresholdRad * 180 / math.pi
print('once:', runningOnce, '\tangle:', thresholdAngle, '\tthresholdRad:', thresholdRad)

selectedMesh = scene.selectedByType('mesh')
for mesh in selectedMesh:
    for polygon in mesh.geometry.polygons.selected:
        add_poly_to_selection(polygon)  # add selected poly to selection dict
for i in selectionPolyDict:
    polygon = selectionPolyDict[i]
    for prePolygon in polygon.neighbours:
        if not is_poly_pre_selected(prePolygon):  # if not in pre-selection dict
            if not is_poly_selected(prePolygon):  # if not in selection dict
                if can_select_by_angle(polygon, prePolygon):  # if in normal angle threshold
                    add_poly_to_pre_selection(prePolygon)  # add to pre-selection dict
for i in preSelectionPolyDict:
    polygon = preSelectionPolyDict[i]
    polygon.select()
edgeOfSelectionPolyDict = preSelectionPolyDict.copy()
selectionPolyDict.update(edgeOfSelectionPolyDict)
preSelectionPolyDict.clear()
safeCounter = 0
if not runningOnce:
    while len(edgeOfSelectionPolyDict) > 0:
        safeCounter += 1
        if safeCounter > safeLimit:
            print('Safe limit reached.')
            break
        for i in edgeOfSelectionPolyDict:
            polygon = edgeOfSelectionPolyDict[i]
            for prePolygon in polygon.neighbours:
                if not is_poly_pre_selected(prePolygon):  # if not in pre-selection dict
                    if not is_poly_on_the_edge_of_selection(prePolygon):  # if not in selection dict
                        if not is_poly_selected(prePolygon):
                            if can_select_by_angle(polygon, prePolygon):  # if in normal angle threshold
                                add_poly_to_pre_selection(prePolygon)  # add to pre-selection dict
        for i in preSelectionPolyDict:
            polygon = preSelectionPolyDict[i]
            polygon.select()
        edgeOfSelectionPolyDict = preSelectionPolyDict.copy()
        selectionPolyDict.update(edgeOfSelectionPolyDict)
        preSelectionPolyDict.clear()

print('Done.')
