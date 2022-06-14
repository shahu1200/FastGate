# **i-TEK FastGate**
## **Installation**
----
As of now, production code will zipped as **project_name.tar.gz** and transfered to the gateways using remote connection.
After that below process is to be done:
1. copy **project_name.tar.gz** file in **/home/iTEK**
2. extract project
    - tar -xvzf **project_name.tar.gz**
3. cd **project_name**
5. follow below process for individual installation
> NOTE :- Do not change the directory until said to do so.

### **Raspberry Pi**
----

Raspi-conf
- In **Interface**
    - Enable **I2C**
    - Enable **Serial Port**
- In **Localisation**
    - Set **Timezone**
    - Set **WLAN Country** to **INDIA**
> **NOTE** :- if asked to reboot skip it.

Modify boot cmdline
- sudo nano /boot/cmdline.txt
```
console=tty3 root=PARTUUID=402b7f43-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait logo.nologo
```

Modify boot config
- sudo nano /boot/config.txt
> Modify/Add below options
- enable_uart=1
- dtoverlay=pi3-miniuart-bt
- core_freq=250
- disable_splash=1

Disable NTP server
> **NOTE** :- If using RTC module
- Stop all NTP services
    - sudo systemctl stop systemd-timesyncd
    - sudo systemctl disable systemd-timesyncd
    - sudo timedatectl set-ntp false
- To check NTP service status
    - sudo timedatectl status

### **Application**
---
Python packages
- pip3 install -r requirements.txt

Utilities - These are helper scripts which can be installed. They are present in **scripts** folder.
- pip3 install --upgrade scripts/<file_name>.whl

Run application manually
- sudo ./app/cli_app

Run application on boot
- sudo bash install.sh
- sudo reboot

## **Monitoring**
---
These steps are valid only after installtion has been done.

### **RTC Module**
To check if RTC module is detected or not
- sudo i2cdetect -y 1
    - If you get following error then it means you have not enabled I2C in **raspi-conf**
        ```
        Error: Could not open file `/dev/i2c-1' or `/dev/i2c/1': No such file or directory
        ```
    - Under ROW=60 and COL=8
        - If value is **'--'** then RTC module not detected
        - If value is **'68'** then RTC module detected

### **Manual Run**
To run application manually use below command.
- sudo systemctl stop itek_cfs.service
- sudo ./app/cli_app
> **NOTE** :- To run application on startup just reboot the system.

### **Logs**
To view realtime logs
- tail -f logs/app.log

### **Transactions**

To extract transaction from the database
- itekcsv -e database/itekCFS.sqlite3

> **NOTE** :- This tools dumps all database TABLES into corresponding tab-formatted csv file.

> **WARNING** :- You cannot modify **database or tables or records** using this tool.

To delete transactions
- copy database file to different location
- stop application
- delete original database file
- restart application
