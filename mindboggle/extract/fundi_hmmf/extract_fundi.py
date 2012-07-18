#!/usr/bin/python
"""
Extract fundus curves from surface mesh patches (sulci).

Authors:
Yrjo Hame  .  yrjo.hame@gmail.com
Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np

from extract_sulci import extract_sulci
from compute_likelihood import compute_likelihood
from find_anchors import find_anchors
from connect_anchors import connect_anchors
from time import time

import sys
sys.path.append('/projects/mindboggle/mindboggle/mindboggle/utils/')
import io_vtk

#==================
# Extract all fundi
#==================
def extract_fundi(vertices, faces, depths, mean_curvatures, min_directions,
                  depth_threshold=0.2, thr=0.5, min_sulcus_size=50,
                  min_distance=5, max_distance=8):
    """
    Extract all fundi.

    A fundus is a connected set of high-likelihood vertices in a surface mesh.

    Inputs:
    ------
    vertices: [#vertices x 3] numpy array
    faces: vertices for polygons [#faces x 3] numpy array
    depths: depth values [#vertices x 1] numpy array
    mean_curvatures: mean curvature values [#vertices x 1] numpy array
    min_directions: directions of minimum curvature [3 x #vertices] numpy array
    depth_threshold: depth threshold for defining sulci
    thr: likelihood threshold
    min_sulcus_size: minimum sulcus size from which to find a fundus
    min_distance: minimum distance
    max_distance: maximum distance

    Output:
    ------
    fundi: list of #sulci lists of vertex indices.

    Calls:
    -----
    extract_sulci()
    compute_likelihood()
    find_anchors()
    connect_anchors()

    """

    import pickle
    load_path = "/drop/input/"
    load_em = 0
    save_em = 1

    # Extract sulci (vertex indices for each sulcus)
    if load_em:
        sulci = pickle.load(open(load_path + "sulci.p","rb"))
        n_sulci = int(pickle.load(open(load_path + "n_sulci.p","rb")))
        sulci_index_lists = pickle.load(open(load_path + "sulci_index_lists.p","rb"))
    else:
        print("Extract sulci from surface mesh...")
        t0 = time()
        sulci, n_sulci, sulci_index_lists = extract_sulci(faces, 
               depths, depth_threshold, min_sulcus_size)
        if save_em:
            pickle.dump(sulci, open(load_path + "sulci.p","wb"))
            pickle.dump(n_sulci, open(load_path + "n_sulci.p","wb"))
            pickle.dump(sulci_index_lists, open(load_path + "sulci_index_lists.p","wb"))

            sulci_indices = [x for lst in sulci_index_lists for x in lst]
            # Remove faces that do not contain three sulcus vertices
            fs = frozenset(sulci_indices)
            faces_sulci = [lst for lst in faces if len(fs.intersection(lst)) == 3]
            faces_sulci = np.reshape(np.ravel(faces_sulci), (-1, 3))
            print('  Reduced {} to {} faces.'.format(len(faces),
                                                     len(faces_sulci)))
            # Save vtk file
            sulci_for_vtk = sulci.copy()
            sulci_for_vtk[sulci == 0] = -1
            LUTs = [[int(x) for x in sulci_for_vtk]]
            LUT_names = ['sulcus'+str(i+1) for i in range(n_sulci)]
            io_vtk.writeSulci(load_path + 'sulci.vtk', vertices, sulci_indices,
                              faces_sulci, LUTs=LUTs, LUTNames=LUT_names)

    # For each sulcus...
    print("Extract a fundus from each of {} sulci...".format(n_sulci))
    fundi = []
    Z = np.zeros(len(depths))
    for i_sulcus, sulcus in enumerate(sulci_index_lists):

        # Compute fundus likelihood values
        print('  Compute fundus likelihood values for sulcus {}...'.
              format(i_sulcus + 1))
        t0 = time()
        sulcus_likelihoods = compute_likelihood(depths[sulcus],
                                                mean_curvatures[sulcus])
        print('    ...completed in {0:.2f} seconds'.
              format(time() - t0))

        # If the sulcus has enough high-likelihood vertices, continue
        print('{} {}'.format(sum(sulcus_likelihoods > thr),sum(sulcus_likelihoods > thr) > min_sulcus_size))
        if sum(sulcus_likelihoods > thr) > min_sulcus_size:

            # Find fundus points
            print('  Find fundus points for sulcus {}...'.format(i_sulcus + 1))
            t0 = time()
            anchors = find_anchors(vertices[sulcus, :], sulcus_likelihoods,
                                   min_directions[sulcus],
                                   thr, min_distance, max_distance)
            anchors = [sulcus[x] for x in anchors]
            print('    ...completed in {0:.2f} seconds'.format(time() - t0))
            if len(anchors) > 0:

                # Connect fundus points and extract fundus
                print('  Connect fundus points for sulcus {}...'.
                      format(i_sulcus + 1))
                t0 = time()
                likelihoods = Z.copy()
                likelihoods[sulcus] = sulcus_likelihoods
                fundi.append(
                      connect_anchors(anchors, faces, sulcus,
                                      likelihoods, thr))
                print('    ...completed in {0:.2f} seconds'.
                      format(time() - t0))
            else:
                fundi.append([])
        else:
            fundi.append([])

    if save_em:
        pickle.dump(likelihoods, open(load_path + "likelihoods.p","wb"))
        pickle.dump(fundi, open(load_path + "fundi.p","wb"))

        # Remove faces that do not contain three sulcus vertices
        sulci_indices = [x for lst in sulci_index_lists for x in lst]
        fs = frozenset(sulci_indices)
        faces_sulci = [lst for lst in faces if len(fs.intersection(lst)) == 3]
        faces_sulci = np.reshape(np.ravel(faces_sulci), (-1, 3))

        # Save sulcus likelihoods
        likelihoods_for_vtk = -np.ones(len(depth))
        likelihoods_for_vtk[sulci_indices] = likelihoods[sulci_indices]
        io_vtk.writeSulci(load_path + 'likelihoods.vtk', vertices,
                          sulci_indices, faces_sulci,
                          LUTs=[likelihoods_for_vtk], LUTNames=['sulcus likelihoods'])

        # Save fundi
        fundi_for_vtk = -np.ones(len(depths))
        for fundus in fundi:
            if len(fundus) > 0:
                fundi_for_vtk += fundus
        io_vtk.writeSulci(load_path + 'fundi.vtk', vertices,
                          sulci_indices, faces_sulci,
                          LUTs=[fundi_for_vtk], LUTNames=['fundi'])

    return fundi

import pickle
load_path = "/drop/input/"
load_em = 1
save_em = 1
if load_em:
    vertices = pickle.load(open(load_path + "vertices.p","rb"))
    faces = pickle.load(open(load_path + "faces.p","rb"))
    depths = pickle.load(open(load_path + "depths.p","rb"))
    mean_curvatures = pickle.load(open(load_path + "mean_curvatures.p","rb"))
    min_directions = pickle.load(open(load_path + "min_directions.p","rb"))
else:
    depth_file = load_path + 'lh.pial.depth.vtk'
    curv_file = load_path + 'lh.pial.curv.avg.vtk'
    dir_file = load_path + 'lh.pial.curv.min.dir.csv'
    vertices, faces, depths = io_vtk.load_VTK_Map(depth_file)
    vertices, faces, mean_curvatures = io_vtk.load_VTK_Map(curv_file)
    vertices = np.array(vertices)
    faces = np.array(faces)
    depths = np.array([x/max(depths) for x in depths])
    mean_curvatures = np.array(mean_curvatures)
    min_directions = np.loadtxt(dir_file)
    if save_em:
        pickle.dump(vertices, open(load_path + "vertices.p","wb"))
        pickle.dump(faces, open(load_path + "faces.p","wb"))
        pickle.dump(depths, open(load_path + "depths.p","wb"))
        pickle.dump(mean_curvatures, open(load_path + "mean_curvatures.p","wb"))
        pickle.dump(min_directions, open(load_path + "min_directions.p","wb"))

fundi = extract_fundi(vertices, faces, depths, mean_curvatures, min_directions,
    depth_threshold=0.2, thr=0.5, min_sulcus_size=50,
    min_distance=5, max_distance=8)

"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x, y, z = np.transpose(np.reshape([x for lst in p for x in lst], (-1, 3)))
ax.scatter(x, y, z)

v = np.transpose(np.reshape([x for lst in vertices for x in lst], (-1, 3)))
ax.scatter(v[0], v[1], v[2])

plt.show()
"""
