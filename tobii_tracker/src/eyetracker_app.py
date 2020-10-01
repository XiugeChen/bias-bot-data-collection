import wx
import threading
import socket
import time
import sys
import signal
import logging
import numpy as np
import tobii_research as tr

######## Global var ########
EYE_TRACKER = None

# Protocol
CLOSE_CODE = "CLOSE"

# Settings
HOST = "localhost"
PORT = 10000

# Screen
SCREEN_X = 1440
SCREEN_Y = 900

######## Functions and Classes ########

class DisplayFrame(wx.Frame):
    def __init__(self):
        global EYE_TRACKER

        super(DisplayFrame, self).__init__(parent=None, title='Display Page', size=wx.Size(SCREEN_X, SCREEN_Y))
        self.SetPosition((0, 0))

        if EYE_TRACKER is not None:
            EYE_TRACKER.subscribe_to(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback, as_dictionary=True)

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        back_btn = wx.Button(panel, label="Back")

        # sizer.AddStretchSpacer()
        sizer.Add(back_btn, 0, wx.CENTER)
        panel.SetSizer(sizer)

        back_btn.Bind(wx.EVT_BUTTON, self.on_press_back)
        self.Bind(wx.EVT_PAINT, self.draw_boundary)

        self.Show()

    def draw_boundary(self, event):
        dc = wx.PaintDC(self)

        dc.SetPen(wx.Pen('#4c4c4c', 1, wx.SHORT_DASH))
        dc.DrawRectangle(2, 20, SCREEN_X - 2, SCREEN_Y - 2)

    def display_gaze(self, x, y):
        dc = wx.ClientDC(self)

        dc.SetPen(wx.Pen('#4c4c4c', 1, wx.SHORT_DASH))
        dc.DrawRectangle(2, 20, SCREEN_X - 2, SCREEN_Y - 2)

        dc.SetPen(wx.Pen('RED'))
        dc.DrawCircle(x, y, 7)

    def gaze_data_callback(self, gaze_data):
        gaze_left_eye, gaze_right_eye = gaze_data['left_gaze_point_on_display_area'], gaze_data['right_gaze_point_on_display_area']

        try:
            # csv format: computer_time,data_type,screen_x,screen_y,left_x_per,left_y_per,right_x_per,right_y_per
            message = "{:d},gaze_data,{},{},{},{},{},{}".format(int(round(time.time() * 1000)), SCREEN_X, SCREEN_Y, gaze_left_eye[0], gaze_left_eye[1], gaze_right_eye[0],gaze_right_eye[1])
            client.send(message.encode('ascii'))
            logging.debug(message)

        except Exception as e:
            logging.error("[Error]", e.__class__, "occurred.")

        if not np.isnan(gaze_left_eye[0]):
            x = (gaze_left_eye[0] + gaze_right_eye[0]) / 2 if not np.isnan(gaze_right_eye[0]) else gaze_left_eye[0]
        else:
            x = gaze_right_eye[0] if not np.isnan(gaze_right_eye[0]) else 0.0

        if not np.isnan(gaze_left_eye[1]):
            y = (gaze_left_eye[1] + gaze_right_eye[1]) / 2 if not np.isnan(gaze_right_eye[1]) else gaze_left_eye[1]
        else:
            y = gaze_right_eye[1] if not np.isnan(gaze_right_eye[1]) else 0.0

        x = min(max(x, 0.0), 1.0)
        y = min(max(y, 0.0), 1.0)

        self.display_gaze(x * SCREEN_X, y * SCREEN_Y)

    def on_press_back(self, event):
        if EYE_TRACKER is not None:
            EYE_TRACKER.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, self.gaze_data_callback)

        SetupFrame()
        self.Hide()

class CaliResultFrame(wx.Frame):
    def __init__(self, cali_result):
        super(CaliResultFrame, self).__init__(parent=None, title='Calibration Result Page', size=wx.Size(SCREEN_X, SCREEN_Y))
        self.SetPosition((0, 0))

        self.cali_result = cali_result

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        cont_btn = wx.Button(panel, label='Continue')
        recali_btn = wx.Button(panel, label='Re-Calibration')

        # sizer.AddStretchSpacer()
        sizer.Add(cont_btn, 0, wx.CENTER)
        sizer.Add(recali_btn, 0, wx.CENTER)
        panel.SetSizer(sizer)

        cont_btn.Bind(wx.EVT_BUTTON, self.on_press_cont)
        recali_btn.Bind(wx.EVT_BUTTON, self.on_press_recali)
        self.Bind(wx.EVT_PAINT, self.draw_result)

        self.Show()

    def draw_result(self, event):
        dc = wx.PaintDC(self)

        dc.SetPen(wx.Pen('#4c4c4c', 1, wx.SHORT_DASH))
        dc.DrawRectangle(2, 20, SCREEN_X - 2, SCREEN_Y - 2)

        # Draw calibration points
        dc.SetPen(wx.Pen('RED'))
        for (x, y) in zip([0.2, 0.2, 0.5, 0.8, 0.8], [0.2, 0.8, 0.5, 0.2, 0.8]): # for (x, y) in zip([0.1, 0.1, 0.5, 0.9, 0.9], [0.1, 0.9, 0.5, 0.1, 0.9]):
            dc.DrawCircle(x * SCREEN_X, y * SCREEN_Y, 7)

        # Draw sample points:
        dc.SetPen(wx.Pen("BLUE"))

        try:
            for samples in self.cali_result.calibration_points:
                for sample in samples.calibration_samples:
                    left, right = sample.left_eye.position_on_display_area, sample.right_eye.position_on_display_area

                    if not np.isnan(left[0]):
                        x = (left[0] + right[0]) / 2 if not np.isnan(right[0]) else left[0]
                    else:
                        x = right[0] if not np.isnan(right[0]) else 0.0

                    if not np.isnan(left[1]):
                        y = (left[1] + right[1]) / 2 if not np.isnan(right[1]) else left[1]
                    else:
                        y = right[1] if not np.isnan(right[1]) else 0.0

                    x = min(max(x, 0.0), 1.0)
                    y = min(max(y, 0.0), 1.0)

                    dc.DrawCircle(x * SCREEN_X, y * SCREEN_Y, 7)
        except AttributeError or TypeError:
            logging.warn("Draw calibration results failed")

    def on_press_cont(self, event):
        DisplayFrame()
        self.Hide()

    def on_press_recali(self, event):
        CaliFrame()
        self.Hide()

class CaliFrame(wx.Frame):
    def __init__(self):
        super(CaliFrame, self).__init__(parent=None, title='Calibration Page', size=wx.Size(SCREEN_X, SCREEN_Y))
        self.SetPosition((0, 0))

        self.cali_result, self.finish_cali = {}, False
        self.cali_thread = threading.Thread(target=self.cali_start, args=())
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        cont_btn = wx.Button(panel, label='Continue')

        # sizer.AddStretchSpacer()
        sizer.Add(cont_btn, 0, wx.CENTER)
        panel.SetSizer(sizer)

        cont_btn.Bind(wx.EVT_BUTTON, self.on_press_cont)
        self.Bind(wx.EVT_PAINT, self.draw_cali_init)

        self.Show()
        self.cali_thread.start()

    def draw_cali_init(self, event):
        dc = wx.PaintDC(self)

        dc.SetPen(wx.Pen('#4c4c4c', 1, wx.SHORT_DASH))
        dc.DrawRectangle(2, 20, SCREEN_X - 2, SCREEN_Y - 2)

    def show_point(self, x, y):
        dc = wx.ClientDC(self)

        dc.SetPen(wx.Pen('#4c4c4c', 1, wx.SHORT_DASH))
        dc.DrawRectangle(2, 20, SCREEN_X - 2, SCREEN_Y - 2)

        dc.SetPen(wx.Pen('BLACK'))
        dc.DrawCircle(x, y, 10)

    def cali_start(self):
        global EYE_TRACKER

        if EYE_TRACKER is None:
            self.finish_cali = True
            return

        time.sleep(1.0)

        calibration = tr.ScreenBasedCalibration(EYE_TRACKER)

        # Enter calibration mode.
        calibration.enter_calibration_mode()
        logging.info("Entered calibration mode for eye tracker with serial number {0}.".format(EYE_TRACKER.serial_number))

        for (x, y) in zip([0.2, 0.2, 0.5, 0.8, 0.8], [0.2, 0.8, 0.5, 0.2, 0.8]): # for (x, y) in zip([0.1, 0.1, 0.5, 0.9, 0.9], [0.1, 0.9, 0.5, 0.1, 0.9]):
            self.show_point(x * SCREEN_X, y * SCREEN_Y)

            time.sleep(0.7)
            if calibration.collect_data(x, y) != tr.CALIBRATION_STATUS_SUCCESS:
                # Try again if it didn't go well the first time.
                calibration.collect_data(x, y)
            time.sleep(0.3)

        try:
            self.cali_result = calibration.compute_and_apply()
            logging.info("Compute and apply returned {0} and collected at {1} points."
                         .format(self.cali_result.status, len(self.cali_result.calibration_points)))

        except ValueError:
            logging.error("Calibration failed")
        
        calibration.leave_calibration_mode()
        self.finish_cali = True

    def on_press_cont(self, event):
        if self.finish_cali:
            self.cali_thread.join()

            CaliResultFrame(self.cali_result)
            self.Hide()

class CaliPreFrame(wx.Frame):
    def __init__(self):
        super(CaliPreFrame, self).__init__(parent=None, title='Calibration Preperation Page')

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        instruction_text = wx.StaticText(panel, wx.ID_ANY, "Click start to start calibration\n"
                                                           "Focus your gaze on the red dot until it disappear\n"
                                                           "Total 5 dots will show up\n",
                                     wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTRE)
        start_btn = wx.Button(panel, label='Start')
        skip_btn = wx.Button(panel, label='Skip')
        back_btn = wx.Button(panel, label="Back")

        sizer.AddStretchSpacer()
        sizer.Add(instruction_text, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(start_btn, 0, wx.CENTER)
        sizer.Add(skip_btn, 0, wx.CENTER)
        sizer.Add(back_btn, 0, wx.CENTER)
        sizer.AddStretchSpacer()
        panel.SetSizer(sizer)

        start_btn.Bind(wx.EVT_BUTTON, self.on_press_start)
        skip_btn.Bind(wx.EVT_BUTTON, self.on_press_skip)
        back_btn.Bind(wx.EVT_BUTTON, self.on_press_back)

        self.Show()

    def on_press_start(self, event):
        CaliFrame()
        self.Hide()

    def on_press_skip(self, event):
        DisplayFrame()
        self.Hide()

    def on_press_back(self, event):
        SetupFrame()
        self.Hide()

class SetupFrame(wx.Frame):
    def __init__(self):
        super(SetupFrame, self).__init__(parent=None, title='Set Up Page')

        self.panel = TrackerPanel(self)
        self.find_thread = threading.Thread(target=self.find_eyetracker, args=())
        self.run_find_thread = True
        #continue button
        cont_btn = wx.Button(self.panel, label='Continue')
        self.panel.sizer.Add(cont_btn, 0, wx.ALL | wx.CENTER, 5)
        cont_btn.Bind(wx.EVT_BUTTON, self.on_press_cont)
        # back button
        back_btn = wx.Button(self.panel, label='Back')
        self.panel.sizer.Add(back_btn, 0, wx.ALL | wx.CENTER, 5)
        back_btn.Bind(wx.EVT_BUTTON, self.on_press_back)

        self.Show()
        self.find_thread.start()

    def on_press_cont(self, event):
        self.run_find_thread = False
        self.find_thread.join()

        CaliPreFrame()
        self.Hide()

    def on_press_back(self, event):
        self.run_find_thread = False
        self.find_thread.join()

        StartFrame()
        self.Hide()

    def find_eyetracker(self):
        global EYE_TRACKER

        while(self.run_find_thread):
            found_eyetrackers = tr.find_all_eyetrackers()
            if len(found_eyetrackers) > 0:
                self.panel.update_eyetracker(found_eyetrackers)
                EYE_TRACKER = found_eyetrackers[0]

            time.sleep(1)

        return

class TrackerPanel(wx.Panel):
    def __init__(self, parent):
        super(TrackerPanel, self).__init__(parent)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.row_obj_dict = {}

        self.list_ctrl = wx.ListCtrl(
            self, size=(-1, 100),
            style=wx.LC_REPORT | wx.BORDER_SUNKEN
        )
        self.list_ctrl.InsertColumn(0, 'Address', width=100)
        self.list_ctrl.InsertColumn(1, 'Model', width=100)
        self.list_ctrl.InsertColumn(2, 'Name', width=50)
        self.list_ctrl.InsertColumn(3, 'Serial number', width=200)
        # position
        self.sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(self.sizer)

    def update_eyetracker(self, eyetrackers):
        self.list_ctrl.ClearAll()

        self.list_ctrl.InsertColumn(0, 'Address', width=170)
        self.list_ctrl.InsertColumn(1, 'Model', width=120)
        self.list_ctrl.InsertColumn(2, 'Name', width=50)
        self.list_ctrl.InsertColumn(3, 'Serial number', width=200)

        index = 0
        for eyetracker in eyetrackers:
            self.list_ctrl.InsertItem(index, eyetracker.address)
            self.list_ctrl.SetItem(index, 1, eyetracker.model)
            self.list_ctrl.SetItem(index, 2, eyetracker.device_name)
            self.list_ctrl.SetItem(index, 3, eyetracker.serial_number)
            index += 1

            logging.debug("Find eye tracker: address=({address}) \t model=({model}) \t "
                  "device_name=({device_name}) \t serial_number=({serial_number})"
                  .format(address=eyetracker.address, model=eyetracker.model, device_name=eyetracker.device_name,
                          serial_number=eyetracker.serial_number)
                  )

class StartFrame(wx.Frame):
    def __init__(self):
        super(StartFrame, self).__init__(parent=None, title='Start Page')

        # init
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        start_btn = wx.Button(panel, label="Start")
        welcome_text = wx.StaticText(panel, wx.ID_ANY, "Welcome to Tobii Eye Tracker @ unimelb\n",
                                     wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTRE)
        # position
        sizer.AddStretchSpacer()
        sizer.Add(welcome_text, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(start_btn, 0, wx.CENTER)
        sizer.AddStretchSpacer()
        panel.SetSizer(sizer)
        # events
        start_btn.Bind(wx.EVT_BUTTON, self.on_press_start)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Show()

    def on_press_start(self, event):
        SetupFrame()
        self.Hide()

    def on_close(self, event):
        client.send(CLOSE_CODE.encode('ascii'))
        client.close()
        self.Destroy()


# Main code
logging.basicConfig(level=logging.DEBUG)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_addr = (HOST, PORT)

try:
    client.connect(server_addr)
    logging.info("Connect with server on %s port %s" % server_addr)

    app = wx.App()
    frame = StartFrame()
    app.MainLoop()

except (KeyboardInterrupt, SystemExit):
    print("[Info] Key board interrupt or system exit, terminate program")
    client.send(CLOSE_CODE.encode('ascii'))
    client.close()
except socket.error:
    logging.error("Socket error occurred")
except Exception as e:
    logging.error(e.__class__, "occurred.")
    client.send(CLOSE_CODE.encode('ascii'))
    client.close()
