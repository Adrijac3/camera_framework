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
            print(e.key())
            print("inside subclass keypress")
            MyWindow.s_input_fetched, MyWindow.tx_input_fetched, MyWindow.ty_input_fetched = MyWindow.GetSpinBoxObject()
            # self.s, self.tx, self.ty = MyWindow.GetParameters()

            check_s = MyWindow.s_input_fetched.hasFocus()
            check_tx = MyWindow.tx_input_fetched.hasFocus()
            check_ty = MyWindow.ty_input_fetched.hasFocus()

            # print(check_s, check_tx, check_ty)

            if check_s == True:
                if e.key() == 16777236:
                    print("signal render function with s value increased by 1 step")
                    self.sig.emit("s+")
                elif e.key() == 16777234:
                    print("signal render function with s value decreased by 1 step")
                    self.sig.emit("s-")
            if check_tx == True:
                if e.key() == 16777236:
                    print("signal render function with tx value increased by 1 step")
                    self.sig.emit("tx+")
                elif e.key() == 16777234:
                    print("signal render function with ty value decreased by 1 step")
                    self.sig.emit("tx-")
            if check_ty == True:
                if e.key() == 16777236:
                    print("signal render function with tx value increased by 1 step")
                    self.sig.emit("ty+")
                elif e.key() == 16777234:
                    print("signal render function with ty value decreased by 1 step")
                    self.sig.emit("ty-")
            if e.key() == 16777216:
                sys.exit()
            if e.key() != 16777234 and e.key() != 16777236:
                return super().keyPressEvent(e)

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
        self.label_width = 751
        self.label_height = 351
        self.prev_button_offset = 0
        self.frame_info = "0/total"
        # video_path = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/{frame_name}.mp4"
        # tcmr_output = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/tcmr_output.pkl"
        # annotated = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/annotate/smplx_param.pkl"
        video_path = f"../data/{frame_name}/{frame_name}.mp4"
        tcmr_output = f"../data/{frame_name}/tcmr_output.pkl"
        annotated = f"../data/{frame_name}/annotate/smplx_param.pkl"


        self.width, self.height, self.m_iTotalframes, self.all_frames, self.all_poses, self.all_betas, self.data, self.renderer, self.model = initialize_rendering(frame_name, gender, video_path, tcmr_output, annotated)
        
        print("video width and height fetched: ", self.width, self.height)

        # set qlbael dimensions here
        self.display_label.setGeometry(QtCore.QRect(20, 20, self.label_width, self.label_height))

        '''SET QDoubleSpinBox initial values'''
        frame_cam = self.data['orig_cam'][0]
        print("default values :", frame_cam)
        self.m_fS = 1
        self.m_fTx = frame_cam[2]
        self.m_fTy = frame_cam[3]
        self.SetDoubleSpinBoxValues(MyWindow.s_input, 0.01, 5, self.m_fS)
        self.SetDoubleSpinBoxValues(MyWindow.tx_input, 0.01, 5, self.m_fTx)
        self.SetDoubleSpinBoxValues(MyWindow.ty_input,0.01, 5, self.m_fTy)

        # self.m_iTotalframes = len(self.all_frames)
        if self.m_iFrameCounter == 0:
            self.RenderFile(0, None, None, None)

        '''SET EVENTS'''
        self.prev_button.clicked.connect(self.FetchPrevFrame)
        self.next_button.clicked.connect(self.FetchNextFrame)
        MyWindow.s_input.valueChanged.connect(self.ValueChange)
        MyWindow.tx_input.valueChanged.connect(self.ValueChange)
        MyWindow.ty_input.valueChanged.connect(self.ValueChange)
        self.params_button.clicked.connect(self.ChangeParameters)
        self.display_label.mousePressEvent = self.Getxy
        self.annotate.stateChanged.connect(self.CheckAnnotation)
        MyWindow.s_input.sig.connect(self.ReceiveSignal)
        MyWindow.tx_input.sig.connect(self.ReceiveSignal)
        MyWindow.ty_input.sig.connect(self.ReceiveSignal)
    
    @QtCore.pyqtSlot(str)
    def ReceiveSignal(self,val):
        print("signal received: ", val)


    @staticmethod
    def GetSpinBoxObject():
        return MyWindow.s_input, MyWindow.tx_input, MyWindow.ty_input

    # @staticmethod
    # def GetParameters():
    #     return self.m_fS, self.m_fTx, self.m_fTy

    def Getxy(self, event):
        # MyWindow.s_input.setFocusPolicy(QtCore.Qt.NoFocus)
        x = event.pos().x()
        y = event.pos().y()
        print("Global pos: ", x,y)
        r = self.m_pixmapPix.rect()
        x0, y0 = r.x(), r.y()
        x1, y1 = x0+r.width(), y0+r.height()

        # Check we clicked on the pixmap
        if x >= x0 and x < x1 and y >= y0 and y < y1:

            # emit position relative to pixmap bottom-left corner
            x_relative = (x - x0) / (x1 - x0)
            y_relative = (y - y0) / (y1 - y0)

            print("Local pos: ", x_relative, y_relative)

    
    def wheelEvent(self,event):
        self.x =self.x + event.angleDelta().y()/120
        print("wheel: ",self.x)
        delta = event.angleDelta().y()
        self.x += (delta and delta // abs(delta))
        print("wheel with abs: ",self.x)

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
            self.RenderFile(self.m_iFrameCounter, self.m_fS, self.m_fTx, self.m_fTy)


    def SetDoubleSpinBoxValues(self, object_name, step, decimal, initial_val):
        object_name.setDecimals(decimal)
        object_name.setRange(-100.0,100.0)
        object_name.setValue(initial_val)
        # object_name.setMinimum(min_val)
        # object_name.setMaximum(max_val)
        object_name.setSingleStep(step)
        # object_name.setKeyboardTracking(False)

    def FetchPrevFrame(self):

        self.m_iFrameCounter -= 1

        if self.m_iFrameCounter < 0:
            print("resetting frame from ", self.m_iFrameCounter," to 0")
            self.m_iFrameCounter = 0

        frame_cam = self.data['orig_cam'][self.m_iFrameCounter]

        self.SetDoubleSpinBoxValues(MyWindow.s_input, 0.01, 5, self.m_fS)
        self.SetDoubleSpinBoxValues(MyWindow.tx_input, 0.01, 5, frame_cam[2])
        self.SetDoubleSpinBoxValues(MyWindow.ty_input,0.01, 5, frame_cam[3])

        self.RenderFile(self.m_iFrameCounter, None, None, None)
        print("frame number = ", self.m_iFrameCounter)

    def FetchNextFrame(self):
        self.m_iFrameCounter += 1

        if self.m_iFrameCounter > self.m_iTotalframes:
            print("resetting frame from ", self.m_iFrameCounter," to ", self.m_iTotalframes)
            self.m_iFrameCounter = self.m_iTotalframes

        frame_cam = self.data['orig_cam'][self.m_iFrameCounter]

        self.SetDoubleSpinBoxValues(MyWindow.s_input, 0.01, 5, self.m_fS)
        self.SetDoubleSpinBoxValues(MyWindow.tx_input, 0.01, 5, frame_cam[2])
        self.SetDoubleSpinBoxValues(MyWindow.ty_input,0.01, 5, frame_cam[3])
        self.RenderFile(self.m_iFrameCounter, None, None, None)

        print("frame number = ", self.m_iFrameCounter)

    def ChangeParameters(self):
        if 0:
            pass
        else:
                self.m_fS = MyWindow.s_input.value()
                self.m_fTx = MyWindow.tx_input.value()
                self.m_fTy = MyWindow.ty_input.value()
                self.RenderFile(self.m_iFrameCounter, self.m_fS, self.m_fTx, self.m_fTy)
                
    def RenderFile(self, i = None, s=None, tx=None, ty=None):
        if 1:
            print("renderfile i value: ", i)
            pose = self.all_poses[i][3:72]
            betas = self.all_betas[i]
            global_orient = self.data['pose'][i][:3]

            frame_cam = self.data['orig_cam'][i]
            if all([s, tx, ty]):
                s = float(s)
                tx = float(tx)
                ty = float(ty)
                print("s,tx,ty:", s, tx, ty)
                frame_cam = [s*frame_cam[0], s*frame_cam[1], tx, ty]
                print("frame cam:", frame_cam)

            ret, frame = self.all_frames[i]
            img, mask = render_current_frame(ret, frame, frame_cam, self.renderer, self.model, pose, betas, global_orient)
            new_img = QImage(img, img.shape[1], img.shape[0], QImage.Format_RGB888)
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

    def CheckAnnotation(self, state):
        if state == QtCore.Qt.Checked:
            print("Annotation mode")
        else:
            print("Normal viewing mode")
        

def main():
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
