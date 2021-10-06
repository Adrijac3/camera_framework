# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.display_label = QtWidgets.QLabel(self.centralwidget)
        self.display_label.setGeometry(QtCore.QRect(20, 20, 751, 371))
        self.display_label.setStyleSheet("")
        self.display_label.setScaledContents(True)
        self.display_label.setObjectName("display_label")
        self.prev_button = QtWidgets.QPushButton(self.centralwidget)
        self.prev_button.setGeometry(QtCore.QRect(10, 410, 89, 25))
        self.prev_button.setObjectName("prev_button")
        self.next_button = QtWidgets.QPushButton(self.centralwidget)
        self.next_button.setGeometry(QtCore.QRect(680, 410, 89, 25))
        self.next_button.setObjectName("next_button")
        self.s_input = QtWidgets.QTextEdit(self.centralwidget)
        self.s_input.setGeometry(QtCore.QRect(180, 490, 51, 31))
        self.s_input.setObjectName("s_input")
        self.s_label = QtWidgets.QLabel(self.centralwidget)
        self.s_label.setGeometry(QtCore.QRect(140, 500, 21, 21))
        self.s_label.setObjectName("s_label")
        self.tx_input = QtWidgets.QTextEdit(self.centralwidget)
        self.tx_input.setGeometry(QtCore.QRect(360, 490, 51, 31))
        self.tx_input.setObjectName("tx_input")
        self.tx_label = QtWidgets.QLabel(self.centralwidget)
        self.tx_label.setGeometry(QtCore.QRect(310, 500, 31, 17))
        self.tx_label.setObjectName("tx_label")
        self.ty_label = QtWidgets.QLabel(self.centralwidget)
        self.ty_label.setGeometry(QtCore.QRect(490, 500, 31, 17))
        self.ty_label.setObjectName("ty_label")
        self.ty_input = QtWidgets.QTextEdit(self.centralwidget)
        self.ty_input.setGeometry(QtCore.QRect(540, 490, 51, 31))
        self.ty_input.setObjectName("ty_input")
        self.render_button = QtWidgets.QPushButton(self.centralwidget)
        self.render_button.setGeometry(QtCore.QRect(330, 410, 111, 25))
        self.render_button.setObjectName("render_button")
        self.params_button = QtWidgets.QPushButton(self.centralwidget)
        self.params_button.setGeometry(QtCore.QRect(300, 560, 181, 25))
        self.params_button.setObjectName("params_button")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Frame viewer"))
        self.display_label.setText(_translate("MainWindow", "Frames"))
        self.prev_button.setText(_translate("MainWindow", "Previous"))
        self.next_button.setText(_translate("MainWindow", "Next"))
        self.s_label.setText(_translate("MainWindow", "S :"))
        self.tx_label.setText(_translate("MainWindow", "tx :"))
        self.ty_label.setText(_translate("MainWindow", "ty :"))
        self.render_button.setText(_translate("MainWindow", "Render"))
        self.params_button.setText(_translate("MainWindow", "Change Parameters"))
