# PK2CMD-UI
PK2CMD is a commandline utility for Linux to upload programs to Microchip PIC using Pickit 2. This tool only provides a GUI to interact with this utility. In order to use this tool PK2CMD must be installed. The installation path should be added to *pk2cmd_command* option of the *config.properties* file. By default the script will look for the associated commands in the `PATH` variable. 
You can also specify the default path to HEX files using *default_hex_file_path* option in the config file. By default its value is set to `/`. 

![Screenshot](/images/description_screenshot.png)

# Features
- Simple UI written using Tkinter
- Automatically detets when the Pickit2 is connected via USB port.

# Dependecy
- Tkinter
- tk_tools
- pyudev

# Usage
**Connect Pickit2 only after starting the UI Tool**. If not Pickit2 will not be detected automatically.

