# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'reminder.ui'
#
# Created by: PySide6 UI code generator
#
# WARNING: Any manual changes made to this file will be lost when pyside6-uic is
# run again.  Do not edit this file unless you know what you are doing.

from PySide6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(200, 200)
        Dialog.setMinimumSize(QtCore.QSize(200, 200))
        Dialog.setMaximumSize(QtCore.QSize(200, 200))
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 50, 58, 17))
        self.label.setObjectName("label")
        self.Eventname = QtWidgets.QLineEdit(Dialog)
        self.Eventname.setGeometry(QtCore.QRect(80, 50, 113, 21))
        self.Eventname.setObjectName("Eventname")
        self.Time = QtWidgets.QLineEdit(Dialog)
        self.Time.setGeometry(QtCore.QRect(80, 90, 113, 21))
        self.Time.setObjectName("Time")
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 90, 58, 17))
        self.label_2.setObjectName("label_2")
        self.setButton = QtWidgets.QPushButton(Dialog)
        self.setButton.setGeometry(QtCore.QRect(60, 130, 80, 25))
        self.setButton.setObjectName("setButton")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(60, 10, 101, 17))
        self.label_3.setObjectName("label_3")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Reminder"))
        self.label.setText(_translate("Dialog", "Event"))
        self.label_2.setText(_translate("Dialog", "Time(s)"))
        self.setButton.setText(_translate("Dialog", "Set"))
        self.label_3.setText(_translate("Dialog", "Set Reminder"))