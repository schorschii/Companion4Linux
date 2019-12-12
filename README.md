# Confluence Companion App for Linux

This Python script emulates the functionality of the Atlassian Companion App (Windows/Mac) for usage on Linux clients.  

This script is currently EXPERIMENTAL and therefore not intended for productive usage! Contributions welcome!

## Installation (Ubuntu)
1. Install required Python packages
```
apt install python3-pip python3-distutils
pip3 install websockets
```

2. The Companion App requires a valid certificate for the domain "atlassian-domain-for-localhost-connections-only.com" in order to communicate with the browser. You can generate your own certificate using `openssl` (recommended) or use the provided demo certificate and key files.  

  The demo certificate is self signed. Thats why you have to import the associated root CA in your browser or (system-wide) in your operating system.  
  In Chrome, go to "Settings" -> "Certificates" -> "Authorities" -> "Import" and choose the "myCA.pem" file.

3. Edit `companion.py` and change `ALLOWED_SITE = "Confluence"` to your site name. If the defined name does not match the confluence server name, all requests are rejected. If rejected, the script prints out the site name, so you can adjust it.

4. Change the working directory (important, otherwise `companion.py` won't find the cert and key file) and start the script. Ensure that you have write permissions in the `temp` directory.
```
cd companion
chmod +x companion.py
./companion.py
```

Hint: you can replace the cert paths in the script with absolute paths and put `start.sh` in your autostart.
