# os.environ['PYOPENGL_PLATFORM'] = 'egl'
import pyrender
import cv2
import time
import torch
import joblib
import trimesh
import pickle
import math
import shutil
import colorsys
import matplotlib.pyplot as plt
import argparse
from tqdm import tqdm, trange
import joblib
import random
import numpy as np
from pathlib import Path
from tqdm import tqdm
from lib.models.smpl import SMPL, SMPL_MODEL_DIR
from lib.models.smpl import get_smpl_faces

from pyrender.constants import RenderFlags

class WeakPerspectiveCamera(pyrender.Camera):
    def __init__(self,
                 scale,
                 translation,
                 znear=pyrender.camera.DEFAULT_Z_NEAR,
                 zfar=None,
                 name=None):
        super(WeakPerspectiveCamera, self).__init__(
            znear=znear,
            zfar=zfar,
            name=name,
        )
        self.scale = scale
        self.translation = translation

    def get_projection_matrix(self, width=None, height=None):
        P = np.eye(4)
        P[0, 0] = self.scale[0]
        P[1, 1] = self.scale[1]
        P[0, 3] = self.translation[0] * self.scale[0]
        P[1, 3] = -self.translation[1] * self.scale[1]
        P[2, 2] = -1
        return P

class Renderer:
    def __init__(self, resolution=(224,224), orig_img=False, wireframe=False):
        self.resolution = resolution

        self.faces = get_smpl_faces()
        self.orig_img = orig_img
        self.wireframe = wireframe
        self.renderer = pyrender.OffscreenRenderer(
            viewport_width=self.resolution[0],
            viewport_height=self.resolution[1],
            point_size=1.0
        )

        # set the scene
        self.scene = pyrender.Scene(bg_color=[0.0, 0.0, 0.0, 0.0], ambient_light=(0.3, 0.3, 0.3))

        # light = pyrender.PointLight(color=[1.0, 1.0, 1.0], intensity=0.8)
        light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=0.8)

        light_pose = np.eye(4)
        light_pose[:3, 3] = [0, -1, 1]
        self.scene.add(light, pose=light_pose)

        light_pose[:3, 3] = [0, 1, 1]
        self.scene.add(light, pose=light_pose)

        light_pose[:3, 3] = [1, 1, 2]
        self.scene.add(light, pose=light_pose)

    def render(self, img, verts, cam, angle=None, axis=None, mesh_filename=None, color=[1.0, 1.0, 0.9], rotate=False):
        mesh = trimesh.Trimesh(vertices=verts, faces=self.faces, process=False)

        Rx = trimesh.transformations.rotation_matrix(math.radians(180), [1, 0, 0])
        mesh.apply_transform(Rx)

        if rotate:
            rot = trimesh.transformations.rotation_matrix(
                np.radians(60), [0, 1, 0])
            mesh.apply_transform(rot)

        if mesh_filename is not None:
            mesh.export(mesh_filename)

        if angle and axis:
            R = trimesh.transformations.rotation_matrix(math.radians(angle), axis)
            mesh.apply_transform(R)

        sx, sy, tx, ty = cam

        # sx = 1
        # sy = 1
        # tx = 0
        # ty =  0
        camera = WeakPerspectiveCamera(
            scale=[sx, sy],
            translation=[tx, ty],
            zfar=1000.
        )


        material = pyrender.MetallicRoughnessMaterial(
            metallicFactor=0.0,
            alphaMode='OPAQUE',
            smooth=True,
            wireframe=True,
            roughnessFactor=1.0,
            emissiveFactor=(0.1, 0.1, 0.1),
            baseColorFactor=(color[0], color[1], color[2], 1.0)
        )

        mesh = pyrender.Mesh.from_trimesh(mesh, material=material)

        mesh_node = self.scene.add(mesh, 'mesh')

        camera_pose = np.eye(4)
        cam_node = self.scene.add(camera, pose=camera_pose)

        if self.wireframe:
            render_flags = RenderFlags.RGBA | RenderFlags.ALL_WIREFRAME
        else:
            render_flags = RenderFlags.RGBA

        rgb, _ = self.renderer.render(self.scene, flags=render_flags)

        # plt.imshow(rgb) ;plt.show()

        valid_mask = (rgb[:, :, -1] > 0)[:, :, np.newaxis]

        output_img = rgb[:, :, :-1] * valid_mask + (1 - valid_mask) * img
        image = output_img.astype(np.uint8)

        self.scene.remove_node(mesh_node)
        self.scene.remove_node(cam_node)

        return image, valid_mask

if __name__ == '__main__':

    frame_name  = 'abhi'
    gender = 'male'
    video_path = f"/home/ady/CVIT/annotation_3d-main_003/annotation_3d-main/data/to_annotate/{frame_name}/{frame_name}.mp4"
    tcmr_output = f"/home/ady/CVIT/annotation_3d-main_003/annotation_3d-main/data/to_annotate/{frame_name}/tcmr_output.pkl"
    annotated = f"/home/ady/CVIT/annotation_3d-main_003/annotation_3d-main/data/to_annotate/{frame_name}/annotate/smplx_param.pkl"

    data = joblib.load(tcmr_output)[1]
    with open(annotated, 'rb') as fi:
        ad = pickle.load(fi)

    model = SMPL( SMPL_MODEL_DIR, batch_size=1, create_transl=False, gender= gender)

    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # _fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    _fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    video_out = cv2.VideoWriter('outpy.avi', _fourcc, 30, (1080,1920))
    all_poses = ad['pose']
    all_betas = ad['beta']

    for i in trange(frame_count):
        frame_cam = data['orig_cam'][i]
        pose = torch.tensor(all_poses[i][3:72]).unsqueeze(0).float()
        betas  = torch.tensor(all_betas[i]).unsqueeze(0).float()
        go = torch.tensor(data['pose'][i][:3]).unsqueeze(0).float()
        out = model(global_orient = go, body_pose = pose, betas = betas[..., -1])
        frame_verts = out.vertices[0].detach().numpy()
        ret, frame = cap.read()

        if ret:
            height = frame.shape[0]
            width = frame.shape[1]
            renderer = Renderer(resolution=(width, height), orig_img=True, wireframe=False)
            img, mask = renderer.render( frame[..., ::-1], frame_verts, cam=frame_cam, mesh_filename=None,)
            video_out.write(img)
            # cv2.imshow('', img)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            plt.imshow(img)
            plt.show()
            # cv2.imshow('', img)

    cap.release()
    video_out.release()
    cv2.destroyAllWindows()



