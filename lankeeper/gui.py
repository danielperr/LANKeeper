# LANKeeper (https://github.com/danielperr/LANKeeper)
# Main GUI file

import os
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from datetime import datetime

from device import Device
from monitorgroup import MonitorGroup
from detectors.detectors import detectors_sorted
import utils


MIN_SIZE = 900, 845
TITLE_FRAME_HEIGHT = 50
PANEL_TITLE_SIZE = 18
DASHBOARD_PANEL_HEIGHT = 200
DIAGNOSIS_PANEL_HEIGHT = 100

COL_LANKEEPER_BLUE = '#1760B3'
COL_PRIMARY_GRAY = '#EEEEEE'
COL_PRIMARY_TEXT = '#333333'
COL_SCROLLBAR = '#BBBBBB'
COL_SELECTED_BG = '#f0f7ff'

SRC_BANNER_WHITE = os.getcwd() + r'\lankeeper\resources\images\white-banner.png'
SRC_LOADING_GIF = os.getcwd() + r'\lankeeper\resources\images\loading.gif'
SRC_INFO = os.getcwd() + r'\lankeeper\resources\images\info.png'
SRC_CHECKMARK = os.getcwd() + r'\lankeeper\resources\images\checkmark.png'

DATETIME_FORMAT = r'%m/%d/%Y at %H:%M:%S'
LABEL_STYLESHEET = f'font: 13px "Segoe UI"; color: {COL_PRIMARY_TEXT}'


class MainWindow (QMainWindow):

    def __init__(self, manager, *args, **kwargs):
        """App main window"""
        super().__init__(*args, **kwargs)

        self._manager = manager
        self.loopTimer = QTimer(self)
        self.loopTimer.timeout.connect(self._manager.loop)
        self.loopTimer.start(10)
        self.scanTimer = QTimer(self)
        self.scanTimer.timeout.connect(self._manager.scan)
        self.scanTimer.start(10000)
        self.deviceDataCallback = self._manager.get_device_data
        self.openDeviceId = 0

        self.device_ids = []
        self.mg_ids = []

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
        self.devicesTable.doubleClicked.connect(self._deviceSelected)
        #       </devicesTable>
        #     </devicesPanel>
        #     <monitoringPanel>
        self.monitoringPanel = Panel()
        self.devmonFrame.layout().addWidget(self.monitoringPanel, 5)
        self.monitoringPanel.panelTitle = 'Monitoring'
        self.monitoringPanel.mainFrame.setLayout(QVBoxLayout())
        self.monitoringPanel.mainFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.monitoringPanel.mainFrame.layout().setSpacing(10)
        #       <mgTitleFrame>
        self.mgTitleFrame = QFrame()
        self.monitoringPanel.mainFrame.layout().addWidget(self.mgTitleFrame)
        self.mgTitleFrame.setLayout(QHBoxLayout())
        self.mgTitle = QLabel('Monitoring groups')
        self.mgTitleFrame.layout().addWidget(self.mgTitle)
        mgTitleFont = QFont()
        mgTitleFont.setFamily('Segoe UI')
        mgTitleFont.setPixelSize(16)
        mgTitleFont.setWeight(QFont.DemiBold)
        self.mgTitle.setFont(mgTitleFont)
        self.mgTitle.setStyleSheet('color: ' + COL_PRIMARY_TEXT)
        self.mgEditBtn = QLabel('<a href="#">Edit</a>')
        self.mgTitleFrame.layout().addWidget(self.mgEditBtn)
        self.mgEditBtn.setStyleSheet('font-size: 12px')
        self.mgEditBtn.linkActivated.connect(self._mgEditBtnClicked)
        self.mgEditBtn.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        #       </mgTitleFrame>
        #       <mgTable>
        self.mgTable = Table(1, 1, no_header=True)  # monitor group table
        self.monitoringPanel.mainFrame.layout().addWidget(self.mgTable)
        # self.mgTable.setItem(0, 0, QTableWidgetItem('Default Group'))
        # self.mgTable.setItem(0, 1, QTableWidgetItem('20 devices'))
        self.mgTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #       </mgTable>
        #     </monitoringPanel>
        #   </devmonFrame>
        #   <diagFrame>
        self.diagFrame = QFrame()
        self.mainFrame.layout().addWidget(self.diagFrame)
        self.diagFrame.setLayout(QHBoxLayout())
        self.diagFrame.setMinimumHeight(DIAGNOSIS_PANEL_HEIGHT + 10)
        self.diagFrame.setMaximumHeight(DIAGNOSIS_PANEL_HEIGHT + 10)
        self.diagFrame.layout().setContentsMargins(18, 0, 18, 10)
        self.diagFrame.layout().setSpacing(0)
        #     <diagPanel>
        self.diagPanel = Panel()
        self.diagFrame.layout().addWidget(self.diagPanel)
        self.diagPanel.panelTitle = 'Diagnosis'
        self.diagPanel.setMinimumHeight(DIAGNOSIS_PANEL_HEIGHT)
        self.diagPanel.setMaximumHeight(DIAGNOSIS_PANEL_HEIGHT)
        #   </diagFrame>
        # </mainFrame>
        self.show()

        # Initialize other windows
        self.deviceWindow = DeviceWindow()  # Device window
        self.deviceWindow.initUi()
        self.mgmanageWindow = MGManageWindow(self._manager)  # Monitor groups management window
        self.mgmanageWindow.initUi()

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

    def updateDevicesTable(self, devices, loading=False):
        self.device_ids = list(zip(*devices))[0]
        self.devicesTable.setRowCount(0)
        for row, device in enumerate([x[1:] for x in devices]):
            self.devicesTable.insertRow(row)
            for col, item in enumerate(device):
                if col == len(device) - 1 and loading:
                    self.devicesTable.setItem(row, col, QTableWidgetItem('scanning...'))
                elif col == 0:
                    if item == 1:
                        iconWidget = QWidget()
                        iconWidget.setLayout(QHBoxLayout())
                        iconWidget.layout().setAlignment(Qt.AlignCenter)
                        iconWidget.layout().setContentsMargins(0, 0, 0, 0)
                        pixmap = QPixmap(SRC_INFO)
                        pixmap = pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        label = QLabel()
                        label.setPixmap(pixmap)
                        iconWidget.layout().addWidget(label)
                        iconWidget.setStyleSheet('background-color:rgba(0,0,0,0);')
                        self.devicesTable.setCellWidget(row, col, iconWidget)
                else:
                    self.devicesTable.setItem(row, col, QTableWidgetItem(str(item)))

    def updateMGtable(self, data):
        """
        Update the monitor group table at the main window
        and updates the monitor group window
        mgs (list): [(id: int, mg: MonitorGroup), ...]
        """
        self.mg_ids, mgs = list(zip(*data))
        self.mgTable.setRowCount(0)
        for row, mg in enumerate(mgs):
            self.mgTable.insertRow(row)
            self.mgTable.setItem(row, 0, QTableWidgetItem(mg.name))
            self.mgTable.setItem(row, 1, QTableWidgetItem(str(len(mg.ips))))
        # Update the monitor group window
        self.mgmanageWindow.updateMonitorGroups(mgs, self.mg_ids)

    def _deviceSelected(self, item):
        self.openDeviceId = self.device_ids[item.row()]
        self.deviceWindow.device = self._manager.get_device_data(self.openDeviceId)
        self.deviceWindow.show()

    def _mgEditBtnClicked(self):
        self.mgmanageWindow.show()

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

        self.setWindowModality(Qt.ApplicationModal)
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


class DeviceWindow(SmallWindow):

    TITLE = 'Device info'
    # Label titles
    PLACEHOLDER = 'Unknown'
    T_NAME = 'Name'
    T_IP = 'IP'
    T_MAC = 'MAC'
    T_VENDOR = 'Vendor'
    T_PORTS = 'Open ports'
    T_OS = 'OS'
    T_PORTS = 'Open TCP ports'
    T_FIRST_JOINED = 'FIRST JOINED'
    T_LAST_SEEN = 'LAST SEEN'
    # Style

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._device = None
        self._ip = self.PLACEHOLDER
        self._mac = self.PLACEHOLDER
        self._name = self.PLACEHOLDER
        self._vendor = self.PLACEHOLDER
        self._os = self.PLACEHOLDER
        self._ports = []
        self._first_joined = datetime.now()
        self._last_seen = datetime.now()
        self._deep_scanned = False

    def initUi(self):
        self.mainPanel.panelTitle = self.TITLE
        self.mainPanel.mainFrame.setLayout(QHBoxLayout())
        self.mainPanel.mainFrame.layout().setSpacing(14)
        # <leftFrame>
        self.leftFrame = QFrame()
        self.mainPanel.mainFrame.layout().addWidget(self.leftFrame)
        self.leftFrame.setLayout(QVBoxLayout())
        self.leftFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.nameLabel = self.composeLabel(self.composeText(self.T_NAME, self._name))
        self.leftFrame.layout().addWidget(self.nameLabel)
        self.ipLabel = self.composeLabel(self.composeText(self.T_IP, self._ip))
        self.leftFrame.layout().addWidget(self.ipLabel)
        self.macLabel = self.composeLabel(self.composeText(self.T_MAC, self._mac))
        self.leftFrame.layout().addWidget(self.macLabel)
        self.vendorLabel = self.composeLabel(self.composeText(self.T_VENDOR, self._vendor))
        self.leftFrame.layout().addWidget(self.vendorLabel)
        self.leftFrame.layout().addStretch()
        # </leftFrame>
        # <midFrame>
        self.midFrame = QFrame()
        self.mainPanel.mainFrame.layout().addWidget(self.midFrame)
        self.midFrame.setLayout(QVBoxLayout())
        self.midFrame.layout().setContentsMargins(0, 0, 0, 0)
        # set up mid frame components
        self.osLabel = self.composeLabel(self.composeText(self.T_OS, self._os))
        self.midFrame.layout().addWidget(self.osLabel)
        ports_string = ', '.join(map(str, self._ports)) if self._ports else self.PLACEHOLDER
        self.portsLabel = self.composeLabel(self.composeText(self.T_PORTS, ports_string))
        self.midFrame.layout().addWidget(self.portsLabel)
        self.scanBtn = self.composeLabel('<a href="#">(Scan)</a>')
        self.midFrame.layout().addWidget(self.scanBtn)
        self.scanBtn.linkActivated.connect(self.onClickScan)
        self.midFrame.layout().addStretch()
        # </midFrame>
        # <rightFrame>
        self.rightFrame = QFrame()
        self.mainPanel.mainFrame.layout().addWidget(self.rightFrame)
        self.rightFrame.setLayout(QVBoxLayout())
        self.rightFrame.layout().setContentsMargins(0, 0, 0, 0)
        # set up right frame components
        self.lastSeenBlock = DeviceTimeBlock(self.T_LAST_SEEN, self._last_seen)
        self.rightFrame.layout().addWidget(self.lastSeenBlock)
        self.firstJoinedBlock = DeviceTimeBlock(self.T_FIRST_JOINED, self._first_joined)
        self.rightFrame.layout().addWidget(self.firstJoinedBlock)
        self.rightFrame.layout().addStretch()
        # </rightFrame>

    def composeText(self, title, value):
        return f'<b>{title}:</b> {value}'

    def composeLabel(self, text) -> QLabel:
        label = QLabel(text=text)
        label.setStyleSheet(LABEL_STYLESHEET)
        return label

    def onClickScan(self, e):
        print('scan clicked')

    @property
    def device(self) -> Device:
        return self._device

    @device.setter  # TODO: update new attributes
    def device(self, d: Device):
        self._device = d
        self._ip = d.ip
        print('SETTING DEVICE')
        print(d)
        self.mainPanel.panelTitle = f'{self.TITLE} ({self._ip if not d.name else d.name})'
        self.ipLabel.setText(self.composeText(self.T_IP, self._ip))
        if d.mac and self._mac != d.mac:
            self._mac = d.mac
            self.macLabel.setText(self.composeText(self.T_MAC, self._mac))
        if d.name and self._name != d.name:
            self._name = d.name
            self.mainPanel.panelTitle = f'{self.TITLE} ({self._name})'
            self.nameLabel.setText(self.composeText(self.T_NAME, self._name))
        if d.vendor and self._vendor != d.vendor:
            self._vendor = d.vendor
            self.vendorLabel.setText(self.composeText(self.T_VENDOR, self._vendor))
        if d.os and self._os != d.os:
            self._os = d.os
            self.osLabel.setText(self.composeText(self.T_OS, self._os))
        if d.ports and self._ports != d.ports:
            self._ports = d.ports
            self.portsLabel.setText(self.composeText(self.T_PORTS, ', '.join(map(str, self._ports))))
        if d.last_seen:
            self._last_seen = d.last_seen
            self.lastSeenBlock.time = self._last_seen
        if d.first_joined:
            self._first_joined = d.first_joined
            self.firstJoinedBlock.time = self._first_joined


class DeviceTimeBlock (QFrame):
    """This time block appears in the device window, titled 'FIRST JOINED' and 'LAST SEEN'"""

    def __init__(self, title: str, time: datetime):
        super().__init__()
        self.title = title
        self._time = time
        self.initUi()

    def initUi(self):
        self.setStyleSheet('QLabel {%s}' % LABEL_STYLESHEET)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 14)
        self.layout().setSpacing(0)
        self.titleLabel = QLabel(text=f'<b>{self.title}</b>')
        self.layout().addWidget(self.titleLabel)
        self.agoLabel = QLabel(text=utils.time_ago(self._time))
        self.layout().addWidget(self.agoLabel)
        self.timeLabel = QLabel(text=self._time.strftime(DATETIME_FORMAT))
        self.layout().addWidget(self.timeLabel)
        self.layout().addStretch()

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value
        print(f'{self._time=}')
        print(f'{utils.time_ago(self._time)=}')
        self.agoLabel.setText(utils.time_ago(self._time))
        self.timeLabel.setText(self._time.strftime(DATETIME_FORMAT))


class MGManageWindow(SmallWindow):

    def __init__(self, manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._manager = manager
        self._monitor_groups_ids = []
        self._monitor_groups = []

    def initUi(self):
        self.setMinimumWidth(540)
        self.mainPanel.panelTitle = 'Monitoring groups'
        self.mainPanel.mainFrame.setLayout(QVBoxLayout())
        self.mgTable = Table(1, 5, multi_select=True)
        self.mainPanel.mainFrame.layout().addWidget(self.mgTable)
        self.mgTable.setHorizontalHeaderLabels(['', 'Name', 'Devices', 'Detectors', ''])
        self.mgTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mgTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.mgTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.mgTable.horizontalHeader().setStretchLastSection(True)
        self.mgTable.selectionModel().selectionChanged.connect(self._mgTableSelected)
        self.controlsFrame = QFrame()
        self.mainPanel.mainFrame.layout().addWidget(self.controlsFrame)
        self.controlsFrame.setLayout(QHBoxLayout())
        self.controlsFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.controlsFrame.layout().setSpacing(8)
        # self.controlsFrame.setStyleSheet('QPushButton {background-color: red}')
        self.selectAllBtn = QPushButton('Select all')
        self.controlsFrame.layout().addWidget(self.selectAllBtn)
        self.selectAllBtn.clicked.connect(self._selectAllBtnClicked)
        self.deselectAllBtn = QPushButton('Deselect all')
        self.controlsFrame.layout().addWidget(self.deselectAllBtn)
        self.deselectAllBtn.clicked.connect(self._deselectAllBtnClicked)
        self.deselectAllBtn.setEnabled(False)
        self.deleteBtn = QPushButton('Delete groups')
        self.controlsFrame.layout().addWidget(self.deleteBtn)
        self.deleteBtn.clicked.connect(self._deleteBtnClicked)
        self.deleteBtn.setEnabled(False)
        self.newBtn = QPushButton('New...')
        self.controlsFrame.layout().addWidget(self.newBtn)
        self.newBtn.clicked.connect(self._newBtnClicked)
        self.controlsFrame.layout().addStretch()
        self.okBtn = QPushButton('OK')
        self.controlsFrame.layout().addWidget(self.okBtn)
        self.okBtn.clicked.connect(self._okBtnClicked)
        self.okBtn.setDefault(True)

    def updateMonitorGroups(self, mgs, ids):
        self._monitor_groups = mgs
        self._monitor_groups_ids = ids
        print('\n'.join(map(str, mgs)))
        self.mgTable.setRowCount(len(self._monitor_groups))
        for row, mg in enumerate(self._monitor_groups):
            nameItem = QTableWidgetItem(mg.name)
            devicesItem = QTableWidgetItem(f'{len(mg.ips)} devices')
            devicesItem.setTextAlignment(Qt.AlignCenter)
            detectorsItem = QTableWidgetItem(f'{len(mg.detectors)} detectors')
            detectorsItem.setTextAlignment(Qt.AlignCenter)
            editWidget = QWidget()
            editWidget.setLayout(QHBoxLayout())
            editWidget.layout().setAlignment(Qt.AlignCenter)
            editWidget.layout().setContentsMargins(0, 0, 0, 0)
            edit = QLabel('<a href="#">Edit</a>')
            editWidget.layout().addWidget(edit)
            editWidget.setStyleSheet('background-color:rgba(0,0,0,0);')
            self.mgTable.setItem(row, 1, nameItem)
            self.mgTable.setItem(row, 2, devicesItem)
            self.mgTable.setItem(row, 3, detectorsItem)
            self.mgTable.setCellWidget(row, 4, editWidget)

    def _mgTableSelected(self, selection):
        indexes = self.mgTable.selectedIndexes()
        default_selected = False
        # if 1 in [self._monitor_groups_ids[x.row()] for x in indexes]:
        #     default_selected = True
        for index in indexes:
            if self._monitor_groups_ids[index.row()] == 1:
                self.mgTable.selectionModel().select(index, QItemSelectionModel.Deselect)
                return
        count = len([x for x in indexes if x.column() == 1])
        self.deselectAllBtn.setEnabled(count)
        self.selectAllBtn.setEnabled(count != self.mgTable.rowCount())
        if count > 1:
            deltxt = f'Delete {count} groups'
        elif count:
            deltxt = 'Delete 1 group'
        else:
            deltxt = 'Delete groups'
        self.deleteBtn.setText(deltxt)
        self.deleteBtn.setEnabled(count and not default_selected)

    def _selectAllBtnClicked(self, e):
        self.mgTable.selectAll()

    def _deselectAllBtnClicked(self, e):
        self.mgTable.clearSelection()

    def _deleteBtnClicked(self, e):
        self._manager.delete_mgs([self._monitor_groups_ids[x.row()]
                                  for x in self.mgTable.selectionModel().selectedRows()])

    def _newBtnClicked(self, e):
        pass

    def _okBtnClicked(self, e):
        self.close()


class Panel (QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._panelTitle = 'Panel'

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(15, 0, 15, 20)
        self.setStyleSheet('QFrame {background-color: white; border-radius: 2px;}')
        shadow = QGraphicsDropShadowEffect(blurRadius=6, xOffset=2, yOffset=3, color=QColor(0, 0, 0, int(0.05*255)))
        self.setGraphicsEffect(shadow)
        # <titleFrame>
        self.titleFrame = QFrame()
        self.layout().addWidget(self.titleFrame)
        self.titleFrame.setLayout(QHBoxLayout())
        self.titleFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.titleFrame.setMinimumHeight(50)
        self.titleFrame.setMaximumHeight(50)
        self.titleFrame.setStyleSheet('QFrame {border-bottom: 1px solid %s; border-radius: revert;}' % COL_PRIMARY_GRAY)
        #   <titleLabel>
        self.titleLabel = QLabel()
        self.titleFrame.layout().addWidget(self.titleLabel)
        self.titleLabel.setText(self.panelTitle)
        self.titleLabel.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        titleLabelFont = QFont('Segoe UI', PANEL_TITLE_SIZE, QFont.DemiBold)
        titleLabelFont.setStyleStrategy(QFont.PreferAntialias)
        self.titleLabel.setFont(titleLabelFont)
        self.titleLabel.setStyleSheet('color: %s' % COL_PRIMARY_TEXT)
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

    def __init__(self, r, c, *args, no_header=False, multi_select=False, **kwargs):
        super().__init__(r, c, *args, **kwargs)
        self.setShowGrid(False)
        itemFont = QFont('Segoe UI', 10)
        itemFont.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(itemFont)
        self.verticalHeader().setVisible(False)
        self.setColumnWidth(0, 36)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        if multi_select:
            self.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setPalette(self.style().standardPalette())
        self.setStyleSheet('''QTableWidget::item:selected {{
                background-color: {1};
                color: black;
            }} QHeaderView::section {{
                color: {2};
            }} QScrollBar:vertical {{
                border: none;
                width:8px;
                margin: 0px 0px 0px 0px;
            }} QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 '{0}',
                    stop: 0.5 '{0}',
                    stop: 1 '{0}');
                min-height: 0px;
                border-radius: 4px;
            }} QScrollBar::add-line:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 '{0}',
                    stop: 0.5 '{0}',
                    stop: 1 '{0}');
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }} QScrollBar::sub-line:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 '{0}',
                    stop: 0.5 '{0}',
                    stop: 1 '{0}');
                height: 0 px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}'''.format(COL_SCROLLBAR, COL_SELECTED_BG, COL_PRIMARY_TEXT))
        self.setFocusPolicy(Qt.NoFocus)
        self.horizontalHeader().setHighlightSections(False)

        if no_header:
            self.horizontalHeader().setVisible(False)
        else:
            headerFont = QFont('Segoe UI', 12, QFont.DemiBold)
            headerFont.setStyleStrategy(QFont.PreferAntialias)
            self.horizontalHeader().setFont(headerFont)
            self.horizontalHeader().setStyleSheet('''::section{
                                                        Background-color: %s;
                                                        border: 0;
                                                        height: 36px;
                                                    }''' % COL_PRIMARY_GRAY)

    # TODO: change bg color for selected cell widgets
    # def _itemSelectionChanged(self):
    #     # change bgcolors
    #     for row in


def callback():
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # window = MainWindow(callback)
    # table = Table(15, 3)
    window = SmallWindow()
    window.show()
    sys.exit(app.exec_())
