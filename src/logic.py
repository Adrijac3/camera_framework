'''QT specific imports'''
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QDialog, QLabel, QApplication
from PyQt5.QtGui  import QPixmap, QImage

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
        self.m_oCap = None
        self.m_iFps = 0
        self.m_iTotalframes = 0
        self.m_iDuration = 0
        # self.m_sVideo_path = '../data/video.mp4'
        self.m_sVideo_path = None

        # try:
        #     self.m_oCap = cv2.VideoCapture(self.m_sVideo_path)
        #     self.m_iFps = int(self.m_oCap.get(cv2.CAP_PROP_FPS))
        #     self.m_iDuration = self.getDuration(self.m_sVideo_path)
        #     self.m_iTotalframes = self.m_iFps * self.m_iDuration
        # except:
        #     print("error in opening video")

        '''SET EVENTS'''
        self.prev_button.clicked.connect(self.FetchPrevFrame)
        self.next_button.clicked.connect(self.FetchNextFrame)
        self.render_button.clicked.connect(self.RenderFile)
        self.params_button.clicked.connect(self.ChangeParameters)

        # self.LoadFrame(0)

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

        self.LoadFrame(self.m_iFrameCounter)
        print("frame number = ", self.m_iFrameCounter)

    def FetchNextFrame(self):
        self.m_iFrameCounter += 1

        if self.m_iFrameCounter > self.m_iTotalframes:
            print("resetting frame from ", self.m_iFrameCounter," to ", self.m_iTotalframes)
            self.m_iFrameCounter = self.m_iTotalframes

        self.LoadFrame(self.m_iFrameCounter)
        print("frame number = ", self.m_iFrameCounter)

    def ChangeParameters(self):
        if len(self.s_input.toPlainText() ) == 0 and len(self.tx_input.toPlainText()) == 0 and len(self.ty_input.toPlainText()) == 0:
            msg = QMessageBox()
            msg.setWindowTitle("Empty")
            msg.setText("No parameters set to change")
            msg.setIcon(QMessageBox.Warning)
            x = msg.exec_()
        else:
            if len(self.s_input.toPlainText() ) != 0:
                self.m_fS = self.s_input.toPlainText()
            if len(self.tx_input.toPlainText() ) != 0:
                self.m_fTx = self.tx_input.toPlainText()
            if len(self.ty_input.toPlainText() ) != 0:
                self.m_fTy = self.ty_input.toPlainText()
            self.RenderFile(self.m_fS, self.m_fTx, self.m_fTy)

    def RenderFile(self, s=None, tx=None, ty=None):
        if 1:
            i = self.m_iFrameCounter
            width, height, frame_count, all_frames, all_poses, all_betas, data, renderer, model= initialize_rendering()
            pose = all_poses[i][3:72]
            betas = all_betas[i]
            global_orient = data['pose'][i][:3]
            frame_cam = data['orig_cam'][i]
            ret, frame = all_frames[i]
            img, mask = render_current_frame(ret, frame, frame_cam, renderer, model, pose, betas, global_orient)
            new_img = QImage(img, img.shape[1], img.shape[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(new_img)
            pix = pix.scaled(600, 400, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.display_label.setPixmap(pix)
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Empty")
            msg.setText("Render file not available")
            msg.setIcon(QMessageBox.Warning)
            x = msg.exec_()

    def getDuration(self,filename):
        command = [
            'ffprobe',
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
