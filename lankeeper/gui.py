# LANKeeper (https://github.com/danielperr/LANKeeper)
# Main GUI file

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import sys
import os

MIN_SIZE = 900, 720
TITLE_FRAME_HEIGHT = 50
DASHBOARD_PANEL_HEIGHT = 200

COL_LANKEEPER_BLUE = '#1760B3'
COL_PRIMARY_GRAY = '#EEEEEE'
COL_PRIMATY_TEXT = '#333333'

SRC_BANNER_WHITE = os.getcwd() + '\\lankeeper\\resources\\images\\white-banner.png'
SRC_LOADING_GIF = os.getcwd() + '\\lankeepzer\\resources\\images\\loading.gif'
SRC_INFO = os.getcwd() + '\\lankeeper\\resources\\images\\info.png'
SRC_CHECKMARK = os.getcwd() + '\\lankeeper\\resources\\images\\checkmark.png'


class MainWindow (QMainWindow):

    def __init__(self, loopCallback, scanCallback, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.loopCallback = loopCallback
        self.loopTimer = QTimer(self)
        self.loopTimer.timeout.connect(self.loopCallback)
        self.loopTimer.start(10)
        self.scanCallback = scanCallback
        self.scanTimer = QTimer(self)
        self.scanTimer.timeout.connect(self.scanCallback)
        self.scanTimer.start(10000)

        self.device_ids = []

    def initUi(self):
        self.setWindowTitle('LANKeeper')
        self.setMinimumSize(*MIN_SIZE)
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        self.centralWidget().setLayout(QVBoxLayout())
        self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
        self.centralWidget().layout().setSpacing(0)
        self.statusBar().showMessage('')
        # <titleFrame>
        self.titleFrame = QFrame()
        self.centralWidget().layout().addWidget(self.titleFrame)
        self.titleFrame.setLayout(QHBoxLayout())
        self.titleFrame.layout().setContentsMargins(20, 0, 0, 0)
        self.titleFrame.setStyleSheet('background-color: %s;' % COL_LANKEEPER_BLUE)
        self.titleFrame.setMinimumHeight(TITLE_FRAME_HEIGHT)
        self.titleFrame.setMaximumHeight(TITLE_FRAME_HEIGHT)
        #   <titleLabel>
        self.titleLabel = QLabel()
        self.titleFrame.layout().addWidget(self.titleLabel)
        titlePixmap = QPixmap(SRC_BANNER_WHITE)
        titlePixmap = titlePixmap.scaled(128, 27, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.titleLabel.setPixmap(titlePixmap)
        #   </titleLabel>
        # </titleFrame>
        # <mainFrame>
        self.mainFrame = QFrame()
        self.centralWidget().layout().addWidget(self.mainFrame)
        self.mainFrame.setStyleSheet('background-color: %s;' % COL_PRIMARY_GRAY)
        self.mainFrame.setLayout(QVBoxLayout())
        self.mainFrame.layout().setContentsMargins(0, 10, 0, 0)
        self.mainFrame.layout().setSpacing(0)
        #   <dashboardFrame>
        self.dashboardFrame = QFrame()
        self.mainFrame.layout().addWidget(self.dashboardFrame)
        self.dashboardFrame.setLayout(QHBoxLayout())
        self.dashboardFrame.setMinimumHeight(DASHBOARD_PANEL_HEIGHT + 10)
        self.dashboardFrame.setMaximumHeight(DASHBOARD_PANEL_HEIGHT + 10)
        self.dashboardFrame.layout().setContentsMargins(18, 0, 18, 10)
        self.dashboardFrame.layout().setSpacing(0)
        #     <dashboardPanel>
        self.dashboardPanel = Panel()
        self.dashboardFrame.layout().addWidget(self.dashboardPanel)
        self.dashboardPanel.panelTitle = 'Dashboard'
        self.dashboardPanel.setMinimumHeight(DASHBOARD_PANEL_HEIGHT)
        self.dashboardPanel.setMaximumHeight(DASHBOARD_PANEL_HEIGHT)
        self._dbNewDevices = 0
        self.renderDashboard()
        #     </dashboardPanel>
        #   </dashboardFrame>
        #   <devmonFrame>
        self.devmonFrame = QFrame()
        self.mainFrame.layout().addWidget(self.devmonFrame)
        self.devmonFrame.setLayout(QHBoxLayout())
        self.devmonFrame.layout().setContentsMargins(18, 0, 18, 10)
        self.devmonFrame.layout().setSpacing(10)
        #     <devicesPanel>
        self.devicesPanel = Panel()
        self.devmonFrame.layout().addWidget(self.devicesPanel, 12)
        self.devicesPanel.panelTitle = 'Devices'
        self.devicesPanel.mainFrame.setLayout(QVBoxLayout())
        self.devicesPanel.mainFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.devicesPanel.mainFrame.layout().setSpacing(10)
        #       <devicesTable>
        self.devicesTable = Table(1, 4)
        self.devicesPanel.mainFrame.layout().addWidget(self.devicesTable)
        self.devicesTable.setHorizontalHeaderLabels(['', 'Device', 'Vendor', 'Last seen'])
        self.devicesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.devicesTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.devicesTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.devicesTable.horizontalHeader().setStretchLastSection(True)
        self.devicesTable.horizontalHeader().setStyleSheet('''::section{
                                                                Background-color: %s;
                                                                border: 0;
                                                                height: 36px;
                                                              }''' % COL_PRIMARY_GRAY)
        self.devicesTable.setShowGrid(False)
        headerFont = QFont('Segoe UI', 12, QFont.DemiBold)
        headerFont.setStyleStrategy(QFont.PreferAntialias)
        self.devicesTable.horizontalHeader().setFont(headerFont)
        itemFont = QFont('Segoe UI', 10)
        itemFont.setStyleStrategy(QFont.PreferAntialias)
        self.devicesTable.setFont(itemFont)
        self.devicesTable.verticalHeader().setVisible(False)
        self.devicesTable.setColumnWidth(0, 36)
        self.devicesTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.devicesTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.devicesTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.devicesTable.doubleClicked.connect(self.deviceSelected)
        # self.devicesTable.set
        #       </devicesTable>
        #     </devicesPanel>
        #     <monitoringPanel>
        self.monitoringPanel = Panel()
        self.devmonFrame.layout().addWidget(self.monitoringPanel, 5)
        self.monitoringPanel.panelTitle = 'Monitoring'
        #     </monitoringPanel>
        #   </devmonFrame>
        # </mainFrame>
        self.show()

        # <deviceWindow>
        self.deviceWindow = SmallWindow()
        self.deviceWindow.setWindowModality(Qt.ApplicationModal)
        self.deviceWindow.mainPanel.panelTitle = 'Device info'
        self.deviceWindow.mainPanel.mainFrame.setLayout(QVBoxLayout())
        self.deviceWindow.deviceLabel = QLabel()
        self.deviceWindow.mainPanel.mainFrame.layout().addWidget(self.deviceWindow.deviceLabel)
        # </deviceWindow>

    def renderDashboard(self):
        self.dashboardPanel.mainFrame.setLayout(QVBoxLayout())
        self.dbNewDevicesFrame = QFrame()
        self.dashboardPanel.mainFrame.layout().addWidget(self.dbNewDevicesFrame)
        self.dbNewDevicesFrame.setLayout(QHBoxLayout())
        self.dbNewDevicesFrame.layout().setAlignment(Qt.AlignLeft)
        self.dbNewDevicesIcon = QLabel()
        self.dbNewDevicesFrame.layout().addWidget(self.dbNewDevicesIcon)
        pixmap = QPixmap(SRC_INFO if self._dbNewDevices else SRC_CHECKMARK)
        pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.dbNewDevicesIcon.setPixmap(pixmap)
        self.dbNewDevicesIcon.setAlignment(Qt.AlignLeft)
        self.dbNewDevicesLabel = QLabel()
        self.dbNewDevicesFrame.layout().addWidget(self.dbNewDevicesLabel)
        text = 'No new devices detected.'
        if self._dbNewDevices == 1:
            text = '1 new device detected.'
        elif self._dbNewDevices > 1:
            text = '%s new devices detected.' % self._dbNewDevices
        self.dbNewDevicesLabel.setText(text)
        self.dbNewDevicesLabel.setAlignment(Qt.AlignLeft)
        font = QFont('Segoe UI', 12)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.dbNewDevicesLabel.setFont(font)

    @property
    def dbNewDevices(self):
        return self._dbNewDevices

    @dbNewDevices.setter
    def dbNewDevices(self, value):
        self._dbNewDevices = value
        # self.renderDashboard()
        pixmap = QPixmap(SRC_INFO if self._dbNewDevices else SRC_CHECKMARK)
        pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.dbNewDevicesIcon.setPixmap(pixmap)
        text = 'No new devices detected.'
        if self._dbNewDevices == 1:
            text = '1 new device detected.'
        elif self._dbNewDevices > 1:
            text = '%s new devices detected.' % self._dbNewDevices
        self.dbNewDevicesLabel.setText(text)


class SmallWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        self.centralWidget().setLayout(QVBoxLayout())
        self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
        self.centralWidget().layout().setSpacing(0)
        self.statusBar().showMessage('')
        # <titleFrame>
        self.titleFrame = QFrame()
        self.centralWidget().layout().addWidget(self.titleFrame)
        self.titleFrame.setLayout(QHBoxLayout())
        self.titleFrame.layout().setContentsMargins(20, 0, 0, 0)
        self.titleFrame.setStyleSheet('background-color: %s;' % COL_LANKEEPER_BLUE)
        self.titleFrame.setMinimumHeight(int(TITLE_FRAME_HEIGHT/2))
        self.titleFrame.setMaximumHeight(int(TITLE_FRAME_HEIGHT/2))
        # </titleFrame>
        # <mainFrame>
        self.mainFrame = QFrame()
        self.centralWidget().layout().addWidget(self.mainFrame)
        self.mainFrame.setStyleSheet('background-color: %s;' % COL_PRIMARY_GRAY)
        self.mainFrame.setLayout(QVBoxLayout())
        self.mainFrame.layout().setContentsMargins(18, 10, 18, 10)
        self.mainFrame.layout().setSpacing(0)
        #   <mainPanel>
        self.mainPanel = Panel()
        self.mainFrame.layout().addWidget(self.mainPanel)
        #   </mainPanel>
        # </mainFrame>


class Panel (QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._panelTitle = 'Panel'

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 0, 12, 0)
        self .setStyleSheet('background-color: white; border-radius: 2px;')
        shadow = QGraphicsDropShadowEffect(blurRadius=10, xOffset=0, yOffset=3, color=QColor(0, 0, 0, int(0.2*255)))
        self.setGraphicsEffect(shadow)
        # <titleFrame>
        self.titleFrame = QFrame()
        self.layout().addWidget(self.titleFrame)
        self.titleFrame.setLayout(QHBoxLayout())
        self.titleFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.titleFrame.setMinimumHeight(50)
        self.titleFrame.setMaximumHeight(50)
        self.titleFrame.setStyleSheet('border-bottom: 1px solid %s; border-radius: revert;' % COL_PRIMARY_GRAY)
        #   <titleLabel>
        self.titleLabel = QLabel()
        self.titleFrame.layout().addWidget(self.titleLabel)
        self.titleLabel.setText(self.panelTitle)
        self.titleLabel.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        titleLabelFont = QFont('Segoe UI', 20, QFont.DemiBold)
        titleLabelFont.setStyleStrategy(QFont.PreferAntialias)
        self.titleLabel.setFont(titleLabelFont)
        self.titleLabel.setStyleSheet('color: %s' % COL_PRIMATY_TEXT)
        #   </titleLabel>
        # </titleFrame>
        # <mainFrame>
        self.mainFrame = QFrame()
        self.layout().addWidget(self.mainFrame)
        # </mainFrame>

    @property
    def panelTitle(self):
        return self._panelTitle

    @panelTitle.setter
    def panelTitle(self, value):
        self.titleLabel.setText(value)
        self._panelTitle = value


class Table (QTableWidget):

    def __init__(self, r, c, *args, **kwargs):
        super().__init__(r, c, *args, **kwargs)


def callback():
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # window = MainWindow(callback)
    # table = Table(15, 3)
    window = SmallWindow()
    window.show()
    sys.exit(app.exec_())
