# Confluence Companion App for Linux

The Companion App for Linux is an unoffical Linux port of the [Atlassian Companion App](https://confluence.atlassian.com/doc/install-atlassian-companion-992678880.html) ([originally only available for Windows and macOS](https://confluence.atlassian.com/conf612/administering-the-atlassian-companion-app-958778510.html)). In contrast to the official fat Electron app, this is basically just a tiny python script (~400 lines).

**Please note that the Companion functionality is now only available for Confluence Data Center (as of February 2024). [Atlassian removed it from the Cloud version in 2022](https://community.atlassian.com/t5/Confluence-articles/Removing-the-Companion-app-from-Confluence-Cloud/ba-p/1884657).**

With the Companion App you can [edit files in Atlassian Confluence](https://confluence.atlassian.com/conf612/edit-files-958777653.html) with your preferred (local installed) desktop application. The companion app will automatically upload the file to Confluence if it changed on disk.

When reporting bugs, please append a detailed description of the error including which Confluence version you are using and whether you are running your own Confluence server or if you are using the cloud version.

## Debian Package Installation (Debian/Ubuntu/Mint)
1. Download and install the `.deb` package from the [latest release](https://github.com/schorschii/companion-linux/releases) on Github.
2. Open Confluence in your web browser, open a document and click on "Edit". Your browser will ask you now to allow executing Companion4Linux. A desktop notification will appear informing you about the current companion activity.

## Manual Installation (Debian/Ubuntu/Mint)
```bash
# install required Python packages
apt install python3-distutils python3-pyinotify

# set execution rights and copy `companion2.py` (for Confluence 7.4.0 and newer)
chmod +x companion2.py
cp companion2.py /usr/bin
cp companion-protocol-handler.desktop /usr/share/applications
update-desktop-database
```

Open Confluence in your web browser, open a document and click on "Edit". Your browser will ask you now to allow executing Companion4Linux. A desktop notification will appear informing you about the current companion activity.

**Further hints:**
- File monitoring will be cancelled as soon as the desktop notification is closed. Make sure that the notification is visible until you finished editing your document.
- Temporary files will be saved in `~/.cache/companion/tmp` and config files in `~/.config/companion`. Please ensure that you have write permissions in that directories.
- When executing `firefox` in the terminal, you can see the Companion4Linux output. Check this output for troubleshooting and before reporting bugs.

---

## Functionality
There are 3 ways how the companion app works.

### 1. Local Web Server With SSL Certificate
Atlassian's first attempt was that the web browser connects via websocket to "atlassian-domain-for-localhost-connections-only.com" (which points to 127.0.0.1) where the companion app listens for requests.

SSL encryption between Browser and Companion App (through "atlassian-domain-for-localhost-connections-only.com") is not supported anymore as described [here](https://jira.atlassian.com/browse/CONFSERVER-59244?src=confmacro&_ga=2.138774577.300479270.1578747514-1264684236.1567087366).

This technology is not supported anymore by Companion4Linux.

### 2. Local Web Server Without SSL
The web browser connects via websocket to 127.0.0.1 where the companion app listens for requests. This was replaced with a new technology (case 3) in Atlassian Companion App v1.0.0 / Confluence 7.4.0 in order to support terminal server environments (see [here](https://confluence.atlassian.com/doc/atlassian-companion-app-release-notes-958455712.html)).

This method was still used lately in Confluence Cloud but support was [dropped 2022](https://community.atlassian.com/t5/Confluence-articles/Removing-the-Companion-app-from-Confluence-Cloud/ba-p/1884657), therefore it was also removed from Companion4Linux. Before that, method 1 and 2 were handled by "companion.py".

### 3. Via Protocol Scheme »atlassian-companion:«
The companion app gets called from a browser using a protocol scheme `atlassian-companion:` with a parameter like `{"link":"https://....}`. The user needs to allow this execution (once per domain) in his browser. The browser will then start the application which is registered for this protocol with a command line parameter `atlassian-companion:{"link":"https://....}`. With this information, it can download, monitor and upload the requested file.

This method is handled by "companion2.py".
