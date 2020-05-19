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
from detectors.detectors import detectors_sorted, detectors
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
COL_SELECTED_BG = '#F0F7FF'
COL_GRAY_BORDER = '#B0B0B0'

SRC_BANNER_WHITE = os.getcwd() + r'\lankeeper\resources\images\white-banner.png'
SRC_LOADING_GIF = os.getcwd() + r'\lankeeper\resources\images\loading.gif'
SRC_INFO = os.getcwd() + r'\lankeeper\resources\images\info.png'
SRC_CHECKMARK = os.getcwd() + r'\lankeeper\resources\images\checkmark.png'

DATETIME_FORMAT = r'%m/%d/%Y at %H:%M:%S'
LABEL_STYLESHEET = f'font: 13px "Segoe UI"; color: {COL_PRIMARY_TEXT}'
LIST_STYLESHEET = '''QListWidget {{
                         font-size: 11px;
                         color: {0};
                         border: 1px solid {1};
                         padding: 8px;
                     }} QRadioButton {{
                         background-color: white;
                         margin: 4px;
                     }}'''.format(COL_PRIMARY_TEXT, COL_GRAY_BORDER)


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
        self.openMGRow = 0

        self.monitor_groups = []
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
        self.mgTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mgTable.doubleClicked.connect(self._mgSelected)
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
        self.deviceWindow = DeviceWindow(self._manager)  # Device window
        self.deviceWindow.initUi()
        self.mgmanageWindow = MGManageWindow(self._manager)  # Monitor groups management window
        self.mgmanageWindow.initUi()
        # self.mgEditWindow.mg = MonitorGroup('Default Group', ips=['10.100.102.3'], detectors=[0, 1, 2, 6], websites=['google.com', 'coolmathgames.com'])
        # self.mgEditWindow.show()
        self.mgEditWindow = MGEditWindow(self._manager)
        self.mgEditWindow.initUi()
        self.mgEditWindow.callback = self._mgEditWindowClosed

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
        self.device_ids = [d.id for d in devices]
        self.devicesTable.setRowCount(0)
        for row, device in enumerate(devices):
            self.devicesTable.insertRow(row)
            self.devicesTable.setItem(row, 1, QTableWidgetItem(device.name if device.name else device.ip))
            self.devicesTable.setItem(row, 2, QTableWidgetItem(device.vendor if device.vendor else device.mac))
            last_seen_txt = 'Scanning...' if loading else utils.time_ago(device.last_seen)
            self.devicesTable.setItem(row, 3, QTableWidgetItem(last_seen_txt))
            if device.new_device:
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
                self.devicesTable.setCellWidget(row, 0, iconWidget)

    def updateMGtable(self, data):
        """
        Update the monitor group table at the main window
        and updates the monitor group window
        data (list): [(id: int, mg: MonitorGroup), ...]
        """
        self.mg_ids, self.monitor_groups = list(zip(*data))
        self.mgTable.setRowCount(0)
        for row, mg in enumerate(self.monitor_groups):
            self.mgTable.insertRow(row)
            self.mgTable.setItem(row, 0, QTableWidgetItem(mg.name))
            self.mgTable.setItem(row, 1, QTableWidgetItem(str(len(mg.ips))))
        # Update the monitor group window
        self.mgmanageWindow.updateMonitorGroups(self.monitor_groups, self.mg_ids)

    def _deviceSelected(self, item):
        self.openDeviceId = self.device_ids[item.row()]
        self.deviceWindow.device = self._manager.get_device_data(self.openDeviceId)
        self.deviceWindow.mgs = self.monitor_groups
        self.deviceWindow.show()

    def _mgEditBtnClicked(self):
        self.mgmanageWindow.show()

    def _mgSelected(self, item):
        row = item.row()
        self.openMGRow = row
        self.mgEditWindow.mg = self.monitor_groups[row]
        self.mgEditWindow.show()

    def _mgEditWindowClosed(self, mg):
        self._manager.update_mg(self.openMGRow + 1, mg)

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
        self.mainFrame.layout().setContentsMargins(18, 10, 18, 0)
        self.mainFrame.layout().setSpacing(10)
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
    T_MONITORING = 'Monitoring'
    T_MON_NOTIF = 'Monitoring (1 new notification)'
    T_MON_NOTIFS = 'Monitoring (%s new notifications)'
    # Style

    def __init__(self, manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._manager = manager
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
        self._mgs = []
        self._mid_scan = False  # is it mid port scan

    def initUi(self):
        # <mainPanel>
        self.mainPanel.panelTitle = self.TITLE
        self.mainPanel.mainFrame.setLayout(QHBoxLayout())
        self.mainPanel.mainFrame.layout().setSpacing(14)
        #   <leftFrame>
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
        #   </leftFrame>
        #   <midFrame>
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
        self.scanBtn.linkActivated.connect(self._scanBtnClicked)
        self.midFrame.layout().addStretch()
        #   </midFrame>
        #   <rightFrame>
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
        #   </rightFrame>
        # </mainPanel>
        # <monPanel>
        self.monPanel = Panel()
        self.mainFrame.layout().addWidget(self.monPanel)
        self.monPanel.panelTitle = self.T_MONITORING
        self.monPanel.mainFrame.setLayout(QVBoxLayout())
        self.monPanel.mainFrame.layout().setSpacing(16)
        #   <monReportsFrame>
        self.monReportsFrame = QFrame()
        self.monPanel.mainFrame.layout().addWidget(self.monReportsFrame)
        self.monReportsFrame.setLayout(QVBoxLayout())
        self.monReportsFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.monReportsFrame.layout().setSpacing(8)
        self.monTrafficLabel = IconLabel('This device is sending potentially malicious traffic (TCP port scan) and has been blocked. <a href="#">Unblock<a/>', IconLabel.INFO)
        self.monReportsFrame.layout().addWidget(self.monTrafficLabel)
        self.monProcessLabel = IconLabel('This device is running a process (cmd.exe) that it has never run before. <a href="#">Whitelist cmd.exe</a>', IconLabel.INFO)
        self.monReportsFrame.layout().addWidget(self.monProcessLabel)
        self.monDriveLabel = IconLabel('An unrecognized drive (SanDisk Cruzer) was inserted to this device. <a href="#">Whitelist Sandisk Cruzer</a>', IconLabel.INFO)
        self.monReportsFrame.layout().addWidget(self.monDriveLabel)
        #   </monReportsFrame>
        #   <monGroupsFrame>
        self.monGroupsFrame = QFrame()
        self.monPanel.mainFrame.layout().addWidget(self.monGroupsFrame)
        self.monGroupsFrame.setLayout(QVBoxLayout())
        self.monGroupsFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.monGroupsFrame.layout().setSpacing(8)
        self.monGroupsLabel = QLabel('Assign to a monitoring group')
        self.monGroupsFrame.layout().addWidget(self.monGroupsLabel)
        self.monGroupsLabel.setStyleSheet(LABEL_STYLESHEET)
        #     <monGroupsList>
        self.monGroupsList = QListWidget()
        self.monGroupsFrame.layout().addWidget(self.monGroupsList)
        self.monGroupsList.setStyleSheet(LIST_STYLESHEET)
        self.monGroupsList.setSpacing(0)
        #     </monGroupsList>
        #   </monGroupsFrame>
        # </monPanel>

    def scanDone(self):
        """This method should be called from the manager module
        when the detailed scan (ports and os) is done."""
        self._mid_scan = False

    def composeText(self, title, value):
        return f'<b>{title}:</b> {value}'

    def composeLabel(self, text) -> QLabel:
        label = QLabel(text=text)
        label.setStyleSheet(LABEL_STYLESHEET)
        return label

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
        if not self._mid_scan:
            self.scanBtn.setText('<a href="#">(Scan again)</a>' if (d.ports or d.os) else '<a href="#">(Scan)</a>')
            self.scanBtn.linkActivated.connect(self._scanBtnClicked)
        # update monitoring panel
        self._updateMGTable()

    @property
    def mgs(self) -> list:
        return self._mgs

    @mgs.setter
    def mgs(self, value: list):
        self._mgs = value
        self._updateMGTable()

    def _scanBtnClicked(self, e):
        self._mid_scan = True
        self.scanBtn.setText('(Scanning...)')
        self.scanBtn.linkActivated.disconnect()
        self._manager.scan_ports_os(self._device.ip)

    def _updateMGTable(self):
        self.monGroupsList.clear()
        for row, mg in enumerate(self._mgs):
            item = QListWidgetItem()
            self.monGroupsList.addItem(item)
            radio = QRadioButton(mg.name)
            self.monGroupsList.setItemWidget(item, radio)
            if self._device and row == self._device.mg_id - 1:
                radio.setChecked(True)
            radio.clicked.connect(lambda *args, row=row: self._monGroupSelected(row))
            item.setSizeHint(QSize(item.sizeHint().width(), 22))
            item.setFlags(Qt.ItemIsEnabled)

    def _monGroupSelected(self, row):
        print(self._mgs[row])
        self._manager.update_device_mg(self._device.id, row + 1)


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
        self._editing_mg_row = 0

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
        # MG edit window
        self.mgEditWindow = MGEditWindow(self._manager)
        self.mgEditWindow.initUi()
        self.mgEditWindow.callback = self._mgEditWindowClosed

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
            edit.linkActivated.connect(lambda *args, row=row: self._mgEditBtnClicked(row))
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

    def _mgEditBtnClicked(self, row):
        self._editing_mg_row = row
        self.mgEditWindow.mg = self._monitor_groups[row]
        self.mgEditWindow.show()

    def _mgEditWindowClosed(self, mg):
        if self._editing_mg_row >= len(self._monitor_groups):
            self._manager.add_mg(mg)
        else:
            self._manager.update_mg(self._editing_mg_row + 1, mg)

    def _selectAllBtnClicked(self, e):
        self.mgTable.selectAll()

    def _deselectAllBtnClicked(self, e):
        self.mgTable.clearSelection()

    def _deleteBtnClicked(self, e):
        self._manager.delete_mgs([self._monitor_groups_ids[x.row()]
                                  for x in self.mgTable.selectionModel().selectedRows()])

    def _newBtnClicked(self, e):
        self._editing_mg_row = len(self._monitor_groups)
        self.mgEditWindow.mg = MonitorGroup('New Monitor Group')
        self.mgEditWindow.show()

    def _okBtnClicked(self, e):
        self.close()


class MGEditWindow(SmallWindow):

    MAIN_TITLE = 'Monitoring group settings (%s)'

    def __init__(self, manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = lambda *_: None
        self._manager = manager
        self._mg = None
        self._mid_check = True
        self._web_row_editing = 0  # which website rule we are currently editing

    def initUi(self):
        self.setMinimumWidth(540)
        self.mainPanel.panelTitle = self.MAIN_TITLE % ''
        self.mainPanel.mainFrame.setLayout(QVBoxLayout())
        # self.mainPanel.mainFrame.layout().setContentsMargins(22, 20, 22, 0)
        self.mainPanel.mainFrame.layout().setSpacing(16)
        # <nameFrame>
        self.nameFrame = QFrame()
        self.mainPanel.mainFrame.layout().addWidget(self.nameFrame)
        self.nameFrame.setLayout(QHBoxLayout())
        self.nameFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.nameFrame.layout().setSpacing(8)
        self.nameLabel = QLabel('Name: ')
        self.nameFrame.layout().addWidget(self.nameLabel)
        self.nameLabel.setStyleSheet(LABEL_STYLESHEET)
        self.nameEntry = QLineEdit()
        self.nameFrame.layout().addWidget(self.nameEntry)
        self.nameEntry.textChanged.connect(self._nameEntryTextChanged)
        self.nameEntry.returnPressed.connect(self._nameApplyBtnClicked)
        self.nameResetBtn = QPushButton('Reset')
        self.nameFrame.layout().addWidget(self.nameResetBtn)
        self.nameResetBtn.clicked.connect(self._nameResetBtnClicked)
        self.nameApplyBtn = QPushButton('Apply')
        self.nameFrame.layout().addWidget(self.nameApplyBtn)
        self.nameApplyBtn.clicked.connect(self._nameApplyBtnClicked)
        # </nameFrame>
        # <detectorsFrame>
        self.detectorsFrame = QFrame()
        self.mainPanel.mainFrame.layout().addWidget(self.detectorsFrame)
        self.detectorsFrame.setLayout(QVBoxLayout())
        self.detectorsFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.detectorsFrame.layout().setSpacing(8)
        self.detectorsLabel = QLabel('Assign detectors (notify and block these scenarios)')
        self.detectorsFrame.layout().addWidget(self.detectorsLabel)
        self.detectorsLabel.setStyleSheet(LABEL_STYLESHEET)
        #   <detectorsList>
        self.detectorsList = QListWidget()
        self.detectorsFrame.layout().addWidget(self.detectorsList)
        self.detectorsList.itemChanged.connect(self._detectorsListItemChanged)
        self.detectorsList.setStyleSheet(LIST_STYLESHEET)
        self.detectorsList.setSpacing(2)
        for detector in detectors:
            self.detectorsList.addItem(detector.name)
        for i in range(self.detectorsList.count()):
            item = self.detectorsList.item(i)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
        #   </detectorsList>
        #   <detectorsControlsFrame>
        self.detectorsControlsFrame = QFrame()
        self.detectorsFrame.layout().addWidget(self.detectorsControlsFrame)
        self.detectorsControlsFrame.setLayout(QHBoxLayout())
        self.detectorsControlsFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.detectorsControlsFrame.layout().setSpacing(8)
        self.detectorsSelectAllBtn = QPushButton('Select All')
        self.detectorsControlsFrame.layout().addWidget(self.detectorsSelectAllBtn)
        self.detectorsSelectAllBtn.clicked.connect(self._detectorsSelectAllBtnClicked)
        self.detectorsDeselectBtn = QPushButton('Deselect All')
        self.detectorsControlsFrame.layout().addWidget(self.detectorsDeselectBtn)
        self.detectorsDeselectBtn.clicked.connect(self._detectorsDeselectBtnClicked)
        self.detectorsControlsFrame.layout().addStretch()
        #   </detectorsControlsFrame>
        # </detectorsFrame>
        # <webPanel>
        self.webPanel = Panel(untitled=True)
        self.mainFrame.layout().addWidget(self.webPanel)
        self.webPanel.mainFrame.setLayout(QVBoxLayout())
        # self.webPanel.mainFrame.layout().setContentsMargins(22, 20, 22, 0)
        self.webPanel.mainFrame.layout().setSpacing(8)
        self.webLabel = QLabel('Notify on forbidden website access')
        self.webPanel.mainFrame.layout().addWidget(self.webLabel)
        self.webLabel.setStyleSheet(LABEL_STYLESHEET)
        self.webTable = Table(1, 3, multi_select=True)
        self.webPanel.mainFrame.layout().addWidget(self.webTable)
        self.webTable.setHorizontalHeaderLabels(['', 'Address', ''])
        self.webTable.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.webTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.webTable.horizontalHeader().setStretchLastSection(True)
        self.webTable.selectionModel().selectionChanged.connect(self._webItemSelectionChanged)
        self.webControlsFrame = QFrame()
        self.webPanel.mainFrame.layout().addWidget(self.webControlsFrame)
        self.webControlsFrame.setLayout(QHBoxLayout())
        self.webControlsFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.webControlsFrame.layout().setSpacing(8)
        self.webSelectAllBtn = QPushButton('Select all')
        self.webControlsFrame.layout().addWidget(self.webSelectAllBtn)
        self.webSelectAllBtn.clicked.connect(self._webSelectAllBtnClicked)
        self.webDeselectBtn = QPushButton('Deselect all')
        self.webControlsFrame.layout().addWidget(self.webDeselectBtn)
        self.webDeselectBtn.setEnabled(False)
        self.webDeselectBtn.clicked.connect(self._webDeselectBtnClicked)
        self.webDeleteBtn = QPushButton('Delete rules')
        self.webControlsFrame.layout().addWidget(self.webDeleteBtn)
        self.webDeleteBtn.setEnabled(False)
        self.webDeleteBtn.clicked.connect(self._webDeleteBtnClicked)
        self.webNewButton = QPushButton('New...')
        self.webControlsFrame.layout().addWidget(self.webNewButton)
        self.webNewButton.clicked.connect(self._webNewBtnClicked)
        self.webControlsFrame.layout().addStretch()
        self.okBtn = QPushButton('OK')
        self.webControlsFrame.layout().addWidget(self.okBtn)
        self.okBtn.clicked.connect(self._okBtnClicked)
        # </webPanel>
        self._mid_check = False
        self.websiteRuleEditWindow = WebsiteRuleEditWindow()
        self.websiteRuleEditWindow.initUi()
        self.websiteRuleEditWindow.callback = self._webRuleWindowClosed

    @property
    def mg(self):
        return self._mg

    @mg.setter
    def mg(self, value):
        self._mg = value
        # update name
        self.mainPanel.panelTitle = self.MAIN_TITLE % self._mg.name
        self.nameEntry.setText(self._mg.name)
        # update detectors
        self._mid_check = True  # to not trigger the check event
        for i in range(self.detectorsList.count()):
            state = Qt.Checked if i in self._mg.detectors else Qt.Unchecked
            self.detectorsList.item(i).setCheckState(state)
        self._mid_check = False
        # update website rules
        self.webTable.setRowCount(len(self._mg.websites))
        for row, addr in enumerate(self._mg.websites):
            addrWidget = QWidget()
            addrWidget.setLayout(QHBoxLayout())
            addrWidget.layout().setAlignment(Qt.AlignCenter)
            addrWidget.layout().setContentsMargins(0, 0, 0, 0)
            addrWidget.setStyleSheet('background-color:rgba(0,0,0,0);')
            addrLabel = QLabel(addr)
            addrWidget.layout().addWidget(addrLabel)
            editWidget = QWidget()
            editWidget.setLayout(QHBoxLayout())
            editWidget.layout().setAlignment(Qt.AlignCenter)
            editWidget.layout().setContentsMargins(0, 0, 0, 0)
            editLabel = QLabel('<a href="#">Edit</a>')
            editWidget.layout().addWidget(editLabel)
            editLabel.linkActivated.connect(lambda *args, row=row: self._webEditClicked(row))
            # self.webTable.setIndexWidget(self.webTable.model().index(row, 2), editWidget)
            editWidget.setStyleSheet('background-color:rgba(0,0,0,0);')
            self.webTable.setCellWidget(row, 1, addrWidget)
            self.webTable.setCellWidget(row, 2, editWidget)

    def _nameEntryTextChanged(self, e):
        name = str(self.nameEntry.text()).strip()
        if not name:
            self.nameApplyBtn.setEnabled(False)
            self.nameResetBtn.setEnabled(True)
            return
        if name == self._mg.name:
            self.nameApplyBtn.setEnabled(False)
            self.nameResetBtn.setEnabled(False)
        else:
            self.nameApplyBtn.setEnabled(True)
            self.nameResetBtn.setEnabled(True)

    def _nameResetBtnClicked(self, e):
        self.nameEntry.setText(self._mg.name)

    def _nameApplyBtnClicked(self, *args):
        self._mg.name = str(self.nameEntry.text())
        # trigger update
        self.mg = self._mg

    def _detectorsListItemChanged(self, e):
        if self._mid_check:  # do not trigger multiple times when programatically checking items
            return
        checked = [bool(self.detectorsList.item(i).checkState()) for i in range(self.detectorsList.count())]
        checked_ids = [i for i, x in enumerate(checked) if x]
        self.detectorsSelectAllBtn.setEnabled(len(checked_ids) < len(checked))
        self.detectorsDeselectBtn.setEnabled(bool(checked_ids))
        self._mg.detectors = checked_ids

    def _detectorsSelectAllBtnClicked(self, e):
        self._mid_check = True
        for i in range(self.detectorsList.count()):
            self.detectorsList.item(i).setCheckState(Qt.Checked)
        self._mid_check = False
        self._detectorsListItemChanged(None)

    def _detectorsDeselectBtnClicked(self, e):
        self._mid_check = True
        for i in range(self.detectorsList.count()):
            self.detectorsList.item(i).setCheckState(Qt.Unchecked)
        self._mid_check = False
        self._detectorsListItemChanged(None)

    def _webEditClicked(self, row):
        self._web_row_editing = row
        self.websiteRuleEditWindow.address = self._mg.websites[row]
        self.websiteRuleEditWindow.show()

    def _webRuleWindowClosed(self, address):
        if not address:
            return
        try:
            self._mg.websites[self._web_row_editing] = address
        except IndexError:
            self._mg.websites.append(address)
        self.mg = self._mg  # update the table

    def _webItemSelectionChanged(self, selection):
        indexes = self.webTable.selectedIndexes()
        count = len([x for x in indexes if x.column() == 1])
        print(f'{count}')
        self.webDeselectBtn.setEnabled(count)
        self.webSelectAllBtn.setEnabled(count != self.webTable.rowCount())
        if count > 1:
            deltxt = f'Delete {count} rules'
        elif count:
            deltxt = 'Delete 1 rules'
        else:
            deltxt = 'Delete rules'
        self.webDeleteBtn.setText(deltxt)
        self.webDeleteBtn.setEnabled(count)

    def _webSelectAllBtnClicked(self, e):
        self.webTable.selectAll()

    def _webDeselectBtnClicked(self, e):
        self.webTable.clearSelection()

    def _webDeleteBtnClicked(self, e):
        for x in self.webTable.selectionModel().selectedRows():
            del self._mg.websites[x.row()]
        self.mg = self._mg

    def _webNewBtnClicked(self, e):
        self._web_row_editing = len(self._mg.websites)
        self.websiteRuleEditWindow.address = ''
        self.websiteRuleEditWindow.show()

    def _okBtnClicked(self, e):
        self.callback(self._mg)
        self.close()


class WebsiteRuleEditWindow (SmallWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = lambda _: None
        self._address = ''
        self._old_address = ''

    def initUi(self):
        self.mainPanel.panelTitle = 'Configure forbidden website'
        self.mainPanel.mainFrame.setLayout(QVBoxLayout())
        self.addrLabel = QLabel('Notify when trying to access this address:')
        self.mainPanel.mainFrame.layout().addWidget(self.addrLabel)
        self.addrLabel.setStyleSheet(LABEL_STYLESHEET)
        self.addrEntry = QLineEdit()
        self.mainPanel.mainFrame.layout().addWidget(self.addrEntry)
        self.addrEntry.setPlaceholderText('www.example.com OR 11.12.13.14')
        self.addrEntry.textChanged.connect(self._addrEntryTextChanged)
        self.addrEntry.returnPressed.connect(self._addrEntryReturnPressed)
        self.mainPanel.mainFrame.layout().addStretch()
        # <bottomFrame>
        self.bottomFrame = QFrame()
        self.mainPanel.mainFrame.layout().addWidget(self.bottomFrame)
        self.bottomFrame.setLayout(QHBoxLayout())
        self.bottomFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.bottomFrame.layout().setSpacing(8)
        self.bottomFrame.layout().addStretch()
        self.cancelBtn = QPushButton('Cancel')
        self.bottomFrame.layout().addWidget(self.cancelBtn)
        self.cancelBtn.clicked.connect(self._cancelBtnClicked)
        self.okBtn = QPushButton('OK')
        self.bottomFrame.layout().addWidget(self.okBtn)
        self.okBtn.clicked.connect(self._okBtnClicked)
        self.okBtn.setDefault(True)
        # </bottomFrame>

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value
        self._old_address = value
        self.addrEntry.setText(self._address)

    def _addrEntryTextChanged(self, e):
        addr = str(self.addrEntry.text())
        self._address = addr
        self.okBtn.setEnabled(bool(addr))

    def _addrEntryReturnPressed(self):
        self._okBtnClicked(None)

    def _cancelBtnClicked(self, e):
        self.callback(self._old_address)
        self.close()

    def _okBtnClicked(self, e):
        self.callback(self._address)
        self.close()


class Panel (QFrame):

    def __init__(self, *args, untitled=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._panelTitle = 'Panel'

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(15, 0, 15, 20)
        self.setStyleSheet('QFrame {background-color: white; border-radius: 2px;}')
        shadow = QGraphicsDropShadowEffect(blurRadius=6, xOffset=2, yOffset=3, color=QColor(0, 0, 0, int(0.05*255)))
        self.setGraphicsEffect(shadow)
        # <titleFrame>
        self.titleFrame = QFrame()
        if not untitled:
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


class IconLabel (QFrame):

    SIZE = 16  # width and height in pixels

    # Icon types
    CHECKMARK = 0
    INFO = 1
    WARNING = 2
    CRITICAL = 3

    # Icon sources
    SRCS = [
        SRC_CHECKMARK,
        SRC_INFO,
        r'',
        r''
    ]

    def __init__(self, text, iconType, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUi()
        self.setText(text)
        self.setIconType(iconType)

    def initUi(self):
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(8)
        # <icon>
        self.icon = QLabel()
        self.layout().addWidget(self.icon)
        # </icon>
        # <label>
        self.label = QLabel()
        self.layout().addWidget(self.label)
        self.label.setStyleSheet(LABEL_STYLESHEET)
        # </label>
        self.layout().addStretch()

    # Implement functions in Qt style
    def setText(self, text):
        self.label.setText(text)

    def setIconType(self, iconType):
        pixmap = QPixmap(self.SRCS[iconType])
        pixmap = pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon.setPixmap(pixmap)


def callback():
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # window = MainWindow(callback)
    # table = Table(15, 3)
    window = SmallWindow()
    window.show()
    sys.exit(app.exec_())
