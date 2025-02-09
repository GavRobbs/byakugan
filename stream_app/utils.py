import cv2 as cv
import numpy as np
import queue
from collections import deque
from functools import reduce
from decouple import config
import socket

def get_camera_feed_source():
    #This allows me to read it from my environment variable in my dockerfile
    source = config("CAMERA_FEED_SOURCE", default=None)

    if source == None or source == "DEFAULT":
        return 0
    else:
        return source

#created this object class to make it easy to track objects
class TrackedObject:
    _id_counter = 0

    @staticmethod
    def generate_id():
        """Generate and return a new unique ID."""
        TrackedObject._id_counter += 1
        return TrackedObject._id_counter
        
    def __init__(self, b, c, l):
        self.id = str(TrackedObject.generate_id())
        self.bounding_box = b
        self.lastSeenFrame = l
        self.velocity = 0.0
        self.enabled = True
        self.contour = c
        self.notified = False

    @property
    def centroid(self):
        x, y, w, h = self.bounding_box
        return (x + w // 2, y + h // 2)

    @property
    def area(self):
        return cv.contourArea(self.contour)

    """
    @property
    def centroid(self):
        M = cv.moments(self.contour)

        if M['m00'] != 0:  
            c_x = int(M['m10'] / M['m00'])
            c_y = int(M['m01'] / M['m00'])
        else:
            c_x, c_y = 0, 0

        return (c_x, c_y)"""
    
class ObjectDetector:
    #This class gives me a way to try out some different object detection algos without clogging
    #up the actual thread
    def __init__(self):
        pass

    def iterate(self):
        #This function is called on every iteration of the loop
        #It should return the current foreground mask
        raise NotImplementedError(message="Please implement the iterate function")
    
class MovingMedianObjectDetector:
    #This implements a moving median object detector
    def __init__(self, bufsize=10, shadow_threshold=30):
        self.background_buffer = deque(maxlen=bufsize)
        self.shadow_threshold = shadow_threshold

    def generate_median_background(self):
        #This is some numpy wizardry to get the median value of every corresponding pixel each of the stored frames in the array buffer
        stack = np.stack(self.background_buffer, axis=0)
        return np.median(stack, axis=0).astype(np.uint8)
    
    def generate_fgmask(self, current_frame, median_background):

        #The first part of this step makes an attempt to filter out shadows
        #its conventionally held that in the HSV color space, colors keep H and S, but decrease V (value)
        #So we extract the value channel and compare the absolute difference and disard it
        #if it is less than our shadow threshold
        frame_hsv = cv.cvtColor(current_frame, cv.COLOR_BGR2HSV)
        median_background_hsv = cv.cvtColor(median_background, cv.COLOR_BGR2HSV)

        fg_mask = cv.absdiff(frame_hsv[:, :, 2], median_background_hsv[:, :, 2])
        fg_mask[fg_mask < self.shadow_threshold] = 0

        #We then apply a binary threshold to filter out pixels below a certain intensity
        _, fg_mask = cv.threshold(fg_mask, 40, 255, cv.THRESH_BINARY)
        return fg_mask
    
    def morphology_patch(self, fg_mask):
        #We do some opening and closing here to help reduce noise and hopefully fill in spaces
        kernel = np.ones((3,3), np.uint8)
        mask = cv.morphologyEx(fg_mask, cv.MORPH_OPEN, kernel)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
        mask = cv.dilate(mask, kernel, 7)
        mask = cv.medianBlur(mask, 3)
        return mask 

    def iterate(self, current_frame):

        self.background_buffer.append(current_frame)        
        median_background = self.generate_median_background()
        fg_mask = self.generate_fgmask(current_frame, median_background)
        fg_mask = self.morphology_patch(fg_mask)

        return fg_mask



def match_objects(detections, frame_count, old_to, message_queue_add_func, distance_threshold = 200, max_disappearance = 40, notify_time = 30):

    #Iterate through each object being tracked
    #Calculate the distance between the tracked object and all of the newly detected objects
    #Get the minimum distance in that array, and the corresponding index of that object
    #because that new detection is likely where the previous object that was being tracked has moved to

    #If there are any leftover detections, they are likely new objects, so we add them

    unmatched_detections = detections.copy()

    to_notify = []

    for tracked in old_to:
        if not tracked.enabled:
            continue
            
        distances = [np.linalg.norm(np.array(tracked.centroid) - np.array(d.centroid)) for d in unmatched_detections]

        if len(distances) > 0:
            min_distance = min(distances)
            best_match_index = np.argmin(distances)


            if min_distance < distance_threshold:
                best_match_bbox = detections[best_match_index].bounding_box
    
                tracked.bounding_box = best_match_bbox
                tracked.lastSeenFrame = frame_count
    
                del unmatched_detections[best_match_index]

        if frame_count - tracked.lastSeenFrame > max_disappearance:
            tracked.enabled = False

        if frame_count - tracked.lastSeenFrame > notify_time and tracked.notified is False:
            tracked.notified = True

            to_notify.append(tracked)

            #client.messages.create(
            #    from_="+12525905642",
            #    body=f'{body_size} object detected on {"left" if tracked.centroid[0] > 400 else "right"} side',
            #    to="+18762834804"
            #)

    if len(to_notify) == 0:
        #If we haven't picked up anything, don't say anything
        pass
    elif len(to_notify) <= 3:
        #If we've picked up 3 or less objects, we can dump details in the text message
        complete_msg = ""
        for t in to_notify:
            body_size = "Small" if t.area < 13000 else "Big"
            complete_msg = complete_msg + f'{body_size} object detected on {"left" if tracked.centroid[0] > 400 else "right"} side.'
            message_queue_add_func(complete_msg)
    else:
        #If we've picked up more than 3 objects, we summarize everything
        avg_pos = (
                    sum(t.centroid[0] for t in to_notify) / len(to_notify),
                    sum(t.centroid[1] for t in to_notify) / len(to_notify)
                    )
        msg = f'{len(to_notify)} objects detected, with average position at {"bottom" if avg_pos[1] >= 300 else "top"} - {"left" if avg_pos[0] > 400 else "right"}'
        message_queue_add_func(msg)

            
    for new_det in unmatched_detections:
        old_to.append(new_det)

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1" 
    finally:
        s.close()
    return ip_address