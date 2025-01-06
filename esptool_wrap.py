import os
from shutil import rmtree
import zipfile
import json
import PySimpleGUI as sg
import serial.tools.list_ports
import subprocess


def LEDIndicator(key=None, radius=30):
    return sg.Graph(canvas_size=(radius, radius),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             pad=(0, 0), key=key)


def SetLED(window, key, color):
    graph = window[key]
    graph.erase()
    graph.draw_circle((0, 0), 12, fill_color=color, line_color=color)


def flash_go(path_to_zip_file, com_port):
    args = []
    if os.path.isdir("update"):
        rmtree("update")
    os.mkdir("update")
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall("update")
    with open('update/flasher_args.json', 'r') as file:
        data = json.load(file)
    args.append("esptool.exe")
    args.append("--chip " + str(data["extra_esptool_args"]["chip"]))
    args.append("-p " + com_port)
    args.append("-b 460800")
    args.append("--before=" + str(data["extra_esptool_args"]["before"]))
    args.append("--after=" + str(data["extra_esptool_args"]["after"]))
    args.append("write_flash")
    for arg in data["flash_settings"]:
        args.append("--" + arg + " " + str(data["flash_settings"][arg]))
    for arg in data["flash_files"]:
        args.append(arg + " " + "update/" + str(data["flash_files"][arg]))
    strs = ""
    for st in args:
        strs = strs + " " + st
    process_2 = subprocess.run(strs, shell=True, capture_output=True)
    rmtree("update")
    with open("log.txt", "w") as f:
        f.write(process_2.stdout.decode())
    return process_2.returncode


def main():
    choose_list = []
    # All the stuff inside your window.
    layout = [[sg.Text('Select the zip archive with the new firmware')],
              [sg.Text('File path:'), sg.Input(size=(25, 25)), sg.FileBrowse()],
              [sg.Text('Select your device from the port list'),
               sg.Combo(values=choose_list, key="coms", default_value=' ', size=(10, 10))],
              [sg.Button('Flash'), LEDIndicator('_runing_')]]

    # Create the Window
    window = sg.Window('Esptool Simple Smart Wraper', layout,finalize=True)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        ports = list(serial.tools.list_ports.comports())
        choose_list.clear()
        for p in ports:
            choose_list.append(str(p[0]))
        if not choose_list:
            choose_list.append(' ')
        window["coms"].update(value=choose_list[0], values=choose_list)
        event, values = window.read(timeout=1000)
        if event == sg.WIN_CLOSED:
            break
        if event == "Flash":
            window.disable()
            SetLED(window, '_runing_', 'yellow')
            window.refresh()
            if flash_go(values[0], values["coms"]) == 0:
                SetLED(window, '_runing_', 'green')
            else:
                SetLED(window, '_runing_', 'red')
            window.refresh()
            window.enable()

    window.close()


if __name__ == "__main__":
    main()
