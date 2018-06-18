"""
module that helps with everyday life :)
"""

import os
import sys
import csv
import re
import time
import logging
import io
import functools
import itertools
import threading
from itertools import zip_longest
import getpass
import traceback
import smtplib
from email.message import EmailMessage
import pymssql
from openpyxl import load_workbook
import sqlanydb
import xlrd
import paramiko
import pendulum

# TODO: * write docstrings
#       * remove unneccasary comments
#       * translate doctrings written in Swedish to English


def sftp_download(path, files, host, port, username, password):
    """
    write docstring
    """
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        for i in files:
            filepath = '/' + i
            localpath = path + i
            sftp.get(filepath, localpath)
        sftp.close()
    except:
        print('hej')
        sftp.close()
        raise
