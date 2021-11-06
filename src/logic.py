'''QT specific imports'''
from PyQt5 import QtCore, QtWidgets, QtGui
# from PyQt5.QtWidgets import QMessageBox, QDialog, QLabel, QApplication, QWidget
# from PyQt5.QtGui  import QPixmap, QImage, QColor

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

''' Other python module imports'''
import sys, cv2, math, os
from subprocess import  check_output, CalledProcessError, STDOUT

'''Local imports'''
from ui import Ui_MainWindow
from rdemo import Renderer, initialize_rendering, render_current_frame


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    class CustomSpinBox(QDoubleSpinBox):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        sig = QtCore.pyqtSignal(str)

        def keyPressEvent(self, e):
            self.s_input_fetched, self.tx_input_fetched, self.ty_input_fetched = MyWindow.GetSpinBoxObject()

            # check_s = self.s_input_fetched.hasFocus()
            # check_tx = self.tx_input_fetched.hasFocus()
            # check_ty = self.ty_input_fetched.hasFocus()

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

           # if check_s == True:
            # if check_tx == True:
            #     if e.key() == 16777236:
            #         print("signal render function with tx value increased by 1 step")
            #         self.sig.emit("tx+")
            #     elif e.key() == 16777234:
            #         print("signal render function with ty value decreased by 1 step")
            #         self.sig.emit("tx-")
            # if check_ty == True:
            #     if e.key() == 16777236:
            #         print("signal render function with tx value increased by 1 step")
            #         self.sig.emit("ty+")
            #     elif e.key() == 16777234:
            #         print("signal render function with ty value decreased by 1 step")
            #         self.sig.emit("ty-")
            # if e.key() == 16777216:
            #     sys.exit()
            # if e.key() != 16777234 and e.key() != 16777236:
            #     return super().keyPressEvent(e)

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
        # self.m_sVideo_path = None
        frame_name  = 'abhi'
        gender = 'male'
        self.label_width = 640
        self.label_height = 360
        self.prev_button_offset = 0
        self.frame_info = "0/total"
        self.dump_path = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/Archive/{frame_name}/camera_parameters_annot.pkl"
        video_path = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/{frame_name}.mp4"
        tcmr_output = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/tcmr_output.pkl"
        annotated = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/annotate/smplx_param.pkl"

        # video_path = f"../data/{frame_name}/{frame_name}.mp4"
        # tcmr_output = f"../data/{frame_name}/tcmr_output.pkl"
        # annotated = f"../data/{frame_name}/annotate/smplx_param.pkl"

        self.width, self.height, self.m_iTotalframes, self.all_frames, self.all_poses, self.all_betas, self.data, self.renderer, self.model = initialize_rendering(frame_name, gender, video_path, tcmr_output, annotated)

        self.ratio =  self.width / self.height
        print("video width and height fetched: ", self.width, self.height)

        # set qlbael dimensions here
        self.display_label.setGeometry(QtCore.QRect(20, 20, self.label_width, self.label_height))

        '''SET QDoubleSpinBox initial values'''
        frame_cam = self.data['orig_cam'][0]
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
        print("signal received: ", val)
        if val == 'tx++':
            self.m_fTx += 0.1
        if val == 'tx--':
            self.m_fTx -= 0.1
        if val == 'tx+':
            self.m_fTx += 0.02
        if val == 'tx-':
            self.m_fTx -= 0.02

        if val == 'ty++':
            self.m_fTy += 0.1
        if val == 'ty--':
            self.m_fTy -= 0.1
        if val == 'ty+':
            self.m_fTy += 0.02
        if val == 'ty-':
            self.m_fTy -= 0.02

        if val == 's+':
            self.m_fS += 0.02
        if val == 's-':
            self.m_fS -= 0.02
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

        # smpl_pos_x, smpl_pos_y = self.get_smpl_current_location()
        # change_x = x - smpl_pos_x
        # change_y = y - smpl_pos_y
        # if using smplx_mid_point

        self.m_fTx = 0.00611 * x - 1.96719
        self.m_fTy = 0.01028 * y - 1.78356
        # new_tx = 0.00611 * x - 1.96719
        MyWindow.s_input.setValue(self.m_fS)
        MyWindow.tx_input.setValue(self.m_fTx)
        MyWindow.ty_input.setValue(self.m_fTy)
        self.RenderFile()


    def wheelEvent(self,event):
        self.x =self.x + event.angleDelta().y()/120
        print("wheel: ",self.x)
        delta = event.angleDelta().y()
        self.x += (delta and delta // abs(delta))
        print("wheel with abs: ",self.x)

    def dump_data(self):
        if 0:
            pass
        else:
            with open(self.dump_path, 'wb') as fi:
                pickle.dump( self.data, fi)
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
        # object_name.setMinimum(min_val)
        # object_name.setMaximum(max_val)
        object_name.setSingleStep(step)
        # object_name.setKeyboardTracking(False)

    def FetchPrevFrame(self):
        self.data['orig_cam'][self.m_iFrameCounter] = self.get_parameters()
        self.m_iFrameCounter -= 1

        if self.m_iFrameCounter < 0:
            print("resetting frame from ", self.m_iFrameCounter," to 0")
            self.m_iFrameCounter = 0

        frame_cam = self.data['orig_cam'][self.m_iFrameCounter]

        self.SetDoubleSpinBoxValues(self.s_input, 0.01, 5, self.m_fS)
        self.SetDoubleSpinBoxValues(self.tx_input, 0.01, 5, frame_cam[2])
        self.SetDoubleSpinBoxValues(self.ty_input,0.01, 5, frame_cam[3])

        self.RenderFile()
        # print("frame number = ", self.m_iFrameCounter)

    def FetchNextFrame(self):
        self.data['orig_cam'][self.m_iFrameCounter] = self.get_parameters()
        self.m_iFrameCounter += 1

        if self.m_iFrameCounter > self.m_iTotalframes:
            print("resetting frame from ", self.m_iFrameCounter," to ", self.m_iTotalframes)
            self.m_iFrameCounter = self.m_iTotalframes

        frame_cam = self.data['orig_cam'][self.m_iFrameCounter]

        self.SetDoubleSpinBoxValues(self.s_input, 0.01, 5, self.m_fS)
        self.SetDoubleSpinBoxValues(self.tx_input, 0.01, 5, frame_cam[2])
        self.SetDoubleSpinBoxValues(self.ty_input,0.01, 5, frame_cam[3])
        self.RenderFile()


    def get_parameters(self, first_frame = False):
        if first_frame:
            frame_cam = self.data['orig_cam'][self.m_iFrameCounter]
            tx = frame_cam[2]
            ty = frame_cam[3]
            sx = frame_cam[0]
            sy = sx * self.ratio
        else:
            sx = self.m_fS
            sy = sx * self.ratio
            tx = self.m_fTx
            ty = self.m_fTy
        return sx, sy, tx, ty

    def ChangeParameters(self):
        if 0:
            pass
        else:
            self.m_fS = self.s_input.value()
            self.m_fTx = self.tx_input.value()
            self.m_fTy = self.ty_input.value()
            self.RenderFile()

    def RenderFile(self, first_frame = False):
        if 1:
            i = self.m_iFrameCounter
            pose = self.all_poses[i][3:66]
            betas = self.all_betas[i]
            global_orient = self.data['pose'][i][:3]
            frame_cam = self.get_parameters(first_frame = first_frame)

            ret, frame = self.all_frames[i]
            self.curr_img, self.curr_mask = render_current_frame(ret, frame, frame_cam, self.renderer, self.model, pose, betas, global_orient)

            new_img = QImage(self.curr_img, self.curr_img.shape[1], self.curr_img.shape[0], QImage.Format_RGB888)
            self.m_pixmapPix = QPixmap.fromImage(new_img)
            self.m_pixmapPix = self.m_pixmapPix.scaled(self.label_width, self.label_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.display_label.setPixmap(self.m_pixmapPix)
            self.frame_info = str(i) + "/" + str(self.m_iTotalframes)
            self.frame_info_label.setText(self.frame_info)

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
