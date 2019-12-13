# Confluence Companion App for Linux

This Python script emulates the functionality of the [Atlassian Companion App](https://confluence.atlassian.com/conf612/administering-the-atlassian-companion-app-958778510.html) (Windows/Mac) for usage on Linux clients.  

With the Companion App you can [edit files in Atlassian Confluence](https://confluence.atlassian.com/conf612/edit-files-958777653.html) with your preferred (local installed) desktop application.  

This script is currently EXPERIMENTAL and therefore not intended for productive usage! Contributions welcome.

## Installation (Ubuntu/Mint)
1. Install required Python packages
```bash
apt install python3-pip python3-distutils
pip3 install websockets
```

2. The Companion App requires a valid certificate for the domain "atlassian-domain-for-localhost-connections-only.com" in order to communicate with the browser. You can generate your own certificate using `openssl` (recommended, [see below](#generating-an-own-certificate)) or use the provided demo certificate and key files.

  The demo certificate is self signed. Thats why you have to import the associated root CA in your browser or (system-wide) in your operating system. Please refer to the [instructions below](#importing-the-ca-certificate) how to import the CA certificate.  

3. Edit `companion.py` and change `ALLOWED_SITE = "Confluence"` to your site name. If the defined name does not match the confluence server name, all requests are rejected. If rejected, the script prints out the site name, so you can adjust it.

4. Change the working directory (important, otherwise `companion.py` won't find the cert and key file) and start the script. Ensure that you have write permissions in the `temp` directory.
```bash
cd companion
chmod +x companion.py
./companion.py
```

Hint: you can replace the cert paths in the script with absolute paths and put `start.sh` in your autostart.

---

## Installation Details
### Generating an own Certificate
You can generate your own CA and Companion certificate so you don't have to trust the demo CA.
```bash
# generate CA private key
openssl genrsa -aes256 -out ca-key.pem 2048

# generate CA certificate
openssl req -x509 -new -nodes -extensions v3_ca -key ca-key.pem -days 1024 -out ca-root.pem -sha512

# create openssl config file, content see below
nano req.conf

# create companion private key
openssl genrsa -out companion.key 4096

# create companion certificate signing request
openssl req -new -key companion.key -out companion.csr -sha512 -config req.conf

# sign request = create companion certificate
openssl x509 -req -in companion.csr -CA ca-root.pem -CAkey ca-key.pem -CAcreateserial -out companion.crt -days 1024 -sha512 -extensions req_cert_extensions -extfile req.conf
```
req.conf:
```
[ req ]
req_extensions     = req_cert_extensions
distinguished_name = req_distinguished_name
prompt = no

[req_distinguished_name]
C = DE
ST = MyLocation
L = MyCity
O = MyCompany
OU = MyDepartment
CN = atlassian-domain-for-localhost-connections-only.com

[req_cert_extensions]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName=@subject_alt_name

[ subject_alt_name ]
DNS.1=atlassian-domain-for-localhost-connections-only.com
```

### Importing the CA Certificate
#### Chrome
Go to "Settings" -> "Certificates" -> "Authorities" -> "Import" and choose the "myCA.pem" file.

#### Firefox
Go to "Preferences" -> "Privacy & Security" -> "View Certificates" -> "Authorities" -> "Import" and choose the "myCA.pem" file.

#### Debian
System-wide for all browsers:
```
sudo cp ca-root.pem /usr/share/ca-certificates/myca-root.crt
sudo dpkg-reconfigure ca-certificates
```
