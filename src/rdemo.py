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

        # rgb = cv2.resize(rgb, (img.shape[1], img.shape[0]))
        valid_mask = (rgb[:, :, -1] > 0)[:, :, np.newaxis]
        output_img = rgb[:, :, :-1] * valid_mask + (1 - valid_mask) * img
        image = output_img.astype(np.uint8)
        valid_mask = valid_mask.astype(np.uint8)

        self.scene.remove_node(mesh_node)
        self.scene.remove_node(cam_node)
        return image, valid_mask

def render_current_frame(resolution, frame, frame_cam, renderer, model, frame_verts, faces):
    img, mask = renderer.render( frame, frame_verts, faces, cam=frame_cam, mesh_filename=None)
    return img, mask

def initialize_rendering(model_folder,  gender, video_path, tcmr_output, annotated, resume, cam_out_path):
    if not resume:
        data = joblib.load(tcmr_output)[1]['orig_cam']
    else:
        data = joblib.load(cam_out_path)['cam']

    with open(annotated, 'rb') as fi:
        ad = pickle.load(fi)

    model = smplx.create(model_folder, create_global_orient = True, create_body_pose = True, create_betas = True, create_left_hand_pose = True, create_right_hand_pose = True, model_type='smplx', gender='male', num_betas = 10, use_pca = False)

    cap = cv2.VideoCapture(video_path)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1

    all_poses = ad['pose']
    all_betas = ad['beta']

    resize = False
    if width > 640:
        resize = True
        width = width // 2
        height = height // 2
        if width > 640:
            width = width // 2
            height = height // 2

    renderer = Renderer(resolution=(width, height), orig_img=True, wireframe=False)

    all_frames = []
    all_verts = []

    for i in trange(frame_count):
        pose = all_poses[i][3:66]
        betas = all_betas[i]
        global_orient = all_poses[i][:3]
        ret, frame = cap.read()
        if resize:
            frame = cv2.resize(frame, (int(width), int(height)))
        all_frames.append(frame[..., ::-1])
        pose = torch.tensor(pose).unsqueeze(0).float()
        betas  = torch.tensor(betas.T).float()
        left_hand_pose = torch.tensor(all_poses[i][75:120]).float()
        right_hand_pose = torch.tensor(all_poses[i][120:165]).float()
        go = torch.tensor(global_orient).unsqueeze(0).float()
        out = model(global_orient = go, body_pose = pose, betas = betas, left_hand_pose = left_hand_pose, right_hand_pose = right_hand_pose)
        frame_verts = out.vertices[0].detach().numpy()
        all_verts.append(frame_verts)
    return width, height, frame_count, all_frames, data, renderer, model, all_verts, model.faces
