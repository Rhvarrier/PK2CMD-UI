import configparser
import subprocess

config_file_path = "config.properties"

class PK2CMD:

    version_cmd = "-?V"
    find_pic_cmd = "-P"

    def __init__(self, config_file_path):
        config = configparser.ConfigParser()
        if config.read(config_file_path):
            self.default_hex_file_path = config['DEFAULT']['default_hex_file_path']
            self.pk2cmd_command = config['DEFAULT']['pk2cmd_command']
        else:
            raise ValueError('No config file found!')

    @staticmethod
    def run_cmd(command):
        cp = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines= True)
        out, error = cp.stdout, cp.stderr
        return [out, error]

    @property
    def version(self):
        version, error = PK2CMD.run_cmd(self.pk2cmd_command + " " + PK2CMD.version_cmd)
        if not error:
            return version.split('\n')[1].split(':')[1].strip()
        return False
    
    @property
    def is_connected(self):
        version, error = PK2CMD.run_cmd(self.pk2cmd_command + " " + PK2CMD.version_cmd)
        if not error:
            version = version.split('\n')[3].split(':')[1].strip()
            if "PICkit 2 not found" in version:
                return False
            return True
        return False
    
    @property
    def device_id(self):
        out, error = PK2CMD.run_cmd(self.pk2cmd_command + " " + PK2CMD.find_pic_cmd)
        if not error:
            out = out.partition('\n')[0]
            if "Auto-Detect: Found part " in out:
                return out[out.find("PIC"):-1]
            elif "No PICkit 2 found." in out:
                return None
            else:
                return None
        return None
    
    def upload(self, hex_filepath, device_id):
        cmd = self.pk2cmd_command + " -P" + device_id + " -M -F" + hex_filepath
        out,error = PK2CMD.run_cmd(cmd)
        if not error and "Operation Succeeded" in out:
            return True
        return False

import pyudev
import threading

class USBDetector():
    ''' Monitor udev for detection of usb '''
 
    def __init__(self, obj):
        ''' Initiate the object '''
        self.thread = threading.Thread(target=self._work)
        self.thread.setDaemon(True)
        self.thread.start()
        self.obj = obj
 
    def _work(self):
        ''' Runs the actual loop to detect the events '''
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='usb')
        # this is module level logger, can be ignored
        self.monitor.start()
        for device in iter(self.monitor.poll, None):
            if device.action == 'add':
                # some function to run on insertion of usb
                self.on_created()
            else:
                # some function to run on removal of usb
                self.on_deleted()   
    
    def on_created(self):
        self.obj.connection_event()
        

    def on_deleted(self):
        self.obj.connection_event()

import tkinter as tk
from tkinter import filedialog
import tk_tools
import sys, os

class UI(tk.Frame):
    config_file_path = "config.properties"
    padx = 5
    pady = 5

    def __init__(self, parent):
        self.parent = parent
        self.parent.protocol("WM_DELETE_WINDOW", self.close_window)
        self.parent.title("PK2CMD Pickit2 UI")
        self.parent.geometry('600x250')
        self.parent.resizable(False, False)
        self.pk2cmd = PK2CMD(config_file_path)

        buttons = tk.Frame(parent)
        self.find_pic_btn = tk.Button(buttons, text = "Find PIC", command = self.find_pic, state = tk.DISABLED)
        self.find_file_btn = tk.Button(buttons, text = "Select HEX File", command = self.find_file, state = tk.DISABLED)
        self.upload_btn = tk.Button(buttons, text = "Upload", command = self.upload, state = tk.DISABLED)
        self.find_pic_btn.pack(side=tk.TOP)
        self.find_file_btn.pack(side=tk.TOP)
        self.upload_btn.pack(side=tk.TOP)

        labels = tk.Frame(parent)
        pic_label = tk.Label(labels, text = "Device id: ")
        hex_file_label = tk.Label(labels, text = "HEX File: ")
        pic_label.pack(side=tk.TOP)
        hex_file_label.pack(side=tk.TOP)

        self.hex_file_path = ""

        info = tk.Frame(parent)
        self.device_id = tk.Label(info, text = "-")
        self.hex_file = tk.Label(info, text = "-")
        self.device_id.pack(side=tk.TOP)
        self.hex_file.pack(side=tk.TOP)

        status_frame = tk.Frame(parent)
        self.status = tk.Label(status_frame, text = "")
        self.led = tk_tools.Led(status_frame, size=10)
        self.status.pack(side=tk.LEFT)
        self.led.pack(side=tk.RIGHT)

        buttons.pack(side=tk.TOP)
        labels.pack(side=tk.LEFT)
        info.pack(side=tk.RIGHT)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.usb_detector = USBDetector(self)
        if self.pk2cmd.is_connected:
            self.led.to_green(True)
            self.status['text'] = "Ready to detect device"
        else:
            self.led.to_red(True)
            self.status['text'] = "Connect PICKIT2"

        self.parent.mainloop()
    
    def set_status(self, text, fg):
        self.status['text'] = text
        self.status['fg'] = fg

    def find_pic(self):
        if self.pk2cmd.is_connected:
            self.set_status("Finding PIC id...", "black")
            device_id = self.pk2cmd.device_id
            if device_id != None:
                self.device_id['text'] = device_id
                self.set_status("Done.", "green")
                self.find_file_btn['state'] = tk.NORMAL
            else:
                self.device_id['text'] = "-"
                self.set_status("No PIC detected", "red")
                self.find_file_btn['state'] = tk.DISABLED

    def upload(self):
        self.set_status("Uploading....", "black")
        self.led.to_yellow(True)
        sucess  = self.pk2cmd.upload(self.hex_file_path, self.device_id.cget('text'))
        if sucess:
            self.set_status("Uploading to " + self.device_id.cget('text') + ": Done", "green")
        else : 
            self.set_status("Uploading to " + self.device_id.cget('text') + ": Error occured", "red")
        self.led.to_green(True)

    def set_file(self, file_path):
        self.hex_file_path = file_path
        self.hex_file['text'] = os.path.basename(file_path)
    
    def find_file(self):
        file = tk.filedialog.askopenfilename(initialdir =  self.pk2cmd.default_hex_file_path, title = "Select A HEX File", filetypes=[("Hex files","*.hex")], multiple = False)
        if len(file) != 0:
            self.set_file(file)
            self.upload_btn['state']=tk.NORMAL
        else:
            self.hex_file['text']="-"
            self.set_status("Could not select file", "red")
            self.upload_btn['state']=tk.DISABLED
        

    def connection_event(self):
        pickit_connected = self.pk2cmd.is_connected
        if(pickit_connected):
            self.led.to_green(True)
            self.find_pic_btn['state'] = tk.NORMAL
            self.set_status("Ready to detect device", "black")
        else:
            self.led.to_red(True)
            self.find_pic_btn['state'] = tk.DISABLED
            self.set_status("Connect PICKIT2", "black")
        
    def close_window(self):
        sys.exit()

root = tk.Tk()
ui = UI(root)
