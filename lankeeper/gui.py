# LANKeeper (https://github.com/danielperr/LANKeeper)
# Main GUI file

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import sys

MIN_SIZE = 900, 720
TITLE_FRAME_HEIGHT = 50
DASHBOARD_PANEL_HEIGHT = 200

COL_LANKEEPER_BLUE = '#1760B3'
COL_PRIMARY_GRAY = '#EEEEEE'
COL_PRIMATY_TEXT = '#333333'

SRC_BANNER_WHITE = './resources/images/banner-white.png'


class MainWindow (QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self.devicesTable.set
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


class Panel (QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._panelTitle = 'Panel'

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(12, 0, 12, 0)
        self.setStyleSheet('background-color: white; border-radius: 2px;')
        shadow = QGraphicsDropShadowEffect(blurRadius=10, xOffset=0, yOffset=3, color=QColor(0, 0, 0, 0.2*255))
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    # table = Table(15, 3)
    sys.exit(app.exec_())
