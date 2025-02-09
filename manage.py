import tkinter as tk
from tkinter import ttk
import platform
import subprocess
import re
import threading
import os
import socket
import webbrowser
import queue
import sys

def toggleEntry(e, state):
    e.config(state=state)

def get_local_ip():
    #Get the local IP so we can tell the user where to navigate to
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.connect(("8.8.8.8", 80)) #Try using google's public DNS
        return my_socket.getsockname()[0]

class GUI:
    def __init__(self):
        self.ip_address = get_local_ip()
        self.root = None
        self.isStarted = False
        self.entry_camAddress = None
        self.entry_botToken = None
        self.var_localCamOption = None
        self.var_camAddress = None
        self.var_botToken = None
        self.button_start = None
        self.button_stop = None
        self.docker_process_handle = None
        self.text_slog = None
        self.enableLogging = threading.Event()

    def draw(self):
        pass

    def load(self):
        pass

    def dump(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class WindowsGUI(GUI):
    def __init__(self):
        super().__init__()
        self.os = "Windows"
        
    def createWindowAndSetDefaults(self):
        self.root = tk.Tk()
        self.root.title("Byakugan Launcher")
        self.root.geometry("800x600")
        self.ffmpeg_process_handle = None

        self.var_localCamOption = tk.IntVar(value=2)
        self.var_camAddress = tk.StringVar(value="")
        self.var_botToken = tk.StringVar(value="")

        #This is a thread safe queue, as I've been using through this whole project
        self.message_queue = queue.Queue(maxsize=200)

    def draw(self):

        #This unsightly blob renders the app GUI
        
        app_label = ttk.Label(self.root, text="Byakugan", font=("Helvetica", 18, "bold"))
        app_label.grid(row=0, column=0, columnspan=2)

        os_label = ttk.Label(self.root, text=f"Operating System: {self.os}", font=("Times New Roman", 12))
        os_label.grid(row=1, column=0, sticky="w", pady=20)

        camera_options_label = ttk.Label(self.root, text="Camera Options", font=("Times New Roman", 16, "bold"))
        camera_options_label.grid(row=3, column=0, columnspan=2, sticky="w")

        windows_warning_label = ttk.Label(self.root, text="Byakugan uses Docker. Docker on Windows does not allow direct access to USB webcam hardware, so if you want to use a locally attached camera, a RTMP streaming server will have to be created and a ffmpeg stream fed into the container. The quality of the feed from this is highly dependent on your network speed and processing power of your computer.", wraplength=750, font=("Times New Roman", 12))
        windows_warning_label.grid(row=4, column=0, columnspan=2, pady=5)

        webcam_frame = ttk.Frame(self.root)
        webcam_frame.grid(row=5, column=0, sticky="w", pady=10)

        windows_webcam_setting = ttk.Radiobutton(webcam_frame, text="Use locally attached camera", variable=self.var_localCamOption, value=1, command=lambda: toggleEntry(entry_camAddress, "disabled"))
        windows_webcam_setting.grid(row=0, column=0, padx=100)

        windows_webcam_setting = ttk.Radiobutton(webcam_frame, text="Use external network video feed",  variable=self.var_localCamOption, value=2, command=lambda: toggleEntry(entry_camAddress, "enabled"))
        windows_webcam_setting.grid(row=0, column=1, padx=100)

        addr_frame = ttk.Frame(self.root)
        addr_frame.grid(row=6, column=0, columnspan=2)

        label_camAddress = ttk.Label(addr_frame, text="Camera RTMP Server Address: ")
        label_camAddress.grid(row=0, column=0)

        entry_camAddress = ttk.Entry(addr_frame, textvariable=self.var_camAddress)
        entry_camAddress.grid(row=0, column = 1)

        bt_frame = ttk.Frame(self.root)
        bt_frame.grid(row=7, column=0, columnspan=2, pady=(30, 30))

        label_botToken = ttk.Label(bt_frame, text="Telegram Bot Token: ")
        label_botToken.grid(row=0, column=0)

        self.entry_botToken = ttk.Entry(bt_frame, textvariable=self.var_botToken)
        self.entry_botToken.grid(row=0, column = 1)

        self.text_slog = tk.Text(self.root, height=7, width=50, wrap="word", state="disabled")
        self.text_slog.grid(row=8, column=0, sticky="nsew", padx=(10, 0))

        scrollbar = ttk.Scrollbar(self.root, command=self.text_slog.yview)
        scrollbar.grid(row=8, column=1, sticky="ns")
        self.text_slog.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(30, 0))
        self.button_start = ttk.Button(button_frame, text="Start", command=self.start)
        self.button_start.grid(row=0, column=0)
        self.button_stop = ttk.Button(button_frame, text="Stop", command=self.stop)
        self.button_stop.grid(row=0, column=1)

        threading.Thread(target=self.messageLoop, daemon=True).start()

    def loop(self):
        self.root.mainloop()

    def start(self):
        if self.isStarted:
            return
        
        self.enableLogging.set()

        self.__startDocker()
            
        self.isStarted = True
        toggleEntry(self.button_stop, "enabled")
        toggleEntry(self.button_start, "disabled")

    def disableButtons(self):
        toggleEntry(self.button_stop, "disabled")
        toggleEntry(self.button_start, "disabled")

    def enableButtons(self):
        toggleEntry(self.button_stop, "enabled")
        toggleEntry(self.button_start, "enabled")

    def stop(self):

        if not self.isStarted:
            return
        
        self.__stopFFMPEG()
        self.__endDocker()
        self.isStarted = False
        toggleEntry(self.button_stop, "disabled")
        toggleEntry(self.button_start, "enabled")

    def displayMessage(self, text):
        try:
            self.message_queue.put_nowait(text)
        except queue.Full:
            pass      

    def __printMessage(self, text):
        self.text_slog.config(state="normal")
        self.text_slog.insert(tk.END, text + "\n")
        self.text_slog.config(state="disabled")
        self.text_slog.see(tk.END)

    def messageLoop(self):

        while True:
            try:
                msg = self.message_queue.get(block=False)
                self.root.after(0, self.__printMessage, msg)  # Safe UI update
            except queue.Empty:
                pass

    def __startFFMPEG(self):
        camera_name_query = subprocess.run(["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        #Use a regex to extract a camera name
        match = re.search(r'"(.*?)"', camera_name_query.stdout)
        if match:
            camera_name = match.group(1)
            self.displayMessage(f"Using camera: {camera_name}")
        else:
            self.displayMessage("No camera found! Please close and reopen the app and try again.")
            camera_name = None
            return False

        self.ffmpeg_process_handle = subprocess.Popen(["ffmpeg", "-f", "dshow", "-i", f'video={camera_name}', "-vcodec", "libx264", "-preset", "veryfast", "-video_size", "800x600", "-b:v", "1M", "-nostats", "-loglevel", "error", "-maxrate", "3000k", "-rtbufsize", "1G", "-bufsize", "3000k", "-an", "-f", "flv", "rtmp://127.0.0.1:1935/stream/test"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        threading.Thread(target=self.__ffpmeg_log, daemon=True).start()
        return True
    
    def __ffpmeg_log(self):

        while True:

            if not self.enableLogging.is_set():
                break

            try:
                while self.ffmpeg_process_handle and self.ffmpeg_process_handle.poll() is None:
                    line = self.ffmpeg_process_handle.stderr.readline().decode("utf8", errors="ignore")
                    if line:
                        self.root.after(0, self.displayMessage, line.strip())  # Safe UI update
                        pass
            except Exception as e:
                self.root.after(0, self.displayMessage, f"FFmpeg log error: {e}")

    def __stopFFMPEG(self):
        if self.ffmpeg_process_handle:
            self.displayMessage("Stopping FFmpeg stream...")
            self.ffmpeg_process_handle.kill()
            self.ffmpeg_process_handle = None

    def __startDocker(self):
        os.environ["DOCKER_HOST_IP"] = self.ip_address
        os.environ["BYAKUGAN_BOT_TOKEN"] = self.var_botToken.get()

        if self.var_localCamOption.get() == 1:
            self.docker_process_handle = subprocess.Popen(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.override.yml", "up", "-d"], env={**os.environ}, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
        else:
            self.docker_process_handle = subprocess.Popen(["docker", "compose", "-f", "docker-compose.yml", "up", "-d"], env={**os.environ,"CAMERA_FEED_SOURCE" : self.var_camAddress.get()}, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)

        threading.Thread(target=self.__docker_log, daemon=True).start()

    def __docker_log(self):

        while True:

            if not self.enableLogging.is_set():
                break

            try:
                while self.docker_process_handle and self.docker_process_handle.poll() is None:
                    line = self.docker_process_handle.stdout.readline()

                    if line:
                        self.root.after(0, self.displayMessage, line.strip()) 

                        if "Container byakugan" in line and "Starting" in line:
                            if self.var_localCamOption.get() == 1:
                                self.displayMessage("Starting the FFMPEG dummy camera")
                                if not self.__startFFMPEG():
                                    self.displayMessage("There was an error starting FFMPEG so the application terminated")
                                    return
                            else:
                                self.displayMessage("Fetching input from specified RTMP server")
                            webbrowser.open("http://"+self.ip_address+":5000")
                    
            except Exception as e:
                self.root.after(0, self.displayMessage, f"Docker log error: {e}")

    def __endDocker(self):

        self.displayMessage("Ending docker...this may take a while")
        self.root.after(0, self.disableButtons)

        #I realize that this is hardly done in Python
        #although people do this in JS all the time
        #This stops the app from freezing up when you close docker
        def edfunc():
            try:
                subprocess.run(["docker", "compose", "down"], check=True)
                self.docker_process_handle = None
                self.displayMessage("Docker has been shut down")
                self.enableLogging.clear()
                self.root.after(0, self.enableButtons)
            except Exception as e:
                self.displayMessage(str(e))
        
        threading.Thread(target=edfunc, daemon=True).start()



class LinuxGUI(GUI):
    def __init__(self):
        super().__init__()
        self.os = "Linux"
        
    def createWindowAndSetDefaults(self):
        self.root = tk.Tk()
        self.root.title("Byakugan Launcher")
        self.root.geometry("800x600")
        self.ffmpeg_process_handle = None

        self.var_localCamOption = tk.IntVar(value=2)
        self.var_camAddress = tk.StringVar(value="")
        self.var_botToken = tk.StringVar(value="")

        #This is a thread safe queue, as I've been using through this whole project
        self.message_queue = queue.Queue(maxsize=200)

    def draw(self):

        #This unsightly blob renders the app GUI
        
        app_label = ttk.Label(self.root, text="Byakugan", font=("Helvetica", 18, "bold"))
        app_label.grid(row=0, column=0, columnspan=2)

        os_label = ttk.Label(self.root, text=f"Operating System: {self.os}", font=("Times New Roman", 12))
        os_label.grid(row=1, column=0, sticky="w", pady=20)

        camera_options_label = ttk.Label(self.root, text="Camera Options", font=("Times New Roman", 16, "bold"))
        camera_options_label.grid(row=3, column=0, columnspan=2, sticky="w")

        windows_warning_label = ttk.Label(self.root, text="Byakugan uses Docker. Docker directly supports mounting your webcam to container on Linux, so you can either use your locally attached camera, or get a RTMP stream from another source.", wraplength=750, font=("Times New Roman", 12))
        windows_warning_label.grid(row=4, column=0, columnspan=2, pady=5)

        webcam_frame = ttk.Frame(self.root)
        webcam_frame.grid(row=5, column=0, sticky="w", pady=10)

        windows_webcam_setting = ttk.Radiobutton(webcam_frame, text="Use locally attached camera", variable=self.var_localCamOption, value=1, command=lambda: toggleEntry(entry_camAddress, "disabled"))
        windows_webcam_setting.grid(row=0, column=0, padx=100)

        windows_webcam_setting = ttk.Radiobutton(webcam_frame, text="Use external network video feed",  variable=self.var_localCamOption, value=2, command=lambda: toggleEntry(entry_camAddress, "enabled"))
        windows_webcam_setting.grid(row=0, column=1, padx=100)

        addr_frame = ttk.Frame(self.root)
        addr_frame.grid(row=6, column=0, columnspan=2)

        label_camAddress = ttk.Label(addr_frame, text="Camera RTMP Server Address: ")
        label_camAddress.grid(row=0, column=0)

        entry_camAddress = ttk.Entry(addr_frame, textvariable=self.var_camAddress)
        entry_camAddress.grid(row=0, column = 1)

        bt_frame = ttk.Frame(self.root)
        bt_frame.grid(row=7, column=0, columnspan=2, pady=(30, 30))

        label_botToken = ttk.Label(bt_frame, text="Telegram Bot Token: ")
        label_botToken.grid(row=0, column=0)

        self.entry_botToken = ttk.Entry(bt_frame, textvariable=self.var_botToken)
        self.entry_botToken.grid(row=0, column = 1)

        self.text_slog = tk.Text(self.root, height=7, width=50, wrap="word", state="disabled")
        self.text_slog.grid(row=8, column=0, sticky="nsew", padx=(10, 0))

        scrollbar = ttk.Scrollbar(self.root, command=self.text_slog.yview)
        scrollbar.grid(row=8, column=1, sticky="ns")
        self.text_slog.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(30, 0))
        self.button_start = ttk.Button(button_frame, text="Start", command=self.start)
        self.button_start.grid(row=0, column=0)
        self.button_stop = ttk.Button(button_frame, text="Stop", command=self.stop)
        self.button_stop.grid(row=0, column=1)

        threading.Thread(target=self.messageLoop, daemon=True).start()

    def loop(self):
        self.root.mainloop()

    def start(self):
        if self.isStarted:
            return
        
        self.enableLogging.set()
        self.__startDocker()
            
        self.isStarted = True
        toggleEntry(self.button_stop, "enabled")
        toggleEntry(self.button_start, "disabled")

    def disableButtons(self):
        toggleEntry(self.button_stop, "disabled")
        toggleEntry(self.button_start, "disabled")

    def enableButtons(self):
        toggleEntry(self.button_stop, "enabled")
        toggleEntry(self.button_start, "enabled")

    def stop(self):

        if not self.isStarted:
            return
        
        self.__endDocker()
        self.isStarted = False
        toggleEntry(self.button_stop, "disabled")
        toggleEntry(self.button_start, "enabled")

    def displayMessage(self, text):
        try:
            self.message_queue.put_nowait(text)
        except queue.Full:
            pass      

    def __printMessage(self, text):
        self.text_slog.config(state="normal")
        self.text_slog.insert(tk.END, text + "\n")
        self.text_slog.config(state="disabled")
        self.text_slog.see(tk.END)

    def messageLoop(self):

        while True:
            try:
                msg = self.message_queue.get(block=False)
                self.root.after(0, self.__printMessage, msg)  # Safe UI update
            except queue.Empty:
                pass

    def __startDocker(self):
        os.environ["DOCKER_HOST_IP"] = self.ip_address
        os.environ["BYAKUGAN_BOT_TOKEN"] = self.var_botToken.get()

        if self.var_localCamOption.get() == 1:
            self.docker_process_handle = subprocess.Popen(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.override-linux.yml", "up", "-d"], env={**os.environ}, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
        else:
            self.docker_process_handle = subprocess.Popen(["docker", "compose", "-f", "docker-compose.yml", "up", "-d"], env={**os.environ,"CAMERA_FEED_SOURCE" : self.var_camAddress}, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)

        threading.Thread(target=self.__docker_log, daemon=True).start()

    def __docker_log(self):

        while True:

            if not self.enableLogging.is_set():
                break

            try:
                while self.docker_process_handle and self.docker_process_handle.poll() is None:
                    line = self.docker_process_handle.stdout.readline()

                    if line:
                        self.root.after(0, self.displayMessage, line.strip()) 

                        if "Container byakugan" in line and "Starting" in line:
                            webbrowser.open("http://"+self.ip_address+":5000")
                    
            except Exception as e:
                self.root.after(0, self.displayMessage, f"Docker log error: {e}")

    def __endDocker(self):

        self.displayMessage("Ending docker...this may take a while")
        self.root.after(0, self.disableButtons)

        #I realize that this is hardly done in Python
        #although people do this in JS all the time
        #This stops the app from freezing up when you close docker
        def edfunc():
            subprocess.run(["docker", "compose", "down"], check=True)
            self.docker_process_handle = None
            self.displayMessage("Docker has been shut down")
            self.enableLogging.clear()
            self.root.after(0, self.enableButtons)

        threading.Thread(target=edfunc, daemon=True).start()


if __name__ == "__main__":

    gui = None

    if platform.system() == "Windows":
        gui = WindowsGUI()
    elif platform.system() == "Linux":
        gui = LinuxGUI()
    else:
        print("Incompatible system")
        sys.exit(0)

    gui.createWindowAndSetDefaults()
    gui.draw()
    gui.loop()