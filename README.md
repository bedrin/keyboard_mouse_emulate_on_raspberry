# BLKB - linux bluetooth keyboard emulator

Emulate bluetooth keyboard on your Linux device - accepts bluetooth connection from another device (computer, phone, you name it) and sends predefined keys combination

Runs as a docker container - when connection is dropped, container is restarted and awaits for a new connection.

## Configuration

Clone this repo and make a few changes to `btk_server.py` file

1. Put your BT MAC address on line `MY_ADDRESS = "B8:27:EB:87:15:DC"` - use `hciconfig hci0 | awk '/BD Address: /{print $3}'` to find it out
2. Change the BT name on line `MY_DEV_NAME = "ThanhLe_Keyboard_Mouse"`
3. Change the keys you want to send in method `BTKbService.__init__`. Default implementation sends R each 10 seconds and Ctrl+R each 5 minutes
```
        # start infinite loop
        while True:
          for x in range(0,30):
              logging.info("sending R")
              self.send_string(0, "R")
              logging.info("sent R")
              time.sleep(10)
          logging.info("sending CTRL+R")
          self.send_string(0x01, "R")
          logging.info("sent CTRL+R")
          time.sleep(30)
```

## Build

```
docker build -t blkb:dev .
```

## Prerequisites to run

### Bluetooth pairing and trust

You need to pair and trust your linux device with target device first.

Easiest way to do it is using `bluetoothctl` tool - Google for it.

### setcap

Not 100% sure if following steps are required since container is running as privileged

```
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hciconfig`
```

## Running

```
docker run --name blkb  -v /var/run/dbus:/var/run/dbus --rm --network host --privileged blkb:dev
```

Of if you're using Docker Compose:

```
---
version: "2.1"
services:
  blkb:
    container_name: blkb
    network_mode: host
    image: blkb:dev
    restart: always
    volumes:
      - /var/run/dbus:/var/run/dbus
    privileged: true
```

## Disclaimer

Based on https://github.com/quangthanh010290/keyboard_mouse_emulate_on_raspberry