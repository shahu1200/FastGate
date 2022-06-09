#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.main import main

if __name__ == '__main__':    
    main()


"""
conversion python code into exe file

pyinstaller --console --paths "app" 
                      --paths "app/data_conversion" 
                      --paths "app/gpio" 
                      --paths "app/rfid" 
                      --paths "app/mqtt"
                      --paths "app/web"
                      --paths "app/templates" 
                      "cli_app.py"
                      --collect-data="app.templates"


this below command worked for this project
pyinstaller --console --paths "app" --paths "app/data_conversion" --paths "app/gpio" --paths "app/rfid" --paths "app/mqtt" --paths "app/web" --paths "app/templates" "cli_app.py" --collect-data="app.templates" --collect-data "app.static" --collect-data "logs" --collect-data "database" --add-data "config.toml:."




pyinstaller --console --paths "app" --paths "app/data_conversion" --paths "app/gpio" --paths "app/rfid" --paths "app/mqtt" --paths "app/web" --paths "app/templates" "cli_app.py" --collect-data="app.templates"

pyinstaller --console --paths "app" --paths "app/data_conversion" --paths "app/gpio" --paths "app/rfid" --paths "app/mqtt" --paths "app/web" --paths "app/templates" "cli_app.py" --collect-data="app.templates" --collect-data="logs"
"""