#!/bin/bash
cat > /etc/systemd/system/itek_cfs.service << EOF
[Unit]
Description=iTek CFS application
After=network.target

[Service]
ExecStart=${PWD}/app/cli_app
WorkingDirectory=${PWD}/

#StandardOutput=inherit
StandardError=inherit
Restart=always
User=${USER}
RestartSec=10s
SyslogIdentifier=itek_cfs

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable itek_cfs.service
