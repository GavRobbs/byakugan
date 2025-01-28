import cv2 as cv
import numpy as np
import queue
from functools import reduce

#This uses an adaptive background, the alpha variable is the learning rate
#and the higher it is, the faster objects "fade" into the background
def get_adaptive_background(frame, bg_model, alpha=0.01):
    frame_float = frame.astype(float)
    bg_float = bg_model.astype(float)

    new_bg = cv.addWeighted(bg_float, 1-alpha, frame_float, alpha, 0)
    return new_bg.astype(np.uint8)

#This helps us to handle variable lighting conditions from the camera
#We also try to guess at creating a shadow mask
def handle_lighting_changes(frame, bg_model):
    frame_hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    bg_hsv = cv.cvtColor(bg_model, cv.COLOR_BGR2HSV)

    frame_h, frame_s, frame_v = cv.split(frame_hsv)
    bg_h, bg_s, bg_v = cv.split(bg_hsv)

    diff_h = cv.absdiff(frame_h, bg_h)
    diff_s = cv.absdiff(frame_s, bg_s)
    diff_v = cv.absdiff(frame_v, bg_v)

    #Shadows lower brightness but don't change hue
    shadow_mask = (frame_s > 50) & (frame_v > bg_v - 30)

    combined_diff = (0.5 * diff_h + 0.3 * diff_s + 0.2 * diff_v).astype(np.uint8)
    _, mask = cv.threshold(combined_diff, 30, 255, cv.THRESH_BINARY)
    mask = cv.bitwise_and(mask, mask, mask=shadow_mask.astype(np.uint8))
    return mask

#We do some postprocessing for open and closing here
def pp_mask(mask):
    kernel_close = np.ones((5, 5), np.uint8)
    kernel_open = np.ones((3, 3), np.uint8)
    
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel_close)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel_open)

    return mask

#We fill internal holes in objects
def fill_holes(mask):
    mask_inv = cv.bitwise_not(mask)
    filled = mask_inv.copy()
    h, w = mask.shape
    border_mask = np.zeros((h+2, w+2), np.uint8)
    cv.floodFill(filled, border_mask, (0, 0), 255)
    filled_inv = cv.bitwise_not(filled)
    final = cv.bitwise_or(mask, filled_inv)
    return final

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
        avg_pos = reduce(lambda t1, t2: (t1.centroid[0] + t2.centroid[0], t1.centroid[1] + t2.centroid[1]), to_notify) / len(to_notify)
        msg = f'{len(to_notify)} objects detected, with average position at {"bottom" if avg_pos[1] >= 300 else "top"} - {"left" if avg_pos[0] > 400 else "right"}'
        message_queue_add_func(msg)

            
    for new_det in unmatched_detections:
        old_to.append(new_det)