from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2 as cv
import queue
import threading
from utils import * 
import time
import sqlite3
import dbutils
import sys
import ffmpeg
import os
from bot import TelegramBotThread
import socket

# Create our Flask app
app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app) 

# Create a thread-safe queue for capture
frame_queue = queue.Queue(maxsize=35)

# Create a thread-safe queue for recording
recording_queue = queue.Queue(maxsize=90)

#The message queue takes the messages from object detection and uses them to activate the camera
message_queue = queue.Queue(maxsize=1)

recording_event = threading.Event()
record_count = 0

last_msg_time = 0
suppress_msg_time = 200.0   

# Global variable for the latest processed frame
captured_frame = None

tracked_objects = []
frame_count = 0      
server_linked = False

DOCKER_HOST_IP = config("DOCKER_HOST_IP")

def capture_and_process_frames():
    global frame_queue, captured_frame, tracked_objects, frame_count, recording_queue
    source = get_camera_feed_source()
    print("The video source is " + str(source))
    camera = cv.VideoCapture(source)
    camera.set(cv.CAP_PROP_AUTOFOCUS, 0) # turn the autofocus off

    if not camera.isOpened():
        print("Error: Camera not opened!")
        return
    
    object_detector = MovingMedianObjectDetector()

    while True:
        success, frame = camera.read()
        if not success or frame is None:
            print("Error: Failed to capture frame!")
            break

        #We always resize the frame to cut down on what it takes to process it
        frame =  cv.resize(frame, (800, 600), interpolation=cv.INTER_AREA)

        if recording_queue.full():
            recording_queue.get()
        
        recording_queue.put(frame.copy())

        fgmask = object_detector.iterate(frame)

        contours, hierarchy = cv.findContours(image=fgmask, mode=cv.RETR_EXTERNAL, method=cv.CHAIN_APPROX_SIMPLE)
        new_detections = []
        for contour in contours:
            area = cv.contourArea(contour)
            if area > 3500 and area < 30000:
                new_detections.append(TrackedObject(cv.boundingRect(contour), contour, frame_count))

        #Check the contours detected and compare them to the old ones to look for motion

        match_objects(new_detections, frame_count, tracked_objects, add_to_mq)

        tracked_objects = [obj for obj in tracked_objects if obj.enabled]

        #Just uncomment this if I want to see how tracking is working
        for t_obj in tracked_objects:
            cv.circle(frame, t_obj.centroid, 10, (255, 0, 0), -1)
            cv.putText(frame, " " + t_obj.id, t_obj.centroid, cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0))

        frame_count += 1

        #If the queue is full, drop the oldest frame
        if frame_queue.full():
            frame_queue.get()

        #put it in the queue
        frame_queue.put(frame)

        #Just for testing
        #frame_queue.put(fgmask.copy())

    camera.release()

def pass_frame():
    #This thread pulls the frame from the queue and sets it up for
    #display via the MJPEG stream created by the generate_stream function
    global frame_queue, captured_frame
    while True:
        try:
            captured_frame = frame_queue.get(timeout=1)
        except queue.Empty:
            continue

def add_to_mq(msg):
    global message_queue, last_msg_time, suppress_msg_time
    new_time = time.time()
    if new_time - last_msg_time > suppress_msg_time:
        print("Ready to message again")
        last_msg_time = new_time
        message_queue.put_nowait(msg)

def handle_messages():
    global message_queue, record_count, recording_event  

    while True:
        try:
            msg = message_queue.get(timeout = 1)
            print(msg)
            if not recording_event.is_set():
                record_count = 0
                recording_thread = threading.Thread(target=record_frames, args=[msg,], daemon=False)
                recording_thread.start()
                recording_event.set()
        except queue.Empty:
            continue
        except Exception as e:
            print(f'Error in message handler: {e}')
        time.sleep(2)

def record_frames(desc=None):
    global recording_queue, recording_event, record_count
    sqlite_conn = None
    sqlite_cursor = None

    try:
        sqlite_conn, sqlite_cursor = dbutils.load_database()
        video_fn, alert_id = dbutils.create_recording(sqlite_conn, sqlite_cursor, desc)
    except RuntimeError:
        print("Error loading database")
        sys.exit(1)

    video_writer = cv.VideoWriter("/app/recordings/" + video_fn + ".avi", cv.VideoWriter.fourcc(*'XVID'), 30, (800, 600))

    firstFrame = True

    while recording_event.is_set() and record_count < 600:

        try:
            current_recorded_frame = recording_queue.get(timeout=1)
            video_writer.write(current_recorded_frame)
            record_count += 1

            if firstFrame:
                firstFrame = False
                dbutils.add_thumbnail_to_alert(sqlite_conn, sqlite_cursor, alert_id, current_recorded_frame)
                alert_details = dbutils.get_alert_details(sqlite_conn, sqlite_cursor, alert_id)

                try:
                    bot_thread.add_message_to_queue({
                        "name": "alert",
                        "text" : f'*New event detected!* \n\n*Description:* {alert_details['description']} \n\nReview the footage [here]({"http://" + DOCKER_HOST_IP + ":5000/#/alerts/" + str(alert_id)}).',
                        "image" : alert_details['thumbnail']                    
                    })
                except queue.Full:
                    print("Bot message queue is full")

        except queue.Empty:
            pass

    record_count = 0
    recording_event.clear()
    video_writer.release()

    #Use ffmpeg to convert to mp4 for better browser support
    ffmpeg.input("/app/recordings/" + video_fn + ".avi").output("/app/recordings/" + video_fn + ".mp4", vcodec="libx264", acodec="aac", threads=2, video_bitrate='500K', preset='ultrafast').run(quiet=True)
    #Clear up the old file
    os.remove("/app/recordings/" + video_fn + ".avi")



def generate_stream():
    #This is a generator function used to create the stream response
    global captured_frame
    while True:
        if captured_frame is not None:
            _, buffer = cv.imencode('.jpg', captured_frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
@app.route('/')
@app.route('/<path:path>')
def serve_frontend(path="index.html"):
    if path.startswith("api/"):  # Avoid serving API routes as frontend files
        return "Not Found", 404
    return send_from_directory(app.static_folder, path)
            
@app.route("/api/live")
def video_feed():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    #Opening a new connection is faster and way simpler than having
    #to manage all the threads
    page_no = request.args.get("page")

    if not page_no:
        page_no = 1

    sqlite_conn, sqlite_cursor = dbutils.load_database()
    alerts = dbutils.get_alerts_data(sqlite_conn, sqlite_cursor, 5, page_no)
    return jsonify(alerts), 200

@app.route("/api/alerts/<alert_id>", methods=["GET", "DELETE"])
def get_alert_detail(alert_id):

    sqlite_conn, sqlite_cursor = dbutils.load_database()

    if request.method == "GET":
        alert = dbutils.get_alert_details(sqlite_conn, sqlite_cursor, alert_id)
        return jsonify(alert), 200
    else:
        print("Alert deleted")
        dbutils.delete_alert(sqlite_conn, sqlite_cursor, alert_id)
        return jsonify({"message" : "Alert deleted"}), 200
    
   
@app.route("/api/setup/link_bot", methods=["POST",])
def link_bot():
    data = request.json
    sqlite_conn, sqlite_cursor = dbutils.load_database()
    dbutils.update_setting_value(sqlite_conn, sqlite_cursor, "BOT_CHAT_ID", data["chat_id"])

    bot_thread.add_message_to_queue({
        "name": "bot_chat_id",
        "value": data["chat_id"]
    })

    bot_thread.add_message_to_queue({
        "name": "system",
        "text": "Byakugan linked to Hyuga bot"
    })

    return Response("OK", status=200, mimetype="text/plain")

@app.route("/api/setup", methods=["GET",])
def get_setup_status():
    global server_linked
    sqlite_conn, sqlite_cursor = dbutils.load_database()

    chat_id = dbutils.get_setting_value(sqlite_conn, sqlite_cursor, "BOT_CHAT_ID")

    if chat_id is not None:
        return Response("COMPLETE", status=200, mimetype="text/plain")
    else:
        return Response("INCOMPLETE", status=200, mimetype="text/plain")


@app.route("/api/thumbnails/<filename>")
def get_image(filename):
    return send_from_directory("/app/thumbnails", filename)

@app.route("/api/recordings/<filename>")
def get_video(filename):
    as_attachment = request.args.get("download")

    #The as_attachment variable allows you to change the Content-Disposition
    #to determine if it displays in the browser or downloads

    return send_from_directory("/app/recordings", filename, mimetype="video/mp4", as_attachment = True if as_attachment == "yes" else False)


@app.route("/api/record", methods=["POST", "GET"])
def recording_state():
    global record_count

    #We can use get to check if we are recording or not
    if request.method == "GET":
        return jsonify({"recording" : "on" if recording_event.isSet() else "off"}), 200
    elif request.method != "POST":
        #Give an error if the method is not get or post
        return "", 405
    
    #Fall through if the method is post
    data = request.json
    if "new_state" not in data:
        return jsonify({"error": "Please include a new_state field with a value of \"on\" or \"off\""}), 400
    
    if data["new_state"].lower() == "on":
        if not recording_event.is_set():
            record_count = 0
            recording_thread = threading.Thread(target=record_frames, args=["User generated recording",], daemon=False)
            recording_thread.start()
            recording_event.set()
            return jsonify({"status" : "Recording started successfully"}), 201
        else:
            return jsonify({"status" : "The program is already recording"}), 400
            
    elif data["new_state"].lower() == "off":
        recording_event.clear()
        return jsonify({"status" : "Recording stopped successfully"}), 201
    else:
        return jsonify({"error": "Please include a new_state field with a value of \"on\" or \"off\""}), 400
    

if __name__ == "__main__":

    capture_thread = threading.Thread(target=capture_and_process_frames, daemon=True)
    pass_thread = threading.Thread(target=pass_frame, daemon=True)
    messaging_thread = threading.Thread(target=handle_messages, daemon=True)
    bot_thread = TelegramBotThread()

    capture_thread.start()
    pass_thread.start()
    bot_thread.start()
    messaging_thread.start()

    app.run('0.0.0.0', port=5000)

    recording_event.clear()

