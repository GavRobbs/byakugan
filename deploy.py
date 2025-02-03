import subprocess
import os
import re

import socket

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.connect(("8.8.8.8", 80)) #Try using google's public DNS
        return my_socket.getsockname()[0]


if __name__ == "__main__":

    print(get_local_ip())

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

    operating_system_name = os.name

    try:
        host_ip = get_local_ip()
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
                
    if operating_system_name == "nt":
        print(f'A Windows operating system has been detected. The host IP is {host_ip}.')
        print("Docker on Windows does not allow direct access to USB webcam hardware, so if you want to use a locally attached camera, a RTMP streaming server will have to be created and a ffmpeg stream fed into the container. The quality of the feed from this is highly dependent on your network speed.\n")
        os.environ["DOCKER_HOST_IP"] = host_ip

        windows_choice_answered = False
        while not windows_choice_answered:
            res = input("Do you want to do this (Y) or use an external server to supply the video feed (N)? ").lower()
            if res == "y":
                windows_choice_answered = True
                camera_name_query = subprocess.run(["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

                #Use a regex to extract a camera name
                match = re.search(r'"(.*?)"', camera_name_query.stdout)
                if match:
                    camera_name = match.group(1)
                    print(f"Using camera: {camera_name}")
                else:
                    print("No camera found!")
                    exit(1)
                subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.override.yml", "up", "-d"], check=True)
                print("The containers for the frontend, server and rtmp streamer have been created.")
                print("Byakugan is now starting.")
                print("The RTMP server will now be started using ffmpeg. Don't close this application or else it will disconnect.")

                subprocess.run(["ffmpeg", "-f", "dshow", "-i", f'video={camera_name}', "-vcodec", "libx264", "-preset", "veryfast", "-b:v", "1M", "-maxrate", "3000k", "-bufsize", "512M", "-an", "-f", "flv", "rtmp://localhost/stream/test"],
                               check=True,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)

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

                    subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "up", "-d"], 
                                   check=True,
                                   env={
                                       **os.environ,
                                       "CAMERA_FEED_SOURCE" : feed_addr
                                        })
            else:
                #Restart the loop
                pass
        
    else:
        print(f"A Linux based machine has been detected. The host IP is {host_ip}. You can: ")
        print("1) Use an attached USB webcam at /dev/video0")
        print("2) Use an external video feed eg. RTMP server or RTSP camera\n")

        linux_choice_answered = False
        rtmp_addr = ""
        os.environ["DOCKER_HOST_IP"] = host_ip

        while not linux_choice_answered:

            linux_choice = input("Which one would you prefer, option 1 or 2? ")
            if linux_choice == "1":
                linux_choice_answered = True
                subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.override-linux.yml", "up", "-d"], check=True)
            elif linux_choice == "2":
                valid_feed_server = False                

                while not valid_feed_server:
                    feed_addr = input("Please enter the feed address in the format <scheme>://<address>/: ")
                    feed_regex = r"[a-z]+:\/\/[^\s\/]+\/[^\s\/]+\/[^\s]+"
                    
                    matches = re.findall(feed_regex, feed_addr)
                    if matches is not None:
                        valid_feed_server = True
                        linux_choice_answered = True

                    subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "up", "-d"], 
                                   check=True,
                                   env={
                                       **os.environ,
                                       "CAMERA_FEED_SOURCE" : feed_addr
                                        })

            else:
                print("Please enter 1 or 2")

    print("Byakugan started via docker-compose")
    print(f"Navigate to http://{host_ip}:5000 to use Byakugan.")

#ffmpeg -f dshow -i video="NexiGo N930E FHD Webcam" -vcodec libx264 -preset veryfast -b:v 500k -maxrate 3000k -bufsize 512M -an -f flv rtmp://localhost/stream/test
