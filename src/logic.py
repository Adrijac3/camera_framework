'''QT specific imports'''
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QDialog, QLabel, QApplication
from PyQt5.QtGui  import QPixmap, QImage, QColor

''' Other python module imports'''
import sys, cv2, math, os
from subprocess import  check_output, CalledProcessError, STDOUT

'''Local imports'''
from ui import Ui_MainWindow
from rdemo import initialize_rendering, render_current_frame


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, *args, **kwargs):

        super(MyWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        '''SET VARIABLES'''
        self.m_fS = 0.0
        self.m_fTx = 0.0
        self.m_fTy = 0.0
        self.m_iFrameCounter = 0
        self.m_pixmapPix = None
        # self.m_oCap = None
        # self.m_iFps = 0
        # self.m_iTotalframes = 0
        # self.m_iDuration = 0
        # self.m_sVideo_path = '../data/video.mp4'
        self.m_sVideo_path = None
        frame_name  = 'abhi'
        gender = 'male'
        # video_path = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/{frame_name}.mp4"
        # tcmr_output = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/tcmr_output.pkl"
        # annotated = f"/Users/coreqode/Desktop/00.00-ObsUniv/24-annotation/annotation_3d/data/to_annotate/{frame_name}/annotate/smplx_param.pkl"
        video_path = f"../data/{frame_name}/{frame_name}.mp4"
        tcmr_output = f"../data/{frame_name}/tcmr_output.pkl"
        annotated = f"../data/{frame_name}/annotate/smplx_param.pkl"


        self.width, self.height, self.frame_count, self.all_frames, self.all_poses, self.all_betas, self.data, self.renderer, self.model = initialize_rendering(frame_name, gender, video_path, tcmr_output, annotated)


        '''SET QDoubleSpinBox initial values'''
        frame_cam = self.data['orig_cam'][0]
        print("default values :", frame_cam)
        self.SetDoubleSpinBoxValues(self.s_input, 0.01, 5, frame_cam[0])
        self.SetDoubleSpinBoxValues(self.tx_input, 0.01, 5, frame_cam[1])
        self.SetDoubleSpinBoxValues(self.ty_input,0.01, 5, frame_cam[2])

        self.m_iTotalframes = len(self.all_frames)
        if self.m_iFrameCounter == 0:
            self.RenderFile(0, None, None, None)

        '''SET EVENTS'''
        self.prev_button.clicked.connect(self.FetchPrevFrame)
        self.next_button.clicked.connect(self.FetchNextFrame)
        # self.render_button.clicked.connect(self.RenderFile)
        self.params_button.clicked.connect(self.ChangeParameters)
        self.display_label.mousePressEvent = self.Getxy
        # self.display_label.left_click.connect(self.image_clicked)

    def Getxy(self, event):
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
        # return x, y

    

        # self.LoadFrame(0)

    def SetDoubleSpinBoxValues(self, object_name, step, decimal, initial_val):
        object_name.setDecimals(decimal)
        object_name.setRange(-100.0,100.0)
        object_name.setValue(initial_val)
        # object_name.setMinimum(min_val)
        # object_name.setMaximum(max_val)
        object_name.setSingleStep(step)

    def LoadFrame(self, frame_number):
        self.m_oCap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.m_oCap.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(img)
            pix = pix.scaled(600, 400, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.display_label.setPixmap(pix)
            # cv2.imshow('frame',frame)
        else:
            dlg = QDialog()
            dlg.resize(200,100)
            lbl = QLabel(dlg)
            lbl.setText("Failed to fetch frame")
            lbl.move(10,50)
            dlg.setWindowTitle("Error")
            dlg.exec_()

    def FetchPrevFrame(self):

        self.m_iFrameCounter -= 1

        if self.m_iFrameCounter < 0:
            print("resetting frame from ", self.m_iFrameCounter," to 0")
            self.m_iFrameCounter = 0

        # self.LoadFrame(self.m_iFrameCounter)
        self.RenderFile(self.m_iFrameCounter, None, None, None)
        print("frame number = ", self.m_iFrameCounter)

    def FetchNextFrame(self):
        self.m_iFrameCounter += 1

        if self.m_iFrameCounter > self.m_iTotalframes:
            print("resetting frame from ", self.m_iFrameCounter," to ", self.m_iTotalframes)
            self.m_iFrameCounter = self.m_iTotalframes

        # self.LoadFrame(self.m_iFrameCounter)
        self.RenderFile(self.m_iFrameCounter, None, None, None)

        print("frame number = ", self.m_iFrameCounter)

    def ChangeParameters(self):
        # if len(self.s_input.toPlainText() ) == 0 and len(self.tx_input.toPlainText()) == 0 and len(self.ty_input.toPlainText()) == 0:
            # msg = QMessageBox()
            # msg.setWindowTitle("Empty")
            # msg.setText("No parameters set to change")
            # msg.setIcon(QMessageBox.Warning)
            # x = msg.exec_()
        if 0:
            pass
        else:
            # if len(self.s_input.toPlainText() ) != 0:
                self.m_fS = self.s_input.value()
            # if len(self.tx_input.toPlainText() ) != 0:
                self.m_fTx = self.tx_input.value()
            # if len(self.ty_input.toPlainText() ) != 0:
                self.m_fTy = self.ty_input.value()
                self.RenderFile(self.m_iFrameCounter, self.m_fS, self.m_fTx, self.m_fTy)

    def RenderFile(self, i = None, s=None, tx=None, ty=None):
        if 1:
            print(i)
            pose = self.all_poses[i][3:72]
            betas = self.all_betas[i]
            global_orient = self.data['pose'][i][:3]

            frame_cam = self.data['orig_cam'][i]
            if all([s, tx, ty]):
                s = float(s)
                tx = float(tx)
                ty = float(ty)
                print(s, tx, ty)
                frame_cam = [s*frame_cam[0], s*frame_cam[1], tx, ty]
                print(frame_cam)

            ret, frame = self.all_frames[i]
            img, mask = render_current_frame(ret, frame, frame_cam, self.renderer, self.model, pose, betas, global_orient)
            new_img = QImage(img, img.shape[1], img.shape[0], QImage.Format_RGB888)
            self.m_pixmapPix = QPixmap.fromImage(new_img)
            self.m_pixmapPix = self.m_pixmapPix.scaled(600, 400, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.display_label.setPixmap(self.m_pixmapPix)
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Empty")
            msg.setText("Render file not available")
            msg.setIcon(QMessageBox.Warning)
            x = msg.exec_()

    def getDuration(self,filename):
        command = [ 'ffprobe',
            '-v',
            'error',
            '-show_entries',
            'format=duration',
            '-of',
            'default=noprint_wrappers=1:nokey=1',
            filename
        ]

        try:
            output = check_output( command, stderr=STDOUT ).decode()
        except CalledProcessError as e:
            output = e.output.decode()
        #print(output)
        return math.ceil(float(output))

def main():
    app = QApplication(sys.argv)
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
