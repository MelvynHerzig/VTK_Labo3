#!/usr/bin/env python
#
# Labo 3 from VTK.
#
# Goal: Displaying a knee in 4 different viewports with filters, contouring, clipping,and implicit functions.
#
# Authors: Forestier Quentin & Herzig Melvyn
#
# Date: 15.05.2022

import vtk
import os.path

SKIN_COLOR = [0.77, 0.61, 0.60]

colors = vtk.vtkNamedColors()

# Creating the knee actor. According to the following documentation:
# https://kitware.github.io/vtk-examples/site/Python/IO/ReadSLC/
reader = vtk.vtkSLCReader()
reader.SetFileName("vw_knee.slc")
reader.Update()

# Getting outline box

outliner = vtk.vtkOutlineFilter()
outliner.SetInputConnection(reader.GetOutputPort())
outliner.Update()

boxMapper = vtk.vtkPolyDataMapper()
boxMapper.SetInputConnection(outliner.GetOutputPort())

boxActor = vtk.vtkActor()
boxActor.SetMapper(boxMapper)
boxActor.GetProperty().SetColor([0.0, 0.0, 0.0])

# Getting skin
skinFilter = vtk.vtkContourFilter()
skinFilter.SetInputConnection(reader.GetOutputPort())
skinFilter.SetValue(0, 50)  # From tries

skinMapper = vtk.vtkPolyDataMapper()
skinMapper.SetInputConnection(skinFilter.GetOutputPort())
skinMapper.SetScalarVisibility(0)

skinActor = vtk.vtkActor()
skinActor.SetMapper(skinMapper)
skinActor.GetProperty().SetColor(SKIN_COLOR)

# Getting bone
boneFilter = vtk.vtkContourFilter()
boneFilter.SetInputConnection(reader.GetOutputPort())
boneFilter.SetValue(0, 72)  # From example

boneMapper = vtk.vtkPolyDataMapper()
boneMapper.SetInputConnection(boneFilter.GetOutputPort())
boneMapper.SetScalarVisibility(0)

boneActor = vtk.vtkActor()
boneActor.SetMapper(boneMapper)
boneActor.GetProperty().SetColor([0.90, 0.90, 0.90])


if os.path.exists("distances.vtk"):
    # Reading mesh
    boneReader = vtk.vtkPolyDataReader()
    boneReader.SetFileName("distances.vtk")
    boneReader.ReadAllScalarsOn()
    boneReader.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(boneReader.GetOutputPort())
    mapper.SetScalarRange(boneReader.GetOutput().GetScalarRange())
else:

    # https://kitware.github.io/vtk-examples/site/Cxx/PolyData/DistancePolyDataFilter/
    distanceFilter = vtk.vtkDistancePolyDataFilter()
    distanceFilter.SignedDistanceOff()
    distanceFilter.SetInputConnection(0, boneFilter.GetOutputPort())
    distanceFilter.SetInputConnection(1, skinFilter.GetOutputPort())
    distanceFilter.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(distanceFilter.GetOutputPort())
    mapper.SetScalarRange(distanceFilter.GetOutput().GetScalarRange())

    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName("distances.vtk")
    writer.SetFileTypeToBinary()
    writer.SetInputConnection(distanceFilter.GetOutputPort())
    writer.Write()

actor = vtk.vtkActor()
actor.SetMapper(mapper)


# ---------------- CLIPPING SPHERE IN SKIN ----------------

clipSphere = vtk.vtkSphere()
clipSphere.SetRadius(45)
clipSphere.SetCenter([70, 30, 100])

clip = vtk.vtkClipPolyData()
clip.SetClipFunction(clipSphere)
clip.SetInputConnection(skinFilter.GetOutputPort())

clipMapper = vtk.vtkPolyDataMapper()
clipMapper.SetInputConnection(clip.GetOutputPort())
clipMapper.ScalarVisibilityOff()

# ----------------------------------------------------------------

upperRightActor = vtk.vtkActor()
upperRightActor.SetMapper(clipMapper)
upperRightActor.GetProperty().SetColor(SKIN_COLOR)
upperRightActor.GetProperty().SetOpacity(0.5)
upperRightActor.SetBackfaceProperty(upperRightActor.MakeProperty())
upperRightActor.GetBackfaceProperty().SetColor(SKIN_COLOR)

lowerLeftActor = vtk.vtkActor()
lowerLeftActor.SetMapper(clipMapper)
lowerLeftActor.GetProperty().SetColor(SKIN_COLOR)


# Setting the 2*2 grid of viewports. According to the following documentation:
# https://kitware.github.io/vtk-examples/site/Cxx/Visualization/MultipleViewports/

# Define viewport ranges.
xmins = [0.0, 0.5, 0.0, 0.5]
xmaxs = [0.5, 1.0, 0.5, 1.0]
ymins = [0.5, 0.5, 0.0, 0.0]
ymaxs = [1.0, 1.0, 0.5, 0.5]

# Pink (top left), green (top right), blue (bottom left), grey (bottom right)
renBkg = [[1.0, 0.8, 0.8],
          [0.8, 1.0, 0.8],
          [0.8, 0.8, 1.0],
          [0.8, 0.8, 0.8]]

renActors = [[boxActor, boneActor, skinActor],
             [boxActor, boneActor, upperRightActor],
             [boxActor, boneActor, lowerLeftActor],
             [boxActor, actor]]

renWin = vtk.vtkRenderWindow()
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(renWin)
interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

camera = vtk.vtkCamera()

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

# Starting display
renWin.SetWindowName("MultipleViewPorts")
renWin.SetSize(800, 800)

interactor.Initialize()
renWin.Render()
interactor.Start()
