# http://www.vtk.org/Wiki/VTK/Tutorials/CMakeListsFile
cmake_minimum_required(VERSION 3.0)
project(mindboggle_surfaces)
## Rather than set the VTK_DIR, compile with
## "cmake .. -DVTK_DIR:STRING=/Users/arno/anaconda/lib/cmake/vtk-7.0"
#set(VTK_DIR "/Users/arno/anaconda/lib/cmake/vtk-7.0")
#find_package(VTK REQUIRED NO_MODULE)
find_package(VTK 7.0 COMPONENTS vtkInteractionStyle vtkRenderingFreeType vtkRenderingOpenGL2 vtkRenderingVolumeOpenGL2 NO_MODULE)
include(${VTK_USE_FILE})

#if(COMMAND CMAKE_POLICY)
#  CMAKE_POLICY(SET CMP0003 NEW)
#endif(COMMAND CMAKE_POLICY)

# David Gobbi on vtkusers mailing list:
# For building a binary package to share with others,
# set to a reasonably old deployment target (e.g. 10.7) and SDK (e.g. 10.9):
#set(CMAKE_OSX_DEPLOYMENT_TARGET "10.7")
#set(CMAKE_OSX_SYSROOT "macosx10.9")

add_subdirectory(
travel_depth
)

add_subdirectory(
curvature
)

add_subdirectory(
surface_overlap
)

add_subdirectory(
area
)

add_subdirectory(
gradient
)

add_subdirectory(
geodesic_depth
)

#add_subdirectory(
#medial_surfaces
#)

add_library(
MeshAnalyser MeshAnalyser.cpp
)
install(TARGETS MeshAnalyser
        LIBRARY DESTINATION /lib
        ARCHIVE DESTINATION /lib)

add_library(
FsSurfaceReader FsSurfaceReader.cpp
)

add_library(
VtkFileEditor VtkFileEditor.cpp
)

add_library(
TravelDepth TravelDepth.cpp
)

add_library(
Overlap Overlap.cpp
)

add_library(
GradientComputer GradientComputer.cpp
)

add_library(
PointAreaComputer PointAreaComputer.cpp
)

target_link_libraries(
MeshAnalyser
)

target_link_libraries(
TravelDepth
)

target_link_libraries(
GradientComputer
)

target_link_libraries(
Overlap
PointAreaComputer
)
