# AsteriskProvisioning
Python script to generate Asterisk 1.8 configuration files for Tauk phone system using config file templates in templates directory and build properties configuration file. Goal was to use only Python only libraries to avoid installing an external dependencies.

- sip.conf
- extensions.conf
- voicemail.conf
- Polycom phones
- Polycom Directory


```bash
./GenTaukConf.py -h
usage: GenTaukConf.py [-h] [--device DEVICE] [--password] properties extensions

Tool to generate Tauk Asterisk and Polycom phone configurations. Outputs files to gen directory
specified in property file

positional arguments:
  properties            Property file name containing application configuration and templates
  extensions            Extension File CSV Format: First Last Name, Email, Extension, MAC Address
                        Example: John Smith,js@specailai.com,8186,0004F214B68B

options:
  -h, --help            show this help message and exit
  --device DEVICE, -d DEVICE
                        Device name either 'extension' or 'mac', defaults to extension
  --password, -p        Generate device passwords.
```


