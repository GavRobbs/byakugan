import subprocess
import re
import configparser
import sys
import platform
import os

import socket

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.connect(("8.8.8.8", 80)) #Try using google's public DNS
        return my_socket.getsockname()[0]
    
def read_settings():
    previous_config = configparser.ConfigParser()
    config_found = previous_config.read("config.ini")

    if not config_found:
        return None

    opsys = previous_config.get("byakugan","os", fallback=None) #Options are Windows or Linux
    host_ip = previous_config.get("byakugan","ip", fallback=None) #Gives the host IP
    bot_token = previous_config.get("byakugan", "bot_token", fallback=None) #The bot token
    video_source_type = previous_config.get("byakugan","source_type", fallback=None) #Can be 'stream' or 'device'

    #If video_source_type is stream, then this gives the rtmp server address (on windows it can be self). Ignored if its device,
    #because we're going to use the default usb webcam on linux
    video_source_spec = previous_config.get("byakugan", "source_details", fallback=None) 

    if opsys is None or host_ip is None or video_source_type is None or video_source_spec is None or bot_token is None:
        return None
    
    if opsys == "Windows":
        if video_source_type != "stream":
            print("Windows only supports video via RTMP server due to docker limitations. The video source can come from the Windows system itself, via a dummy RTMP server which is fed with ffmpeg, or from a diferent RTMP stream source. Please redo the configuration to set it properly.")
            return None
        else:
            return {"os":opsys, "ip":host_ip, "source_type": "stream", "source_details":video_source_spec, "bot_token":bot_token}
    else:
        return {"os":opsys, "ip":host_ip, "source_type": video_source_type, "source_details":video_source_spec, "bot_token":bot_token}
    
def process_settings(settings):
    if settings["os"] == "Windows":
        windows_setup(settings["ip"], settings["source_details"], settings["bot_token"])
    else:
        linux_setup(settings["ip"], True if settings["source_type"] == "device" else False, settings["source_details"], settings["bot_token"])

    sys.exit(0)

def windows_start_ffmpeg():
    camera_name_query = subprocess.run(["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    #Use a regex to extract a camera name
    match = re.search(r'"(.*?)"', camera_name_query.stdout)
    if match:
        camera_name = match.group(1)
        print(f"Using camera: {camera_name}")
    else:
        print("No camera found!")
        exit(1)

    subprocess.run(["ffmpeg", "-f", "dshow", "-i", f'video={camera_name}', "-vcodec", "libx264", "-preset", "veryfast", "-b:v", "1M", "-maxrate", "3000k", "-bufsize", "512M", "-an", "-f", "flv", "rtmp://localhost/stream/test"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
    
def windows_setup(host_ip, rtmp_addr, bot_token):
    os.environ["DOCKER_HOST_IP"] = host_ip
    os.environ["BYAKUGAN_BOT_TOKEN"] = bot_token

    print(os.environ)

    if rtmp_addr == "self":
        subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.override.yml", "up", "-d"], check=True, env={**os.environ})
        print("The containers for the frontend, server and rtmp server have been created.")
        print(f"Byakugan is now starting. Navigate to http://{host_ip} to use it. Exit with Ctrl+C then run python undeploy.py to shut down fully.")
        print("The RTMP feed will now be started using ffmpeg. Don't close this application or else it will disconnect.")
        windows_start_ffmpeg()
    else:
        subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "up", "-d"],
                       check=True, env={**os.environ,"CAMERA_FEED_SOURCE" : rtmp_addr})
        print(f"The containers for the frontend and server have been created. The video will come from the rtmp server you specified at {rtmp_addr}")
        print(f"Byakugan is now starting. Navigate to http://{host_ip} to use it. Run python undeploy.py to shut down fully.")

def linux_setup(host_ip, attachedDevice=True, path="", bot_token=""):
    os.environ["DOCKER_HOST_IP"] = host_ip
    os.environ["BYAKUGAN_BOT_TOKEN"] = bot_token

    if attachedDevice is True:
        subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.override-linux.yml", "up", "-d"], check=True, env={**os.environ})
        print(f"Byakugan started. Navigate to http://{host_ip} to use it. Run python undeploy.py to shut down fully.")
    else:
        subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "up", "-d"], check=True,env={**os.environ,"CAMERA_FEED_SOURCE" :path})
        print(f"Byakugan started. Navigate to http://{host_ip} to use it. Run python undeploy.py to shut down fully.")

def write_config_file(host_ip, operating_system, source_type, source_feed, bot_token):
    config = configparser.ConfigParser()
    config["byakugan"] = {
        "os": operating_system,
        "ip": host_ip,
        "source_type" : source_type,
        "source_details" : source_feed,
        "bot_token" : bot_token
    }

    with open("config.ini", 'w') as cfile:
        config.write(cfile)

if __name__ == "__main__":

    print("Welcome to Byakugan.")
    print("Byakugan is deployed via Docker, and consists of three components:")
    print("- The frontend web interface you can access in the browser")
    print("- The server that manages the requests from the frontend and handles the video processing")
    print("- The video source, which can be an attached USB camera or RTMP stream.")
    input("\nPress RETURN to continue")

    print("\nThere are two primary ways of configuring Byakugan:")
    print("1) Everything on one device, meaning the server, frontend and video source all reside on the same system.")
    print("2) The server and the frontend on one device, and the video source coming from a RTMP stream from another device.")
    input("\nPress RETURN to continue\n")

    settings = read_settings()

    if settings is not None:
        res = input("A previous configuration has been detected. Do you want to use it? Press (Y)es or any other option for no. ")
        if(str(res).lower() == "y"):
           process_settings(settings)
        else:
            print("Creating a new settings file")
    else:
        print("Error: Invalid settings file or no settings file detected.\n")

    try:
        host_ip = get_local_ip() + ":5000"
    except Exception as e:
        print("The script was unable to determine your local IP address automatically.")
        ip_entered = False

        while not ip_entered:
            raw_ip = input("Please enter the IP address (and port) that you expect Byakugan to be served from, in the format X.X.X.X:PORT (eg. 192.168.0.2:5000): ")
            ip_matches = re.match(r'(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(:\d{2,5})?', raw_ip)

            if ip_matches:
                ip_entered = True
                host_ip = ".".join(ip_matches.groups()[:4])

                #If we have a port
                if ip_matches.groups(5):
                    #Chop off the starting colon
                    host_ip = host_ip + ip_matches.groups()[5][1:]
            else:
                print("Invalid IP address specified.")

    operating_system_name = platform.system()

    bot_token = input("Please enter your telegram bot token: ")

    if operating_system_name == "Windows":
        print(f'A Windows operating system has been detected. The host IP is {host_ip}.')
        print("Docker on Windows does not allow direct access to USB webcam hardware, so if you want to use a locally attached camera, a RTMP streaming server will have to be created and a ffmpeg stream fed into the container. The quality of the feed from this is highly dependent on your network speed.\n")

        windows_choice_answered = False
        while not windows_choice_answered:
            res = input("Do you want to do this (Y) or use an external server to supply the video feed (N)? ").lower()
            if res == "y":
                windows_choice_answered = True
                write_config_file(host_ip, operating_system_name, "stream", "self", bot_token)
                process_settings(read_settings())

            elif res == "n":
                windows_choice_answered = True
                valid_feed_server = False                

                while not valid_feed_server:
                    feed_addr = input("Please enter the feed address in the format <scheme>://<address>/: ")
                    feed_regex = r"[a-z]+:\/\/[^\s\/]+\/[^\s\/]+\/[^\s]+"
                    
                    matches = re.findall(feed_regex, feed_addr)
                    if matches is not None:
                        valid_feed_server = True
                        windows_choice_answered = True

                write_config_file(host_ip, operating_system_name, "stream", feed_addr,bot_token)
                process_settings(read_settings())

            else:
                #Restart the loop
                pass
        
    else:
        print(f"A Linux based machine has been detected. The host IP is {host_ip}. You can: ")
        print("1) Use an attached USB webcam at /dev/video0 - recommended for Raspberry Pi due to compatibility issues with RTMP server")
        print("2) Use an external video feed eg. RTMP server or RTSP camera\n")

        linux_choice_answered = False
        while not linux_choice_answered:

            linux_choice = input("Which one would you prefer, option 1 or 2? ")
            if linux_choice == "1":
                linux_choice_answered = True
                write_config_file(host_ip, "Linux", "device", "self", bot_token)
                process_settings(read_settings())
            elif linux_choice == "2":
                valid_feed_server = False                

                while not valid_feed_server:
                    feed_addr = input("Please enter the feed address in the format <scheme>://<address>/: ")
                    feed_regex = r"[a-z]+:\/\/[^\s\/]+\/[^\s\/]+\/[^\s]+"
                    
                    matches = re.findall(feed_regex, feed_addr)
                    if matches is not None:
                        valid_feed_server = True
                        linux_choice_answered = True

                write_config_file(host_ip, "Linux", "stream", feed_addr, bot_token)
                process_settings(read_settings())
            else:
                print("Please enter 1 or 2")

#ffmpeg -f dshow -i video="NexiGo N930E FHD Webcam" -vcodec libx264 -preset veryfast -b:v 500k -maxrate 3000k -bufsize 512M -an -f flv rtmp://localhost/stream/test
