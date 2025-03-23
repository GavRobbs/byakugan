import unittest
import utils
import cv2 as cv


class TestStream(unittest.TestCase):

    def setUp(self):
        self.cam = None
    
    def test_OpenCamera(self):
        
        #This test detects if we successfully connected to the video stream

        self.cam = cv.VideoCapture(utils.get_camera_feed_source())

        self.assertTrue(self.cam.isOpened())


    def test_DetectVideoStream(self):

        #This test checks if we can read a frame from the video stream

        frameRead, frame = self.cam.read()

        self.assertEqual(frameRead, True)
        self.assertNotEqual(frame, None)

    def tearDown(self):
        self.cam.release()
        return super().tearDown()

    