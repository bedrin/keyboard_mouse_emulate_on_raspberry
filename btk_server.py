#!/usr/bin/python3

from __future__ import absolute_import, print_function
from optparse import OptionParser, make_option
import os
import sys
import uuid
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import socket
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
import logging
from logging import debug, info, warning, error

import keymap

logging.basicConfig(level=logging.DEBUG)


class BTKbDevice():
    # change these constants
    MY_ADDRESS = "B8:27:EB:87:15:DC"
    MY_DEV_NAME = "Raspberry_Keyboard"

    errorCount = 0

    # define some constants
    P_CTRL = 17  # Service port - must match port configured in SDP record
    P_INTR = 19  # Service port - must match port configured in SDP record#Interrrupt port
    # dbus path of the bluez profile we will create
    # file path of the sdp record to load
    SDP_RECORD_PATH = sys.path[0] + "/sdp_record.xml"
    UUID = "00001124-0000-1000-8000-00805f9b34fb"

    def __init__(self):
        logging.info("2. Setting up BT device")
        self.init_bt_device()
        self.init_bluez_profile()
        self.set_bt_class()

    # configure the bluetooth hardware device
    def init_bt_device(self):
        logging.info("3. Configuring Device name " + BTKbDevice.MY_DEV_NAME)
        # set the device class to a keybord and set the name
        os.system("hciconfig hci0 up")
        os.system("hciconfig hci0 class 0x0025C0")
        os.system("hciconfig hci0 name " + BTKbDevice.MY_DEV_NAME)
        # make the device discoverable
        os.system("hciconfig hci0 piscan")

    def set_bt_class(self):
        logging.info("workaround. Setting bluetooth class again")
        os.system("hciconfig hci0 class 0x0025C0")

    # set up a bluez profile to advertise device capabilities from a loaded service record
    def init_bluez_profile(self):
        logging.info("4. Configuring Bluez Profile")
        # setup profile options
        service_record = self.read_sdp_service_record()
        opts = {
            "AutoConnect": True,
            "ServiceRecord": service_record
        }
        # retrieve a proxy for the bluez profile interface
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object(
            "org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")
        manager.RegisterProfile("/org/bluez/hci0", BTKbDevice.UUID, opts)
        logging.info("6. Profile registered ")
        os.system("hciconfig hci0 -a")

    # read and return an sdp record from a file
    def read_sdp_service_record(self):
        logging.info("5. Reading service record")
        try:
            fh = open(BTKbDevice.SDP_RECORD_PATH, "r")
        except:
            sys.exit("Could not open the sdp record. Exiting...")
        return fh.read()

    # listen for incoming client connections
    def listen(self):
        logging.info("\033[0;33m7. Waiting for connections\033[0m")
        self.scontrol = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)  # BluetoothSocket(L2CAP)
        self.sinterrupt = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)  # BluetoothSocket(L2CAP)
        self.scontrol.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sinterrupt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind these sockets to a port - port zero to select next available
        self.scontrol.bind((socket.BDADDR_ANY, self.P_CTRL))
        self.sinterrupt.bind((socket.BDADDR_ANY, self.P_INTR))

        # Start listening on the server sockets
        self.scontrol.listen(5)
        self.sinterrupt.listen(5)

        self.ccontrol, cinfo = self.scontrol.accept()
        print (
            "\033[0;32mGot a connection on the control channel from %s \033[0m" % cinfo[0])

        self.cinterrupt, cinfo = self.sinterrupt.accept()
        print (
            "\033[0;32mGot a connection on the interrupt channel from %s \033[0m" % cinfo[0])

    # send a string to the bluetooth host machine
    def send_string(self, message):
        global errorCount
        try:
            self.cinterrupt.send(bytes(message))
            errorCount = 0
        except OSError as err:
            error(err)
            errorCount += 1
            if errorCount > 50 :
                sys.exit()


class BTKbService(dbus.service.Object):

    def __init__(self):
        logging.info("1. Setting up service")
        # create and setup our device
        self.device = BTKbDevice()
        # start listening for connections
        self.device.listen()

        self.scancodes = {
            " ": "KEY_SPACE",
            "→": "KEY_RIGHT",
            "↵": "KEY_ENTER"
            }
        # the structure for a bt keyboard input report (size is 10 bytes)
        self.interimstate = [
            0xA1,  # this is an input report
            0x01,  # Usage report = Keyboard
            # Bit array for Modifier keys
            [0x01,  # Right GUI - Windows Key
                 0,  # Right ALT
                 0,  # Right Shift
                 0,  # Right Control
                 0,  # Left GUI
                 0,  # Left ALT
                 0,  # Left Shift
                 0],  # Left Control
            0x00,  # Vendor reserved
            0x00,  # rest is space for 6 keys
            0x00,
            0x00,
            0x00,
            0x00,
            0x00]

        # start infinite loop
        while True:
          for x in range(0,12):
              logging.info("sending ENTER (↵)")
              self.send_string(0, "↵")
              logging.info("sent ENTER (↵)")
              time.sleep(10)
        
          logging.info("sending RIGHT (→)")
          self.send_string(0, "→")
          logging.info("sent RIGHT (→)")
          time.sleep(1)
          logging.info("sending ENTER (↵)")
          self.send_string(0, "↵")
          logging.info("sent ENTER (↵)")
          time.sleep(10)

          logging.info("sending CTRL+R")
          self.send_string(0x01, "R")
          logging.info("sent CTRL+R")
          time.sleep(10)

    def send_key_state(self):
        """sends a single frame of the current key state to the emulator server"""
        bin_str = ""
        element = self.interimstate[2]
        for bit in element:
            bin_str += str(bit)
        self.send_keys(int(bin_str, 2), self.interimstate[4:10])

    def send_key_down(self, modifier, scancode):
        """sends a key down event to the server"""
        self.interimstate[2] = [modifier, 0, 0, 0, 0, 0, 0, 0]
        self.interimstate[4] = scancode
        self.send_key_state()

    def send_key_up(self):
        """sends a key up event to the server"""
        self.interimstate[2] = [0,0,0,0,0,0,0,0]
        self.interimstate[4] = 0
        self.send_key_state()

    def send_string(self, modifier, string_to_send):
        for c in string_to_send:
            cu = c.upper()
            if(cu in self.scancodes):
                scantablekey = self.scancodes[cu]
            else:
                scantablekey = "KEY_"+c.upper()
            logging.info(scantablekey)
            scancode = keymap.keytable[scantablekey]
            self.send_key_down(modifier, scancode)
            time.sleep(0.01)
            self.send_key_up()
            time.sleep(0.01)

    def send_keys(self, modifier_byte, keys):
        logging.info("Get send_keys request through dbus")
        logging.info("key msg: %s", keys)
        state = [ 0xA1, 1, 0, 0, 0, 0, 0, 0, 0, 0 ]
        state[2] = int(modifier_byte)
        count = 4
        for key_code in keys:
            if(count < 10):
                state[count] = int(key_code)
            count += 1
        self.device.send_string(state)

# main routine
if __name__ == "__main__":
    try:
        DBusGMainLoop(set_as_default=True)
        myservice = BTKbService()
        loop = GLib.MainLoop()
        loop.run()
    except KeyboardInterrupt:
        sys.exit()
