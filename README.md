# Confluence Companion App for Linux

This Python script emulates the functionality of the [Atlassian Companion App](https://confluence.atlassian.com/conf612/administering-the-atlassian-companion-app-958778510.html) (Windows/Mac) for usage on Linux clients.  

With the Companion App you can [edit files in Atlassian Confluence](https://confluence.atlassian.com/conf612/edit-files-958777653.html) with your preferred (local installed) desktop application.  

This script is currently in beta. Contributions welcome. Please also tell me if the script just works fine with your confluence installation and linux distribution.

## Debian Package Installation (Debian/Ubuntu/Mint)
1. Download and install the `.deb` package from the latest release on Github.
2. After installation please log out and log in again. The script then starts automatically.
3. Open Confluence in your web browser, open a document and click on "Edit". The companion script will display a GUI dialog asking if you want to trust this site. Click "Yes". Now you can edit files.

## Manual Installation (Debian/Ubuntu/Mint)
1. Install required Python packages
```bash
apt install python3-pip python3-distutils python3-pyinotify python3-wxgtk4.0
pip3 install websockets
```

2. Set execution rights and start the script.
```bash
chmod +x companion.py
./companion.py
```

3. Open Confluence in your web browser, open a document and click on "Edit". The companion script will display a GUI dialog asking if you want to trust this site. Click "Yes". Now you can edit files.

Further hints:
- Temporary files will be saved in `~/.cache/companion/tmp` and config files in `~/.config/companion`. Please ensure that you have write permissions in that directories.
- You can put `companion.py` in your personal autostart.
- You can copy `companion.desktop` into `/etc/xdg/autostart` to install it in autostart for all users. Please do not forget to adjust the script path in the `companion.desktop` file.

---

## Installation Details
### Generating an own Certificate
**Update:** SSL encryption between Browser and Companion App (through atlassian-domain-for-localhost-connections-only.com) is not supported anymore as described [here](https://jira.atlassian.com/browse/CONFSERVER-59244?src=confmacro&_ga=2.138774577.300479270.1578747514-1264684236.1567087366). Confluence now uses a direct WebSocket connection to 127.0.0.1 (no domain name) without transport encryption.
