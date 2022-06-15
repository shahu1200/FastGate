#!/bin/bash

## Modify these parameters only
PROJECT_NAME="FastGate"
APP_VERSION="1.0.0"

#############################################################
## Update version file
VERSION_FILE="app/version.py"
APP_BUILD=$(date '+%d/%m/%Y %H:%M:%S');

cat > $VERSION_FILE << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Application Version

    NOTE: THIS FILE IS CREATED THROUGH BASH
"""

APP_VERSION = "${APP_VERSION}"
APP_BUILD = "${APP_BUILD}"
EOF

#############################################################
# BACKGROUND COLOR
BGBLACK='\033[40m'
BGRED='\033[41m'
BGGREEN='\033[42m'
BGYELLOW='\033[43m'
BGBLUE='\033[44m'
BGPURPLE='\033[45m'
BGCYAN='\033[46m'
BGWHITE='\033[47m'

#############################################################
# FOREGROUND COLOR
FGBLACK='\033[0;90m'
FGRED='\033[0;91m'
FGGREEN='\033[0;92m'
FGYELLOW='\033[0;93m'
FGBLUE='\033[0;94m'
FGPURPLE='\033[0;95m'
FGCYAN='\033[0;96m'
FGWHITE='\033[0;97m'

NOCOLOR='\033[0m'



# #############################################################
# ## Check if README.pdf is present or not
# if [ ! -f "README.pdf" ]; then
#     ## Right now .md to .pdf is converted using vscode and its extension
#     echo -e "${FGRED}ERROR: README.pdf Not found.${NOCOLOR}"
#     echo -e "${FGRED}Need to convert README.md to README.pdf${NOCOLOR}"
#     exit $?
# fi

# #############################################################
# ## Check if ReleaseNote.pdf is present or not
# #if [ ! -f "ReleaseNote.pdf" ]; then
# #    ## Right now .md to .pdf is converted using vscode and its extension
# #    echo -e "${FGRED}ERROR: ReleaseNote.pdf Not found.${NOCOLOR}"
# #    echo -e "${FGRED}Need to convert ReleaseNote.md to ReleaseNote.pdf${NOCOLOR}"
# #    exit $?
# #fi

# #############################################################
# ## Use Pyinstaller to create .exe
# OUTPUT_NAME="${PROJECT_NAME}_${APP_VERSION}"

# echo -e "Creating application ${FGYELLOW}$OUTPUT_NAME, Build: $APP_BUILD${NOCOLOR} ..."
# pyinstaller --noconfirm --onedir --console \
#     --paths "app" \
#     --paths "app/api" \
#     --paths "app/rfid" \
#     --paths "app/gpio" \
#     "cli_app.py"
# if [ $? -ne 0 ]; then
#     echo -e "${FGRED}PYINSTALLER, exit status: $?${NOCOLOR}"
#     exit $?
# fi

# #############################################################
# ## Do additional setup
# echo -e "${FGBLUE}Creating additional files & folders...${NOCOLOR}"
# mkdir -p "dist/$OUTPUT_NAME/app"
# mkdir -p "dist/$OUTPUT_NAME/database"
# mkdir -p "dist/$OUTPUT_NAME/logs"
# mkdir -p "dist/$OUTPUT_NAME/scripts"

# cp -f "config.toml" "dist/$OUTPUT_NAME/"
# cp -f "install.sh" "dist/$OUTPUT_NAME/"
# cp -f "app/requirements.txt" "dist/$OUTPUT_NAME/"
# cp -rf "dist/cli_app/." "dist/$OUTPUT_NAME/app/"
# cp -rf scripts/itekCSV/dist/itekcsv-*.whl "dist/$OUTPUT_NAME/scripts/"
# cp -f "README.pdf" "dist/$OUTPUT_NAME/"
# cp -f "ReleaseNote.pdf" "dist/$OUTPUT_NAME/"

# #############################################################
# ## Compress all files
# echo -e "${FGBLUE}Compressing application...${NOCOLOR}"
# cd "dist/"
# tar -cvzf "$OUTPUT_NAME.tar.gz" "$OUTPUT_NAME/"
# cd ..

# #############################################################
# ## Do some cleanup
# echo -e "${FGBLUE}Performing cleanup...${NOCOLOR}"
# rm -rf "dist/cli_app/"
# rm -rf "dist/$OUTPUT_NAME/"
# rm -rf "build/"
# rm -rf "__pycache__/"
# rm -f "cli_app.spec"
# rm -f "README.pdf"
# #rm -f "ReleaseNote.pdf"

# echo -e "${FGGREEN}!!! Application package created !!!"
