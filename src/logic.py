'''QT specific imports'''
from PyQt5 import QtCore, QtWidgets, QtGui

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

''' Other python module imports'''
import sys, cv2, math, os
from subprocess import  check_output, CalledProcessError, STDOUT

'''Local imports'''
from ui import Ui_MainWindow
from rdemo import Renderer, initialize_rendering, render_current_frame
import argparse
from collections import defaultdict
import pickle
import os


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    class CustomSpinBox(QDoubleSpinBox):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)


        sig = QtCore.pyqtSignal(str)

        def keyPressEvent(self, e):
            self.s_input_fetched, self.tx_input_fetched, self.ty_input_fetched = MyWindow.GetSpinBoxObject()

            if e.key() == 68:
                self.sig.emit("tx+")
            elif e.key() == 65:
                self.sig.emit("tx-")
            elif e.key() == 83:
                self.sig.emit("ty+")
            elif e.key() == 87:
                self.sig.emit("ty-")
            elif e.key() == 81:
                self.sig.emit("s+")
            elif e.key() == 69:
                self.sig.emit("s-")

            elif e.key() == 76:
                self.sig.emit("tx++")
            elif e.key() == 74:
                self.sig.emit("tx--")
            elif e.key() == 75:
                self.sig.emit("ty++")
            elif e.key() == 73:
                self.sig.emit("ty--")
            elif e.key() == 85:
                self.sig.emit("s++")
            elif e.key() == 79:
                self.sig.emit("s--")
            elif e.key() == 16777220:
                self.sig.emit("next")
            elif e.key() == 16777248:
                self.sig.emit("prev")

    '''DEFINE spinboxes manually for subclassing keypress'''
    s_input = None
    tx_input = None
    ty_input = None

    def __init__(self, *args, **kwargs):
        super(MyWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        '''SETUP spinboxes manually for subclassing keypress'''
        MyWindow.s_input = self.CustomSpinBox(self.centralwidget)
        MyWindow.s_input.setGeometry(QtCore.QRect(210, 440, 69, 31))
        MyWindow.s_input.setObjectName("s_input")
        MyWindow.tx_input = self.CustomSpinBox(self.centralwidget)
        MyWindow.tx_input.setGeometry(QtCore.QRect(350, 440, 69, 31))
        MyWindow.tx_input.setObjectName("tx_input")
        MyWindow.ty_input = self.CustomSpinBox(self.centralwidget)
        MyWindow.ty_input.setGeometry(QtCore.QRect(540, 440, 69, 31))
        MyWindow.ty_input.setObjectName("ty_input")

        '''SET VARIABLES'''
        self.x = 0
        self.m_fS = 0.0
        self.m_fTx = 0.0
        self.m_fTy = 0.0
        self.m_iFrameCounter = 0
        self.m_pixmapPix = None

        self.prev_button_offset = 0
        self.frame_info = "0/total"

        args = sys.argv[1:]
        frame_name = str(args[0])
        gender = str(args[1])
        model_folder = str(args[2])
        resume = str(args[3])

        if resume == 'resume':
            self.resume = True
        else:
            self.resume = False

        root_path = os.getcwd()
        dump_path = f"data/to_annotate/{frame_name}/annotate/cam_out.pkl"
        self.dump_path = os.path.join(root_path, dump_path)
        video_path = f"data/to_annotate/{frame_name}/{frame_name}.mp4"
        video_path = os.path.join(root_path,video_path )
        tcmr_output = f"data/to_annotate/{frame_name}/tcmr_output.pkl"
        tcmr_output = os.path.join(root_path, tcmr_output)
        annotated = f"data/to_annotate/{frame_name}/annotate/smplx_param.pkl"
        annotated = os.path.join(root_path, annotated)

        if self.resume:
            cam_out_path = f"data/to_annotate/{frame_name}/annotate/cam_out.pkl"
            assert(os.path.exists(cam_out_path))
        else:
            cam_out_path = None

        self.width, self.height, self.m_iTotalframes, self.all_frames, self.data, self.renderer, self.model, self.all_verts, self.faces = initialize_rendering(model_folder,  gender, video_path, tcmr_output, annotated, self.resume, cam_out_path)

        self.annot_cam = defaultdict(lambda: defaultdict(dict))
        if self.resume:
            self.annot_cam['cam'] = self.data

        self.resolution = (self.width, self.height)
        self.label_width = self.resolution[0]
        self.label_height = self.resolution[1]
        self.ratio =  self.width / self.height
        print("video width and height fetched: ", self.width, self.height)

        # set qlbael dimensions here
        self.display_label.setGeometry(QtCore.QRect(20, 20, self.label_width, self.label_height))

        '''SET QDoubleSpinBox initial values'''
        frame_cam = self.data[0]
        # print("default values :", frame_cam)
        self.m_fS = frame_cam[0]
        self.m_fTx = frame_cam[2]
        self.m_fTy = frame_cam[3]
        self.SetDoubleSpinBoxValues(self.s_input, 0.01, 5, self.m_fS)
        self.SetDoubleSpinBoxValues(self.tx_input, 0.01, 5, self.m_fTx)
        self.SetDoubleSpinBoxValues(self.ty_input,0.01, 5, self.m_fTy)

        # self.m_iTotalframes = len(self.all_frames)
        if self.m_iFrameCounter == 0:
            self.RenderFile(first_frame = True)

        '''SET EVENTS'''
        self.prev_button.clicked.connect(self.FetchPrevFrame)
        self.next_button.clicked.connect(self.FetchNextFrame)
        MyWindow.s_input.valueChanged.connect(self.ValueChange)
        MyWindow.tx_input.valueChanged.connect(self.ValueChange)
        MyWindow.ty_input.valueChanged.connect(self.ValueChange)
        self.dump_button.clicked.connect(self.dump_data)
        self.display_label.mousePressEvent = self.Getxy
        MyWindow.s_input.sig.connect(self.ReceiveSignal)
        MyWindow.tx_input.sig.connect(self.ReceiveSignal)
        MyWindow.ty_input.sig.connect(self.ReceiveSignal)

    @QtCore.pyqtSlot(str)
    def ReceiveSignal(self,val):
        if val == 'next':
            self.FetchNextFrame()
        elif val == 'prev':
            self.FetchPrevFrame()
        else:
            if val == 'tx++':
                self.m_fTx += 0.3
            if val == 'tx--':
                self.m_fTx -= 0.3
            if val == 'tx+':
                self.m_fTx += 0.02
            if val == 'tx-':
                self.m_fTx -= 0.02

            if val == 'ty++':
                self.m_fTy += 0.3
            if val == 'ty--':
                self.m_fTy -= 0.3
            if val == 'ty+':
                self.m_fTy += 0.02
            if val == 'ty-':
                self.m_fTy -= 0.02

            if val == 's++':
                self.m_fS += 0.05
            if val == 's--':
                self.m_fS -= 0.05

            if val == 's+':
                self.m_fS += 0.01
            if val == 's-':
                self.m_fS -= 0.01

            MyWindow.s_input.setValue(self.m_fS)
            MyWindow.tx_input.setValue(self.m_fTx)
            MyWindow.ty_input.setValue(self.m_fTy)
            self.RenderFile()

    @staticmethod
    def GetSpinBoxObject():
        return MyWindow.s_input, MyWindow.tx_input, MyWindow.ty_input

    def Getxy(self, event):
        x = event.pos().x()
        y = event.pos().y()

        self.m_fTx = 0.00611 * x - 1.96719
        self.m_fTy = 0.01028 * y - 1.78356

        # new_tx = 0.00611 * x - 1.96719
        MyWindow.s_input.setValue(self.m_fS)
        MyWindow.tx_input.setValue(self.m_fTx)
        MyWindow.ty_input.setValue(self.m_fTy)
        self.RenderFile()

    """
    def wheelEvent(self,event):
        self.x =self.x + event.angleDelta().y()/120
        print("wheel: ",self.x)
        delta = event.angleDelta().y()
        self.x += (delta and delta // abs(delta))
        print("wheel with abs: ",self.x)

    """

    def dump_data(self):
        if 0:
            pass
        else:

            self.annot_cam['width']  = self.width
            self.annot_cam['height']  = self.height
            self.annot_cam = dict(self.annot_cam)
            with open(self.dump_path, 'wb') as fi:
                pickle.dump( self.annot_cam, fi)
            print('Data dumped!!!')

    def ValueChange(self):
        changed = False
        if self.m_fS != MyWindow.s_input.value():
            self.m_fS = MyWindow.s_input.value()
            changed = True
        if self.m_fTx != MyWindow.s_input.value():
            self.m_fTx = MyWindow.tx_input.value()
            changed = True
        if self.m_fTy != MyWindow.s_input.value():
            self.m_fTy = MyWindow.ty_input.value()
            changed = True
        if changed == True:
            self.RenderFile()

    def SetDoubleSpinBoxValues(self, object_name, step, decimal, initial_val):
        object_name.setDecimals(decimal)
        object_name.setRange(-100.0,100.0)
        object_name.setValue(initial_val)
        object_name.setSingleStep(step)

    def FetchPrevFrame(self):

        sx, sy, tx, ty = self.get_parameters()
        self.m_iFrameCounter -= 1
        if self.m_iFrameCounter < 0:
            print("resetting frame from ", self.m_iFrameCounter," to 0")
            self.m_iFrameCounter = 0

        self.SetDoubleSpinBoxValues(self.s_input, 0.01, 5, sx)
        self.SetDoubleSpinBoxValues(self.tx_input, 0.01, 5, tx)
        self.SetDoubleSpinBoxValues(self.ty_input,0.01, 5, ty)
        self.RenderFile()

    def FetchNextFrame(self):
        sx, sy, tx, ty = self.get_parameters()
        self.m_iFrameCounter += 1

        if self.m_iFrameCounter > self.m_iTotalframes - 1:
            print("resetting frame from ", self.m_iFrameCounter," to ", self.m_iTotalframes)
            self.m_iFrameCounter = self.m_iTotalframes - 1


        self.SetDoubleSpinBoxValues(self.s_input, 0.01, 5, sx)
        self.SetDoubleSpinBoxValues(self.tx_input, 0.01, 5, tx)
        self.SetDoubleSpinBoxValues(self.ty_input,0.01, 5, ty)
        self.RenderFile()

    def get_parameters_resume(self):
        if self.annotate.isChecked():
            sx = self.m_fS
            sy = sx * self.ratio
            tx = self.m_fTx
            ty = self.m_fTy
        else:
            if len(self.annot_cam['cam'][self.m_iFrameCounter]) != 0:
                sx, sy, tx, ty = self.annot_cam['cam'][self.m_iFrameCounter]
                MyWindow.s_input.setValue(sx)
                MyWindow.tx_input.setValue(tx)
                MyWindow.ty_input.setValue(ty)
            else:
                sx = self.m_fS
                sy = sx * self.ratio
                tx = self.m_fTx
                ty = self.m_fTy
                MyWindow.s_input.setValue(sx)
                MyWindow.tx_input.setValue(tx)
                MyWindow.ty_input.setValue(ty)
        return sx, sy, tx, ty

    def get_parameters(self, first_frame = False):
        if self.resume:
            if not self.annotate.isChecked():
                if len(self.annot_cam['cam'][self.m_iFrameCounter]) != 0:
                    sx, sy, tx, ty = self.annot_cam['cam'][self.m_iFrameCounter]
                    MyWindow.s_input.setValue(sx)
                    MyWindow.tx_input.setValue(tx)
                    MyWindow.ty_input.setValue(ty)
                else:
                    sx = self.m_fS
                    sy = sx * self.ratio
                    tx = self.m_fTx
                    ty = self.m_fTy
                    MyWindow.s_input.setValue(sx)
                    MyWindow.tx_input.setValue(tx)
                    MyWindow.ty_input.setValue(ty)
            elif self.annotate.isChecked():
                sx = self.m_fS
                sy = sx * self.ratio
                tx = self.m_fTx
                ty = self.m_fTy
        else:
            if first_frame:
                frame_cam = self.data[self.m_iFrameCounter]
                tx = frame_cam[2]
                ty = frame_cam[3]
                sx = frame_cam[0]
                sy = sx * self.ratio
            else:
                if self.annotate.isChecked():
                    sx = self.m_fS
                    sy = sx * self.ratio
                    tx = self.m_fTx
                    ty = self.m_fTy
                else:
                    if len(self.annot_cam['cam'][self.m_iFrameCounter]) != 0:
                        sx, sy, tx, ty = self.annot_cam['cam'][self.m_iFrameCounter]
                        MyWindow.s_input.setValue(sx)
                        MyWindow.tx_input.setValue(tx)
                        MyWindow.ty_input.setValue(ty)
                    else:
                        sx = self.m_fS
                        sy = sx * self.ratio
                        tx = self.m_fTx
                        ty = self.m_fTy
                        MyWindow.s_input.setValue(sx)
                        MyWindow.tx_input.setValue(tx)
                        MyWindow.ty_input.setValue(ty)
        return sx, sy, tx, ty

    def RenderFile(self, first_frame = False):
        if 1:
            i = self.m_iFrameCounter
            frame_cam = self.get_parameters(first_frame = first_frame)
            verts = self.all_verts[i]
            frame = self.all_frames[i]
            self.curr_img, self.curr_mask = render_current_frame(self.resolution, frame, frame_cam, self.renderer, self.model, verts, self.faces)
            new_img = QImage(self.curr_img, self.curr_img.shape[1], self.curr_img.shape[0], QImage.Format_RGB888)
            self.m_pixmapPix = QPixmap.fromImage(new_img)
            self.m_pixmapPix = self.m_pixmapPix.scaled(self.label_width, self.label_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.display_label.setPixmap(self.m_pixmapPix)
            self.frame_info = str(i) + "/" + str(self.m_iTotalframes)
            self.frame_info_label.setText(self.frame_info)

            if self.annotate.isChecked():
                self.annot_cam['cam'][i] = frame_cam
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Empty")
            msg.setText("Render file not available")
            msg.setIcon(QMessageBox.Warning)
            x = msg.exec_()

def main():
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
