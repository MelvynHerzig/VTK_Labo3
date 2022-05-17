#!/usr/bin/env python
#
# Labo 3 from VTK.
#
# Goal: Displaying a knee in 4 different viewports with filters, contouring, clipping and different effects.
#
# Authors: Forestier Quentin & Herzig Melvyn
#
# Date: 15.05.2022

import vtk
import os.path

# --------------------------- CONSTANTS ---------------------------

SKIN_COLOR = [0.77, 0.61, 0.60]

BONE_SAVE_FILE_NAME = "bone_save.vtk"

LIGHT_RED = [1.0, 0.8, 0.8]
LIGHT_GREEN = [0.8, 1.0, 0.8]
LIGHT_BLUE = [0.8, 0.8, 1.0]
LIGHT_GREY = [0.8, 0.8, 0.8]

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
WINDOW_NAME = "MultipleViewPorts"

# ------------------------ GENERAL ELEMENTS -----------------------
# mostly topologies

colors = vtk.vtkNamedColors()

# Reading the knee slc file.
# https://kitware.github.io/vtk-examples/site/Python/IO/ReadSLC/
reader = vtk.vtkSLCReader()
reader.SetFileName("vw_knee.slc")
reader.Update()

# Getting the outline box actor used in each viewports
outliner = vtk.vtkOutlineFilter()
outliner.SetInputConnection(reader.GetOutputPort())
outliner.Update()

boxMapper = vtk.vtkPolyDataMapper()
boxMapper.SetInputConnection(outliner.GetOutputPort())

boxActor = vtk.vtkActor()
boxActor.SetMapper(boxMapper)
boxActor.GetProperty().SetColor([0.0, 0.0, 0.0])

# Getting skin topology
skinFilter = vtk.vtkContourFilter()
skinFilter.SetInputConnection(reader.GetOutputPort())
skinFilter.SetValue(0, 50)  # From tries

# Getting clipped skin mapper
sphere = vtk.vtkSphere()
sphere.SetRadius(45)
sphere.SetCenter([70, 30, 100])

clippedSkin = vtk.vtkClipPolyData()
clippedSkin.SetClipFunction(sphere)
clippedSkin.SetInputConnection(skinFilter.GetOutputPort())

clippedSkinMapper = vtk.vtkPolyDataMapper()
clippedSkinMapper.SetInputConnection(clippedSkin.GetOutputPort())
clippedSkinMapper.ScalarVisibilityOff()

# Getting bone actor
boneFilter = vtk.vtkContourFilter()
boneFilter.SetInputConnection(reader.GetOutputPort())
boneFilter.SetValue(0, 72)  # From example

boneMapper = vtk.vtkPolyDataMapper()
boneMapper.SetInputConnection(boneFilter.GetOutputPort())
boneMapper.SetScalarVisibility(0)

boneActor = vtk.vtkActor()
boneActor.SetMapper(boneMapper)
boneActor.GetProperty().SetColor([0.90, 0.90, 0.90])


def solid_knee_half_transparent_clipped_skin_invisible_sphere():
    # Skin actor with front face half transparent and back face not transparent
    skinActor = vtk.vtkActor()
    skinActor.SetMapper(clippedSkinMapper)
    skinActor.GetProperty().SetColor(SKIN_COLOR)
    skinActor.GetProperty().SetOpacity(0.5)
    skinActor.SetBackfaceProperty(skinActor.MakeProperty())
    skinActor.GetBackfaceProperty().SetColor(SKIN_COLOR)

    return [boxActor, boneActor, skinActor]


def solid_knee_solid_clipped_skin_half_transparent_sphere():
    # Skin actor
    skinActor = vtk.vtkActor()
    skinActor.SetMapper(clippedSkinMapper)
    skinActor.GetProperty().SetColor(SKIN_COLOR)

    return [boxActor, boneActor, skinActor]


def rainbow_knee_no_skin():
    # Reading or creating distances vtk file for bone vertices to the nearest skin vertex
    if os.path.exists(BONE_SAVE_FILE_NAME):

        # Reading bone polydata with distances
        boneReader = vtk.vtkPolyDataReader()
        boneReader.SetFileName(BONE_SAVE_FILE_NAME)
        boneReader.ReadAllScalarsOn()
        boneReader.Update()

        # Creating the bone mapper
        boneMapper = vtk.vtkPolyDataMapper()
        boneMapper.SetInputConnection(boneReader.GetOutputPort())
        boneMapper.SetScalarRange(boneReader.GetOutput().GetScalarRange())
    else:

        # Computing the shortest distance each vertex of the bone to the skin
        # https://kitware.github.io/vtk-examples/site/Cxx/PolyData/DistancePolyDataFilter/
        distanceFilter = vtk.vtkDistancePolyDataFilter()
        distanceFilter.SignedDistanceOff()
        distanceFilter.SetInputConnection(0, boneFilter.GetOutputPort())
        distanceFilter.SetInputConnection(1, skinFilter.GetOutputPort())
        distanceFilter.Update()

        # Saving bone polydata with distances for further usage.
        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(BONE_SAVE_FILE_NAME)
        writer.SetFileTypeToBinary()
        writer.SetInputConnection(distanceFilter.GetOutputPort())
        writer.Write()

        # Creating the bone mapper
        boneMapper = vtk.vtkPolyDataMapper()
        boneMapper.SetInputConnection(distanceFilter.GetOutputPort())
        boneMapper.SetScalarRange(distanceFilter.GetOutput().GetScalarRange())

    # Making bone actor
    boneActor = vtk.vtkActor()
    boneActor.SetMapper(boneMapper)

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

renActors = [solid_knee_half_transparent_clipped_skin_invisible_sphere(),
             solid_knee_half_transparent_clipped_skin_invisible_sphere(),
             solid_knee_solid_clipped_skin_half_transparent_sphere(),
             rainbow_knee_no_skin()]

renWin = vtk.vtkRenderWindow()
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renWin)
interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

camera = vtk.vtkCamera()

# Creating each viewport, top left, top right, bottom left, bottom right
for i in range(0, 4):

    renderer = vtk.vtkRenderer()

    renWin.AddRenderer(renderer)
    renderer.SetViewport(xmins[i], ymins[i], xmaxs[i], ymaxs[i])

    # Share the camera between viewports.
    if i == 0:
        camera = renderer.GetActiveCamera()
        camera.Azimuth(30)
        camera.Elevation(30)
    else:
        renderer.SetActiveCamera(camera)

    for actor in renActors[i]:
        renderer.AddActor(actor)

    renderer.SetBackground(renBkg[i])
    renderer.ResetCamera()

# Displaying
renWin.SetWindowName(WINDOW_NAME)
renWin.SetSize(WINDOW_WIDTH, WINDOW_HEIGHT)

interactor.Initialize()
renWin.Render()
interactor.Start()
