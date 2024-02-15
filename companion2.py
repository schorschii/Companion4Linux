#!/usr/bin/python3

# companion2.py
# GNU GENERAL PUBLIC LICENSE, Version 3
# (c) Georg Sieber 2020
# github.com/schorschii

# This script emulates the functionality of the Atlassian Companion App 1.0.0 (Windows/Mac) for usage on Linux clients.
# Please see README.md for installation instructions.


from urllib.parse import unquote, urlparse
import urllib.request
import pyinotify
import pathlib
import hashlib
import requests
import subprocess
import gettext
import json
import sys, os

import gi
gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '3.0')
from gi.repository import Notify, Gtk


APP_NAME        = "Companion4Linux"
PROTOCOL_SCHEME = "atlassian-companion:"
DOWNLOAD_DIR    = str(pathlib.Path.home()) + "/.cache/companion/tmp" # temp dir for downloading files


# file change handler class
class FileChangedHandler(pyinotify.ProcessEvent):
    def my_init(self, downloadUrl, uploadUrl, fileName, filePath, fileMd5, **kwargs):
        self._fileUrl = downloadUrl
        self._uploadUrl = uploadUrl
        self._fileName = fileName
        self._filePath = os.path.abspath(filePath)
        self._fileMd5 = fileMd5

    # IN_CLOSE to support Softmaker Office
    # (Does not modify the file but creates a temporary file, then deletes
    # the original and renames the temp file to the original file name.
    # That's why IN_MODIFY is not called.)
    def process_IN_CLOSE_WRITE(self, event):
        self.process_IN_MODIFY(event=event)

    # IN_MODIFY to support LibreOffice
    # (LibreOffice modifies the file directly.)
    def process_IN_MODIFY(self, event):
        if(self._filePath == event.pathname):
            newFileMd5 = md5(event.pathname)
            if(self._fileMd5 == newFileMd5):
                print("[CONTENT NOT CHANGED, IGNORING]  "+event.pathname)
            else:
                print("[CONTENT CHANGED, INFORM CONFLUENCE]  "+event.pathname)
                self._fileMd5 = newFileMd5

                # now upload the modified file
                print("[UPLOAD]  " + self._fileName + " to: " + self._uploadUrl)
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

                # show desktop notification
                notificationFinished = Notify.Notification.new(gettext.gettext("Uploading file..."), self._fileName)
                notificationFinished.show()

                with open(self._filePath, 'rb') as f:
                    result = requests.post(
                        self._uploadUrl,
                        files={
                            "comment": ("comment", "Uploaded by Companion for Linux (yay!)"),
                            "file": (self._fileName, f)
                        },
                        headers=headers
                    )
                    print(result, result.text)

                    # update desktop notification
                    if(result.status_code == 200):
                        notificationFinished.update(gettext.gettext("File uploaded successfully"), self._fileName)
                    else:
                        notificationFinished.update(gettext.gettext("File upload failed"), self._fileName)
                    notificationFinished.show()

# hashing functions
def md5(fname):
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()

def endFileWatcher(notification, event):
    if(hasattr(notification, "notifier")):
        notification.notifier.stop()
    Gtk.main_quit()

def notificationClosed(notification):
    if(hasattr(notification, "notifier")):
        notification.notifier.stop()
    Gtk.main_quit()

# main program
def main():
    # init notifications
    Notify.init(APP_NAME)

    # init translations
    if(os.path.isdir("locale")):
        # use translations in working dir if avail, otherwise /usr/share/locale is used
        gettext.bindtextdomain(APP_NAME, "locale")
        print("using local locales")
    else:
        print("using global locales")
    gettext.textdomain(APP_NAME)

    # check parameter
    urlToHandle = None
    for arg in sys.argv:
        if(arg.startswith(PROTOCOL_SCHEME)):
            urlToHandle = arg
    if(urlToHandle == None):
        print("[MAIN]  Error: no valid '"+PROTOCOL_SCHEME+"' scheme parameter given.")
        exit(1)

    # create temporary directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # parse given companion URL
    print("[HANDLE URL]  "+urlToHandle)
    protocolPayload = unquote(urlToHandle).replace(PROTOCOL_SCHEME, "")
    protocolPayloadData = json.loads(protocolPayload)
    print("[METADATA-LINK]  "+protocolPayloadData["link"])

    # download metadata from provided link
    try:
        metadataString = urllib.request.urlopen(protocolPayloadData["link"]).read()
        metadata = json.loads(metadataString)
    except Exception as e:
        print("[ERROR]  "+str(e))
        exit(1)
    print("[METADATA]  "+str(metadata))

    # start file download
    try:
        filePath = DOWNLOAD_DIR + "/" + metadata["fileName"]
        print("[DOWNLOAD]  "+metadata["downloadUrl"]+"  ->  "+filePath)
        urllib.request.urlretrieve(metadata["downloadUrl"], filePath)
        print("[FINISHED]  "+filePath)
    except Exception as e:
        print("[ERROR]  "+str(e))
        exit(1)

    # start application
    print("[OPEN]  "+filePath)
    subprocess.call(["xdg-open", filePath])

    # set up file watcher
    print("[SETUP FILE WATCHER]  " + DOWNLOAD_DIR)
    wm = pyinotify.WatchManager()
    wm.add_watch(DOWNLOAD_DIR, pyinotify.IN_MODIFY | pyinotify.IN_CLOSE_WRITE)
    notifier = pyinotify.ThreadedNotifier(wm,
        FileChangedHandler(
            #fileId = metadata["fileId"],
            fileName = metadata["fileName"],
            filePath = filePath,
            #mimeType = metadata["mimeType"],
            downloadUrl = metadata["downloadUrl"],
            #companionActionCallbackUrl = metadata["companionActionCallbackUrl"],
            uploadUrl = metadata["uploadUrl"],
            fileMd5 = md5(filePath)
        )
    )
    notifier.start()

    # show GUI
    print("[SHOW NOTIFICATION]")
    notificationWatching = Notify.Notification.new(
        gettext.gettext("Companion watching for changes"),
        metadata["fileName"]
    )
    notificationWatching.connect("closed", notificationClosed)
    notificationWatching.add_action("clicked", gettext.gettext("End file monitoring"), endFileWatcher)
    notificationWatching.show()
    Gtk.main()

    # kill file watcher after notification closed
    print("[EXIT]")
    notifier.stop()
    exit(0)

if __name__ == '__main__':
    main()
