#!/usr/bin/python3

# companion.py
# (c) Georg Sieber 2019
# github.com/schorschii

# this script emulates the functionality of the Atlassian Companion App (Windows/Mac) for usage on Linux clients
# please see README.md for installation instructions

# IMPORTANT NOTE: this script is currently EXPERIMENTAL and therefore not intended for productive usage!


from subprocess import check_output
from urllib.parse import urlparse
import asyncio
import pathlib
import ssl
import websockets
import json
import urllib.request
import subprocess
import time
import requests
import uuid
import pyinotify
import os

ALLOWED_SITE = "Übersicht" # please replace with your confluence site name to allow access
DOWNLOAD_DIR = "temp" # temp dir for downloading files

FILES = [] # temp storage for downloaded file metadata

async def handleJson(websocket, requestjson):
    global FILES
    global DOWNLOAD_DIR
    global ALLOWED_SITE
    responsejson = {}
    if(requestjson["type"] == "authentication"):
        if(requestjson["payload"]["payload"]["siteTitle"] == ALLOWED_SITE):
            print("ACCEPTED SITE: " + requestjson["payload"]["payload"]["siteTitle"])
            responsejson = {
                "requestID": requestjson["requestID"],
                "type": "authentication-status",
                "payload": "ACCEPTED"
            }
        else:
            print("REJECTED SITE: " + requestjson["payload"]["payload"]["siteTitle"])
            responsejson = {
                "requestID": requestjson["requestID"],
                "type": "authentication-status",
                "payload": "REJECTED"
            }
        await send(websocket, json.dumps(responsejson))

    elif(requestjson["type"] == "new-transaction" and requestjson["payload"]["transactionType"] == "file"):
        newUuid = str(uuid.uuid4())
        print("new uuid: "+newUuid)
        responsejson = {
            "requestID": requestjson["requestID"],
            "payload": newUuid
        }
        await send(websocket, json.dumps(responsejson))

    elif(requestjson["type"] == "list-apps"):
        responsejson = {
            "requestID": requestjson["requestID"],
            "payload": [{
                "displayName": "Linux (yay!)",
                "imageURI": "",
                "id": "2a2fe73b2ed43010dba316046ce79923",
                "windowsStore": False
            }]
        }
        await send(websocket, json.dumps(responsejson))

    elif(requestjson["type"] == "launch-file-in-app"):
        appId = requestjson["payload"]["applicationID"]
        transId = requestjson["transactionID"]
        fileUrl = requestjson["payload"]["fileURL"]
        fileName = requestjson["payload"]["fileName"]
        filePath = DOWNLOAD_DIR + "/" + fileName

        # store file info for further requests (upload)
        FILES.append({"transId":transId, "fileName":fileName})

        # inform confluence about that the download started
        responsejson = {
            "eventName": "file-download-start",
            "type": "event",
            "payload": appId,
            "transactionID": transId
        }
        await send(websocket, json.dumps(responsejson))

        # start download
        urllib.request.urlretrieve(fileUrl, filePath)

        # inform confluence that the download finished
        responsejson = {
            "eventName": "file-downloaded",
            "type": "event",
            "payload": None,
            "transactionID": transId
        }
        await send(websocket, json.dumps(responsejson))

        # set up file watcher
        wm = pyinotify.WatchManager()
        wm.add_watch(DOWNLOAD_DIR, pyinotify.ALL_EVENTS)
        notifier = pyinotify.ThreadedNotifier(wm, FileChangedHandler(dict={"websocket":websocket, "appId":appId, "transId":transId, "filePath":filePath}))
        notifier.start()

        # start application
        subprocess.call(["xdg-open", filePath])

    elif(requestjson["type"] == "upload-file-in-app"):
        transId = requestjson["transactionID"]
        fileUrl = requestjson["payload"]["uploadUrl"]

        # get stored file name
        fileName = None
        for f in FILES:
            if(f["transId"] == transId):
                fileName = f["fileName"]
                break
        filePath = DOWNLOAD_DIR + "/" + fileName

        # inform confluence that upload started
        responsejson = {
            "eventName": "file-direct-upload-start",
            "type": "event",
            "payload": {
                "fileID": requestjson["payload"]["fileID"],
                "directUploadId": 2
            },
            "transactionID": transId
        }
        await send(websocket, json.dumps(responsejson))

        # now upload the modified file
        print("Now uploading " + fileName + " to: " + fileUrl)
        parsed_uri = urlparse(fileUrl)
        host = '{uri.netloc}'.format(uri=parsed_uri)
        origin = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        headers = {
            "Host": host,
            "origin": origin,
            "Accept": None,
            "Accept-Language": "de",
            "X-Atlassian-Token": "nocheck"
            #"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) AtlassianCompanion/0.6.2 Chrome/61.0.3163.100 Electron/2.1.0-unsupported.20180809 Safari/537.36"
        }
        with open(filePath, 'rb') as f:
            r = requests.post(
                fileUrl,
                files={
                    "comment": ("comment", "Uploaded by Companion for Linux (yay!)"),
                    "file": (fileName, f)
                },
                headers=headers
            )
            print(r)
            print(r.text)

        # inform confluence that upload finished
        responsejson = {
            "eventName": "file-direct-upload-progress",
            "type": "event",
            "payload": {
                "progress": { "percentage": 100 },
                "directUploadId": 2
            },
            "transactionID": transId
        }
        await send(websocket, json.dumps(responsejson))

        # inform confluence that upload finished
        responsejson = {
            "eventName": "file-direct-upload-end",
            "type": "event",
            "payload": {
                "fileID": requestjson["payload"]["fileID"],
                "directUploadId": 2
            },
            "transactionID": transId
        }
        await send(websocket, json.dumps(responsejson))

class FileChangedHandler(pyinotify.ProcessEvent):
    def my_init(self, dict):
        self._websocket = dict["websocket"]
        self._appId = dict["appId"]
        self._transId = dict["transId"]
        self._filePath = dict["filePath"]

    # IN_CLOSE to support FreeOffice
    # (FreeOffice does not modify the file but creates a temporary file,
    # then deletes the original and renames the temp file to the original file name.
    # That's why IN_MODIFY is not called when using FreeOffice.)
    def process_IN_CLOSE(self, event):
        self.process_IN_MODIFY(event=event)

    # IN_MODIFY to support LibreOffice
    # (LibreOffice modifies the file directly.)
    def process_IN_MODIFY(self, event):
        print("file changed: " + event.pathname + " (watching for: " + os.path.abspath(self._filePath) + ")")
        if(os.path.abspath(self._filePath) == event.pathname):
            # inform confluence about the changes
            responsejson = {
                "eventName": "file-change-detected",
                "type": "event",
                "payload": self._appId,
                "transactionID": self._transId
            }
            self._loop = asyncio.new_event_loop()
            task = self._loop.create_task(self._websocket.send(json.dumps(responsejson)))
            self._loop.run_until_complete(task)
            print("> " + json.dumps(responsejson))

async def companionHandler(websocket, path):
    while(True):
        request = await websocket.recv()
        print(f"< {request}")
        await handleJson( websocket, json.loads(request) )

async def send(websocket, response):
    await websocket.send(response)
    print(f"> {response}")

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('demo-cert/companion.crt', 'demo-cert/companion.key')

start_server = websockets.serve(
    companionHandler, "localhost", 22274, ssl=ssl_context
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
