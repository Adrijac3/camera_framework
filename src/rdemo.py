# os.environ['PYOPENGL_PLATFORM'] = 'egl'
import pyrender
import cv2
import time
import torch
import joblib
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
# from smpl import SMPL, SMPL_MODEL_DIR
# from smpl import get_smpl_faces
from pyrender.constants import RenderFlags
import smplx
import trimesh

class WeakPerspectiveCamera(pyrender.Camera):
    def __init__(self, scale, translation, znear=pyrender.camera.DEFAULT_Z_NEAR, zfar=None, name=None):
        super(WeakPerspectiveCamera, self).__init__( znear=znear, zfar=zfar, name=name,)
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

        self.orig_img = orig_img
        self.wireframe = wireframe
        self.renderer = pyrender.OffscreenRenderer( viewport_width=self.resolution[0], viewport_height=self.resolution[1], point_size=1.0)

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

    def render(self, img, verts, faces, cam, angle=None, axis=None, mesh_filename=None, color=[1.0, 1.0, 0.9], rotate=False):
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False, maintain_order = True)
        Rx = trimesh.transformations.rotation_matrix(math.radians(180), [1, 0, 0])
        mesh.apply_transform(Rx)

        sx, sy, tx, ty = cam
        camera = WeakPerspectiveCamera( scale=[sx, sy], translation=[tx, ty], zfar=1000.)

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

        rgb = cv2.resize(rgb, (img.shape[1], img.shape[0]))
        valid_mask = (rgb[:, :, -1] > 0)[:, :, np.newaxis]
        output_img = rgb[:, :, :-1] * valid_mask + (1 - valid_mask) * img
        image = output_img.astype(np.uint8)
        valid_mask = valid_mask.astype(np.uint8)

        # image = rgb.astype(np.uint8)
        self.scene.remove_node(mesh_node)
        self.scene.remove_node(cam_node)
        return image, valid_mask

def render_current_frame(ret, frame, frame_cam, renderer, model, pose, betas, global_orient):
    pose = torch.tensor(pose).unsqueeze(0).float()
    betas  = torch.tensor(betas.T).float()

    go = torch.tensor(global_orient).unsqueeze(0).float()

    out = model(global_orient = go, body_pose = pose, betas = betas)

    frame_verts = out.vertices[0].detach().numpy()
    faces = model.faces

    """
    TO dump the image
    """
    # pelvis = out.joints[0][0].detach().numpy()
    # frame_verts = frame_verts -  pelvis

    # mesh = trimesh.Trimesh(vertices=frame_verts, faces=faces, process=False, maintain_order = True)
    # Rx = trimesh.transformations.rotation_matrix(math.radians(180), [1, 0, 0])
    # mesh.apply_transform(Rx)

    # frame_verts = mesh.vertices + pelvis

    if ret:
        frame = cv2.resize(frame[..., ::-1], (640, 360))
        img, mask = renderer.render( frame, frame_verts, faces, cam=frame_cam, mesh_filename=None,)

    return img, mask


def initialize_rendering(frame_name, gender, video_path, tcmr_output, annotated):
    data = joblib.load(tcmr_output)[1]

    # with open(tcmr_output, 'rb') as fi:
    #     data = pickle.load(fi)

    with open(annotated, 'rb') as fi:
        ad = pickle.load(fi)


    # model = SMPL( SMPL_MODEL_DIR, batch_size=1, create_transl=False, gender= gender)
    model_folder = '/Users/coreqode/Desktop/00.00-ObsUniv/99-GR/smplx/models'
    model = smplx.create(model_folder, create_global_orient = True, create_body_pose = True, create_betas = True, model_type='smplx', gender='male', num_betas = 10)

    cap = cv2.VideoCapture(video_path)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    all_poses = ad['pose']
    all_betas = ad['beta']

    renderer = Renderer(resolution=(640, 360), orig_img=True, wireframe=False)

    all_frames = []
    all_frames = [cap.read() for i in range(frame_count)]
    return width, height, frame_count, all_frames, all_poses, all_betas, data, renderer, model

if __name__ == '__main__':
    width, height, frame_count, all_frames, all_poses, all_betas, data, renderer, model= initialize_rendering()
    for i in trange(frame_count):
        pose = all_poses[i][3:]
        print(pose.shape)
        betas = all_betas[i]
        # global_orient = data['pose'][i][:3]
        global_orient = all_poses[i][:3]
        frame_cam = data['orig_cam'][i]
        ret, frame = all_frames[i]
        img, mask = render_current_frame(ret, frame, frame_cam, renderer, model, pose, betas, global_orient)


        plt.imshow(img)
        plt.show()

