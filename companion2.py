#!/usr/bin/python3

# companion2.py
# GNU GENERAL PUBLIC LICENSE, Version 3
# (c) Georg Sieber 2020
# github.com/schorschii

# This script emulates the functionality of the Atlassian Companion App 1.0.0 (Windows/Mac) for usage on Linux clients.
# Please see README.md for installation instructions.


from urllib.parse import unquote
from urllib.parse import urlparse
import urllib.request
import pyinotify
import pathlib
import hashlib
import requests
import subprocess
import json
import time
import sys
import os
import wx

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify


APP_NAME        = "Companion App"
PROTOCOL_SCHEME = "atlassian-companion:"
DOWNLOAD_DIR    = str(pathlib.Path.home()) + "/.cache/companion/tmp" # temp dir for downloading files

LOG_FILE        = None # enter a file path here to activate logging
LOG_FILE_HANDLE = None

# tiny logging function, because this script is invoked from the web browser, so we do not see the console output
def log(str):
    global LOG_FILE
    global LOG_FILE_HANDLE
    if(LOG_FILE == None or LOG_FILE == ""):
        print(str)
        return
    if(LOG_FILE_HANDLE == None):
        LOG_FILE_HANDLE = open(LOG_FILE, "a+")
        LOG_FILE_HANDLE.write("\n\n")
    LOG_FILE_HANDLE.write(str+"\n")

# file change handler class
class FileChangedHandler(pyinotify.ProcessEvent):
    def my_init(self, dict):
        self._fileUrl = dict["downloadUrl"]
        self._uploadUrl = dict["uploadUrl"]
        self._fileName = dict["fileName"]
        self._filePath = os.path.abspath(dict["filePath"])
        self._fileMd5 = dict["fileMd5"]

    # IN_CLOSE to support FreeOffice
    # (FreeOffice does not modify the file but creates a temporary file,
    # then deletes the original and renames the temp file to the original file name.
    # That's why IN_MODIFY is not called when using FreeOffice.)
    def process_IN_CLOSE_WRITE(self, event):
        self.process_IN_MODIFY(event=event)

    # IN_MODIFY to support LibreOffice
    # (LibreOffice modifies the file directly.)
    def process_IN_MODIFY(self, event):
        if(self._filePath == event.pathname):
            log("[FILE EVENT]  matching file event: " + event.pathname)
            newFileMd5 = md5(event.pathname)
            if(self._fileMd5 == newFileMd5):
                log("[FILE EVENT]  file content not changed, ignoring")
            else:
                log("[FILE EVENT]  file content changed, inform confluence")
                self._fileMd5 = newFileMd5

                # now upload the modified file
                log("[UPLOAD]  " + self._fileName + " to: " + self._uploadUrl)
                parsed_uri = urlparse(self._uploadUrl)
                host = '{uri.netloc}'.format(uri=parsed_uri)
                origin = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
                headers = {
                    "Host": host,
                    "origin": origin,
                    "Accept": None,
                    "Accept-Language": "de",
                    "X-Atlassian-Token": "nocheck"
                    #"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) AtlassianCompanion/1.0.0 Chrome/61.0.3163.100 Electron/2.1.0-unsupported.20180809 Safari/537.36"
                }
                with open(self._filePath, 'rb') as f:
                    result = requests.post(
                        self._uploadUrl,
                        files={
                            "comment": ("comment", "Uploaded by Companion for Linux (yay!)"),
                            "file": (self._fileName, f)
                        },
                        headers=headers
                    )
                    log(result)
                    log(result.text)

                    # show desktop notification
                    if(result.status_code == 200):
                        notificationFinished = Notify.Notification.new(APP_NAME, "File Uploaded Successfully")
                    else:
                        notificationFinished = Notify.Notification.new(APP_NAME, "File Upload Failed")
                    notificationFinished.show()

# hashing functions
def md5(fname):
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()

# companion window definition
class CompanionWindow(wx.Frame):
    def __init__(self, fileName):
        self.fileName = fileName
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        super(CompanionWindow, self).__init__(None, style=style)
        self.InitUI()

    def InitUI(self):
        # Window Content
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(panel, wx.ID_ANY, "Watching for changes in: " + self.fileName)
        self.Bind(wx.EVT_BUTTON, self.OnClickClose, label)
        vbox.Add(label, wx.ID_ANY, wx.EXPAND | wx.ALL, 20)

        button = wx.Button(panel, wx.ID_ANY, "End Editing")
        self.Bind(wx.EVT_BUTTON, self.OnClickClose, button)
        vbox.Add(button, wx.ID_ANY, wx.EXPAND | wx.ALL, 20)

        panel.SetSizer(vbox)

        # Window Settings
        self.SetSize(300, 200)
        self.SetMinSize((300, 200))
        self.SetTitle("Companion App")
        self.AlignToBottomRight()

    def AlignToBottomRight(self):
        dw, dh = wx.DisplaySize()
        w, h = self.GetSize()
        x = dw - w
        y = dh - h
        self.SetPosition((x, y))

    def OnClickClose(self, e):
        self.Close()

# main program
def main():
    Notify.init(APP_NAME)
    urlToHandle = None

    # check parameter
    for arg in sys.argv:
        if(arg.startswith(PROTOCOL_SCHEME)):
            urlToHandle = arg
    if(urlToHandle == None):
        log("[MAIN]  Error: no valid '"+PROTOCOL_SCHEME+"' scheme parameter given.")
        exit(1)

    # create temporary directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # parse given companion URL
    log("[HANDLE URL]  "+urlToHandle)
    protocolPayload = unquote(urlToHandle).replace(PROTOCOL_SCHEME, "")
    protocolPayloadData = json.loads(protocolPayload)
    log("[METADATA-LINK]  "+protocolPayloadData["link"])

    # download metadata from provided link
    try:
        metadataString = urllib.request.urlopen(protocolPayloadData["link"]).read()
        metadata = json.loads(metadataString)
    except Exception as e:
        log("[GET METADATA ERROR]  "+str(e))
        exit(1)
    log("[METADATA]  "+str(metadata))

    # start file download
    try:
        filePath = DOWNLOAD_DIR + "/" + metadata["fileName"]
        log("[START DOWNLOAD TO]  "+filePath)
        urllib.request.urlretrieve(metadata["downloadUrl"], filePath)
        log("[DOWNLOAD FINISHED]  "+filePath)
    except Exception as e:
        log("[DOWNLOAD ERROR]  "+str(e))
        exit(1)

    # start application
    log("[LAUNCH]  "+filePath)
    subprocess.call(["xdg-open", filePath])

    # set up file watcher
    log("[SETUP FILE WATCHER]  " + DOWNLOAD_DIR)
    wm = pyinotify.WatchManager()
    wm.add_watch(DOWNLOAD_DIR, pyinotify.IN_MODIFY | pyinotify.IN_CLOSE_WRITE)
    notifier = pyinotify.ThreadedNotifier(wm,
        FileChangedHandler( dict={
            "fileId": metadata["fileId"],
            "fileName": metadata["fileName"],
            "filePath": filePath,
            "mimeType": metadata["mimeType"],
            "downloadUrl": metadata["downloadUrl"],
            "companionActionCallbackUrl": metadata["companionActionCallbackUrl"],
            "uploadUrl": metadata["uploadUrl"],
            "fileMd5": md5(filePath)
        })
    )
    notifier.start()

    # show GUI
    log("[SHOW GUI]")
    app = wx.App()
    window = CompanionWindow(metadata["fileName"])
    window.Show()
    app.MainLoop()

    # kill file watcher after window closed
    log("[EXIT]")
    notifier.stop()
    exit(0)

if __name__ == '__main__':
    main()
