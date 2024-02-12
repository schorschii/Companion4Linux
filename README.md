# Confluence Companion App for Linux

The Companion App for Linux is an unoffical port of the [Atlassian Companion App](https://confluence.atlassian.com/conf612/administering-the-atlassian-companion-app-958778510.html) (originally only available for Windows and MacOS) for usage on Linux clients. It is basically just a tiny python script (~400 lines).  

With the Companion App you can [edit files in Atlassian Confluence](https://confluence.atlassian.com/conf612/edit-files-958777653.html) with your preferred (local installed) desktop application. The companion app will automatically upload the file to Confluence if it changed on disk.  

When reporting bugs, please append a detailed description of the error including which Confluence version you are using and whether you are running your own Confluence server or if you are using the cloud version.

## Debian Package Installation (Debian/Ubuntu/Mint)
1. Download and install the `.deb` package from the [latest release](https://github.com/schorschii/companion-linux/releases) on Github.
2. After installation please log out and log in again. The script then starts automatically.
3. Open Confluence in your web browser, open a document and click on "Edit". The companion script will display a GUI dialog asking if you want to trust this site. Click "Yes". Now you can edit files.

## Manual Installation (Debian/Ubuntu/Mint)
1. Install required Python packages
```bash
apt install python3-pip python3-distutils python3-pyinotify python3-wxgtk4.0
pip3 install websockets
```

2. Set execution rights and copy `companion2.py` (for Confluence 7.4.0 and newer).
```bash
chmod +x companion2.py
cp companion2.py /usr/bin
cp companion-protocol-handler.desktop /usr/share/applications
update-desktop-database
```

3. Set execution rights, copy and start `companion.py` (for older Confluence versions).
```bash
chmod +x companion.py
cp companion.py /usr/bin
cp companion-autostart.desktop /etc/xdg/autostart
nohup /usr/bin/companion.py &
```

4. Open Confluence in your web browser, open a document and click on "Edit".  
In Confluence 7.4 and newer, the browser will ask you if you want to open the Companion app. In older versions, the companion script will display a GUI dialog asking if you want to trust this site. Click "Yes". Now you can edit files.

**Further hints:**
- Temporary files will be saved in `~/.cache/companion/tmp` and config files in `~/.config/companion`. Please ensure that you have write permissions in that directories.

---

## Functionality
There are 3 ways how the companion app works.

### 1. Local Web Server With SSL Certificate
Atlassian's first attempt was that the web browser connects via websocket to "atlassian-domain-for-localhost-connections-only.com" (which points to 127.0.0.1) where the companion app listens for requests.

SSL encryption between Browser and Companion App (through "atlassian-domain-for-localhost-connections-only.com") is not supported anymore as described [here](https://jira.atlassian.com/browse/CONFSERVER-59244?src=confmacro&_ga=2.138774577.300479270.1578747514-1264684236.1567087366).

This technology not supported anymore by Companion4Linux.

### 2. Local Web Server Without SSL
The web browser connects via websocket to 127.0.0.1. This technology was replaced with a new technology (case 3) in Atlassian Companion App v1.0.0 / Confluence 7.4.0 in order to support terminal server environments (see [here](https://confluence.atlassian.com/doc/atlassian-companion-app-release-notes-958455712.html)).

This method is handled by "companion.py".

### 3. Via Protocol Scheme »atlassian-companion:«
The companion app waits until called from browser with a command line argument like »atlassian-companion:{"link":"https://....}«.

This method os handled by "companion2.py".
