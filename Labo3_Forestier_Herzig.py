#!/usr/bin/env python
#
# Labo 3 from VTK.
#
# Goal: Displaying a knee in 4 different viewports with filters, contouring, clipping and different effects.
#
# Authors: Forestier Quentin & Herzig Melvyn
#
# Date: 24.05.2022

import vtk
import os.path

# --------------------------- CONSTANTS ---------------------------
SKIN_COLOR = [0.77, 0.61, 0.60]

SPHERE_CENTER = [70, 40, 100]
SPHERE_RADIUS = 45

SCANER_FILE_NAME = "vw_knee.slc"
BONE_SAVE_FILE_NAME = "bone_save.vtk"

LIGHT_RED = [1.0, 0.8, 0.8]
LIGHT_GREEN = [0.8, 1.0, 0.8]
LIGHT_BLUE = [0.8, 0.8, 1.0]
LIGHT_GREY = [0.8, 0.8, 0.8]
UGLY_YELLOW = [1, 0.82, 0.37]
BONE_COLOR = [0.90, 0.90, 0.90]
BLACK = [0.0, 0.0, 0.0]

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
WINDOW_NAME = "MultipleViewPorts"

STRIP_COUNT = 19
STRIP_RADIUS = 2

# ------------------------ GENERAL ELEMENTS -----------------------
# mostly topologies. Elements that are used by multiple viewports.

# Reading the knee slc file.
# https://kitware.github.io/vtk-examples/site/Python/IO/ReadSLC/
slcReader = vtk.vtkSLCReader()
slcReader.SetFileName(SCANER_FILE_NAME)

# Getting the outline box actor, used in each view.
boxOutlineFilter = vtk.vtkOutlineFilter()
boxOutlineFilter.SetInputConnection(slcReader.GetOutputPort())

boxPolyDataMapper = vtk.vtkPolyDataMapper()
boxPolyDataMapper.SetInputConnection(boxOutlineFilter.GetOutputPort())

boxActor = vtk.vtkActor()
boxActor.SetMapper(boxPolyDataMapper)
boxActor.GetProperty().SetColor(BLACK)

# Getting skin topology, used in stripped and "rainbow" bone view port.
skinContourFilter = vtk.vtkContourFilter()
skinContourFilter.SetInputConnection(slcReader.GetOutputPort())
skinContourFilter.SetValue(0, 50)  # 50 is value issued from random tries.

# Getting clipped skin mapper, used in views with skin that is clipped by a sphere.
sphere = vtk.vtkSphere()
sphere.SetRadius(SPHERE_RADIUS)
sphere.SetCenter(SPHERE_CENTER)

clippedSkinPolyData = vtk.vtkClipPolyData()
clippedSkinPolyData.SetClipFunction(sphere)
clippedSkinPolyData.SetInputConnection(skinContourFilter.GetOutputPort())

clippedSkinPolyDataMapper = vtk.vtkPolyDataMapper()
clippedSkinPolyDataMapper.SetInputConnection(clippedSkinPolyData.GetOutputPort())
clippedSkinPolyDataMapper.ScalarVisibilityOff()

# Getting bone actor, used in every view except the "rainbow" bone
boneContourFilter = vtk.vtkContourFilter()
boneContourFilter.SetInputConnection(slcReader.GetOutputPort())
boneContourFilter.SetValue(0, 72)  # From example

bonePolyDataMapper = vtk.vtkPolyDataMapper()
bonePolyDataMapper.SetInputConnection(boneContourFilter.GetOutputPort())
bonePolyDataMapper.ScalarVisibilityOff()

boneActor = vtk.vtkActor()
boneActor.SetMapper(bonePolyDataMapper)
boneActor.GetProperty().SetColor(BONE_COLOR)


# This function returns the actors used to display the view with the stripped skin (top-left in example).
def solid_knee_stripped_skin():
    # Defining a plane to cut
    plane = vtk.vtkPlane()

    # Creating skin mapper
    skinPolyDataMapper = vtk.vtkPolyDataMapper()
    skinPolyDataMapper.SetInputConnection(skinContourFilter.GetOutputPort())
    skinPolyDataMapper.ScalarVisibilityOff()

    # Making a cutter
    cutter = vtk.vtkCutter()
    cutter.SetInputData(skinPolyDataMapper.GetInput())
    cutter.SetCutFunction(plane)
    cutter.GenerateValues(STRIP_COUNT, boxActor.GetBounds()[-2], boxActor.GetBounds()[-1])

    # Making the triangle strips
    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(cutter.GetOutputPort())
    stripper.JoinContiguousSegmentsOn()

    # Making nice tubes around lines of stripper
    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetRadius(STRIP_RADIUS)
    tubeFilter.SetInputConnection(stripper.GetOutputPort())

    # Creating tubes mapper
    tubesPolyDataMapper = vtk.vtkPolyDataMapper()
    tubesPolyDataMapper.ScalarVisibilityOff()
    tubesPolyDataMapper.SetInputConnection(tubeFilter.GetOutputPort())

    # Creating tubes actor
    tubesActor = vtk.vtkActor()
    tubesActor.SetMapper(tubesPolyDataMapper)
    tubesActor.GetProperty().SetColor(SKIN_COLOR)

    return [boxActor, boneActor, tubesActor]


# This function returns the actors used to display the view with the half transparent clipped
# skin with the invisible sphere (top-right in example).
def solid_knee_half_transparent_clipped_skin_invisible_sphere():
    # Skin actor with front face half transparent and back face not transparent
    skinActor = vtk.vtkActor()
    skinActor.SetMapper(clippedSkinPolyDataMapper)
    skinActor.GetProperty().SetColor(SKIN_COLOR)
    skinActor.GetProperty().SetOpacity(0.4)
    skinActor.SetBackfaceProperty(skinActor.MakeProperty())
    skinActor.GetBackfaceProperty().SetColor(SKIN_COLOR)

    return [boxActor, boneActor, skinActor]


# This function returns the actors used to display the view with the solid clipped
# skin with the half transparent sphere (bottom-left in example).
def solid_knee_solid_clipped_skin_half_transparent_sphere():
    # Skin actor
    skinActor = vtk.vtkActor()
    skinActor.SetMapper(clippedSkinPolyDataMapper)
    skinActor.GetProperty().SetColor(SKIN_COLOR)

    # https://python.hotexamples.com/fr/examples/vtk/-/vtkSampleFunction/python-vtksamplefunction-function-examples.html
    # We need to convert an implicit function to a polydata
    # We have to use an explicit function and set the bounding
    sphereSampleFunction = vtk.vtkSampleFunction()
    sphereSampleFunction.SetImplicitFunction(sphere)

    sphereBounds = []

    for c in SPHERE_CENTER:
        sphereBounds.append(c - SPHERE_RADIUS)
        sphereBounds.append(c + SPHERE_RADIUS)

    sphereSampleFunction.SetModelBounds(sphereBounds)

    # We create a filter who define the outline of the sphere
    contourFilter = vtk.vtkContourFilter()
    contourFilter.SetInputConnection(sphereSampleFunction.GetOutputPort())

    # And we put it in a PolyDataMapper
    spherePolyDataMapper = vtk.vtkPolyDataMapper()
    spherePolyDataMapper.SetInputConnection(contourFilter.GetOutputPort())
    spherePolyDataMapper.ScalarVisibilityOff()

    # Then we can create the actor using the mapper
    sphereActor = vtk.vtkActor()
    sphereActor.SetMapper(spherePolyDataMapper)
    sphereActor.GetProperty().SetOpacity(0.3)
    sphereActor.GetProperty().SetColor(UGLY_YELLOW)

    return [boxActor, boneActor, skinActor, sphereActor]


# This function returns the actors used to display the view with
# the "rainbow" bone, that represents distance to skin. (bottom-right in example).
def rainbow_knee_no_skin():
    # Reading or creating bone polydata that contains distances to skin.
    if os.path.exists(BONE_SAVE_FILE_NAME):

        # Reading bone polydata.
        bonePolyDataReader = vtk.vtkPolyDataReader()
        bonePolyDataReader.SetFileName(BONE_SAVE_FILE_NAME)
        bonePolyDataReader.ReadAllScalarsOn()
        bonePolyDataReader.Update()

        # Creating the bone mapper
        bonePolyDataMapper = vtk.vtkPolyDataMapper()
        bonePolyDataMapper.SetInputConnection(bonePolyDataReader.GetOutputPort())
        bonePolyDataMapper.SetScalarRange(bonePolyDataReader.GetOutput().GetScalarRange())
    else:

        # Computing the shortest distance of each vertex of the bone to the skin
        # https://kitware.github.io/vtk-examples/site/Cxx/PolyData/DistancePolyDataFilter/
        # Really time-consuming.
        distancePolyDataFilter = vtk.vtkDistancePolyDataFilter()
        distancePolyDataFilter.SignedDistanceOff()
        distancePolyDataFilter.SetInputConnection(0, boneContourFilter.GetOutputPort())
        distancePolyDataFilter.SetInputConnection(1, skinContourFilter.GetOutputPort())
        distancePolyDataFilter.Update()

        # Saving bone polydata for further usage.
        bonePolyDataWriter = vtk.vtkPolyDataWriter()
        bonePolyDataWriter.SetFileName(BONE_SAVE_FILE_NAME)
        bonePolyDataWriter.SetFileTypeToBinary()
        bonePolyDataWriter.SetInputConnection(distancePolyDataFilter.GetOutputPort())
        bonePolyDataWriter.Write()

        # Creating the bone mapper
        bonePolyDataMapper = vtk.vtkPolyDataMapper()
        bonePolyDataMapper.SetInputConnection(distancePolyDataFilter.GetOutputPort())
        bonePolyDataMapper.SetScalarRange(distancePolyDataFilter.GetOutput().GetScalarRange())

    # Making bone actor
    boneActor = vtk.vtkActor()
    boneActor.SetMapper(bonePolyDataMapper)

    return [boxActor, boneActor]


# ------------------------ VIEWPORTS -----------------------

# Setting the 2*2 grid of viewports. According to the following documentation:
# https://kitware.github.io/vtk-examples/site/Cxx/Visualization/MultipleViewports/

# Define viewport ranges.
xmins = [0.0, 0.5, 0.0, 0.5]
xmaxs = [0.5, 1.0, 0.5, 1.0]
ymins = [0.5, 0.5, 0.0, 0.0]
ymaxs = [1.0, 1.0, 0.5, 0.5]

# 0: top left, 1: top right, 2: bottom left, 3: bottom right
renBkg = [LIGHT_RED, LIGHT_GREEN, LIGHT_BLUE, LIGHT_GREY]

# Getting the actors to display in each view according to the previous functions.
renActors = [solid_knee_stripped_skin(),
             solid_knee_half_transparent_clipped_skin_invisible_sphere(),
             solid_knee_solid_clipped_skin_half_transparent_sphere(),
             rainbow_knee_no_skin()]

renderWindow = vtk.vtkRenderWindow()
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renderWindow)
interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

camera = vtk.vtkCamera()

# Creating each viewport, top left, top right, bottom left, bottom right
for i in range(0, 4):

    renderer = vtk.vtkRenderer()

    renderWindow.AddRenderer(renderer)
    renderer.SetViewport(xmins[i], ymins[i], xmaxs[i], ymaxs[i])

    # Share the camera between viewports.
    if i == 0:
        camera = renderer.GetActiveCamera()
        camera.SetPosition(0.0, -1.0, 0.0)
        camera.SetViewUp(0.0, 0.0, -1.0)
    else:
        renderer.SetActiveCamera(camera)

    for actor in renActors[i]:
        renderer.AddActor(actor)

    renderer.SetBackground(renBkg[i])
    renderer.ResetCamera()

# Displaying
renderWindow.SetWindowName(WINDOW_NAME)
renderWindow.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)

interactor.Initialize()
renderWindow.Render()
interactor.Start()
