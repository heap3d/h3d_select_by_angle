#!/usr/bin/python
# ================================
# (C)2019-2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
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
# thresholdAngle = 30
runningOnce = True
userValAngleName = 'h3d_sba_thresholdAngle'
userValAngleUsername = 'angle'
# userValAngleDialogname = 'set selection angle threshold'
userValRunningName = 'h3d_sba_runningOnce'
selectionPolyDict = {}
preSelectionPolyDict = {}
edgeOfSelectionPolyDict = ()


def addPolyToSelection(in_polygon):  # add polygon to selection dict
    selectionPolyDict[in_polygon.id] = in_polygon


def addPolyToPreSelection(in_polygon):
    preSelectionPolyDict[in_polygon.id] = in_polygon


def isPolySelected(in_polygon):  # check if polygon selected by mark
    result = in_polygon.id in selectionPolyDict
    # if result:
    #     print 'isPolySelected polygon id:', polygon.index, polygon.id, result
    return result


def isPolyPreSelected(in_polygon):
    result = in_polygon.id in preSelectionPolyDict
    # if result:
    #     print 'is_poly_pre_selected polygon id:', polygon.index, polygon.id, result
    return result


def isPolyOnTheEdgeOfSelection(in_polygon):
    result = in_polygon.id in edgeOfSelectionPolyDict
    # if result:
    #     print 'is_poly_on_the_edge_of_selection polygon id:', polygon.index, polygon.id, result
    return result


def canSelectByAngle(in_polygon, newPoly):  # compare two polygon normals
    # compareVector = modo.Vector3(newPoly.normal).cross(modo.Vector3(in_polygon.normal))
    compareVector = modo.Vector3(newPoly.normal)
    try:
        compareAngle = compareVector.angle(modo.Vector3(in_polygon.normal))
    except ValueError:
        print 'can_select_by_angle ValueError exception, returned False: ---------------------------------'
        print 'polygon.id:<{}>, polygon.normal:<{}>'.format(in_polygon.id, in_polygon.normal)
        return False
        # exit()
    rValue = compareAngle <= thresholdRad
    # if rValue:
    #     print 'can_select_by_angle true:', polygon.index, newPoly.index
    return rValue


print
print 'Running...'
scene = modo.scene.current()
# print lx.args()

# if not lx.eval('query scriptsysservice userValue.isDefined ? "%s"' % userValAngleName):
#     lx.eval('user.defNew "%s" float' % userValAngleName)
#     lx.eval('user.def "%s" username "%s"' % (userValAngleName, userValAngleUsername))
#     lx.eval('user.def "%s" dialogname "%s"' % (userValAngleName, userValAngleDialogname))

if len(lx.args()) > 0:
    if lx.args()[0] == 'set':
        # print 'set'
        try:
            lx.eval('user.value %s' % userValAngleName)
        except Exception:
            modo.dialogs.alert(title='threshold angle', message='error reading user value', dtype='error')
        print 'selection angle rads threshold set to', lx.eval('user.value "%s" ?value' % userValAngleName)
        print 'Done.'
        exit()
    else:
        runningOnceString = lx.args()[0]
        runningOnce = 'true' in runningOnceString.lower()
        if len(lx.args()) > 1:
            lx.eval('user.value "%s" %s' % (userValAngleName, lx.args()[1]))

# thresholdAngle = lx.eval('user.value "%s" ?value' % userValAngleName) / math.pi * 180
# thresholdRad = math.sin(math.radians(thresholdAngle))
thresholdRad = lx.eval('user.value "%s" ?value' % userValAngleName)
thresholdAngle = thresholdRad * 180 / math.pi
print 'once:', runningOnce, '\tangle:', thresholdAngle, '\tthresholdRad:', thresholdRad

selectedMesh = scene.selectedByType('mesh')
for mesh in selectedMesh:
    for polygon in mesh.geometry.polygons.selected:
        addPolyToSelection(polygon)  # add selected poly to selection dict
for i in selectionPolyDict:
    polygon = selectionPolyDict[i]
    for prePolygon in polygon.neighbours:
        if not isPolyPreSelected(prePolygon):  # if not in pre-selection dict
            if not isPolySelected(prePolygon):  # if not in selection dict
                if canSelectByAngle(polygon, prePolygon):  # if in normal angle threshold
                    addPolyToPreSelection(prePolygon)  # add to pre-selection dict
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
            print 'Safe limit reached.'
            break
        print 'safeCounter:', safeCounter
        print 'edgeOfSelectionPolyDict', len(edgeOfSelectionPolyDict), edgeOfSelectionPolyDict
        print 'preSelectionPolyDict', len(preSelectionPolyDict), preSelectionPolyDict
        for i in edgeOfSelectionPolyDict:
            polygon = edgeOfSelectionPolyDict[i]
            for prePolygon in polygon.neighbours:
                if not isPolyPreSelected(prePolygon):  # if not in pre-selection dict
                    if not isPolyOnTheEdgeOfSelection(prePolygon):  # if not in selection dict
                        if not isPolySelected(prePolygon):
                            if canSelectByAngle(polygon, prePolygon):  # if in normal angle threshold
                                addPolyToPreSelection(prePolygon)  # add to pre-selection dict
                                # print 'polygon preselected:', prePolygon.index, prePolygon.id, prePolygon
        for i in preSelectionPolyDict:
            polygon = preSelectionPolyDict[i]
            polygon.select()
        edgeOfSelectionPolyDict = preSelectionPolyDict.copy()
        selectionPolyDict.update(edgeOfSelectionPolyDict)
        preSelectionPolyDict.clear()

print 'Done.'
