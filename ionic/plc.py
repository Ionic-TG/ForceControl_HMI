from pylogix import PLC
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from time import strftime


class MachinePLC:
    def __init__(self, ip_address=None):
        if ip_address is None:
            self.ip_address = '192.168.1.3'
        else:
            self.ip_address = ip_address

        # Instatiate the PLC connection
        self.plc = PLC()
        self.plc.IPAddress = self.ip_address

        self.current_position = 0.0
        self.robot_requested_position = 0.0
        self.requested_position = 0.0
        self.command_pos = 0.0
        self.robot_request_bit = False
        self.motion_complete = False
        self.manual_run = False
        self.home_bit = False

        # Heartbeat flags
        self.heartbeat_seconds = 0
        self.connection_ok = False

        # Start process
        # self.run()

    def heartbeat(self):
        """
        Reads the PLC wallclock time and reports it back to the PLC.
        :return:
        """
        # Get heartbeat signal from PLC
        ret = self.plc.Read('Wall_Clock_System_Time.Sec')
        if ret.Status == 'Success':
            self.heartbeat_seconds = ret.Value
        # print(self.heartbeat_seconds, self.stn1.nest_number)
        # Push heartbeat signal to PLC
        self.plc.Write('Z2_Dial_Vision.Heartbeat_From_Server', self.heartbeat_seconds)

        # E/IP connection status
        self.connection_ok = self.plc.SocketConnected

    def write_tags(self):
        """
        Writes tags to PLC.
        :return:
        """
        try:
            self.plc.Write('CommandPos', self.command_pos)
            self.plc.Write('test.0', self.manual_run)
            self.plc.Write('test.2', self.home_bit)

            self.home_bit = False

        except Exception as e:
            print(e)
            print('RuntimeError: Error writing to plc')

    def read_tags(self):
        """
        Reads tags from PLC
        :return:
        """
        try:
            self.robot_requested_position = self.plc.Read('RobotRequestedPosition').Value
            self.current_position = self.plc.Read('Positioner.CurrentPosition').Value
            self.requested_position = self.plc.Read('RequestedPosition').Value
            self.robot_request_bit = self.plc.Read('IRC5:I.Data[0].0').Value
            self.motion_complete = self.plc.Read('PositionerMotionOk').Value

        except:
            print('RuntimeError: Error reading from plc')
            pass

    def async_read_write(self):
        """
        Read and write tags sequentially.
        :return:
        """
        self.read_tags()
        self.write_tags()

    def run(self):
        """
        Run PLC communications main loop using multithreading.
        :return:
        """

        self.heartbeat()

        # Only run loop if PLC is connected
        if self.plc.SocketConnected:

            # Open the threadpool executor
            with ThreadPoolExecutor() as executor:
                rw = executor.submit(self.async_read_write)

                # Wait for threads to finish
                rw.result()

        else:
            print(f'No PLC Found at {self.ip_address} ... Retrying in 250 ms')
