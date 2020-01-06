# LANKeeper (https://github.com/danielperr/LANKeeper)
# Remote windows process handling

import os


def list_tasks(ip, username, password=''):
    return os.popen('TASKLIST /S %s /U %s /P %s' % (ip, username, password)).read()


def kill_task_by_pid(ip, pid, username, password=''):
    return os.popen('TASKKILL /PID %s /S %s /U %s /P %s /F' % (pid, ip, username, password)).read()


def kill_task_by_imagename(ip, imagename, username, password=''):
    return os.popen('TASKKILL /IM %s /S %s /U %s /P %s /F' % (imagename, ip, username, password)).read()
