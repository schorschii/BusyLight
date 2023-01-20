# Office BusyLight

This script displays a "Please do not disturb" text on a EPSON DM-D110 USB display when your microphone is in use and another defined text if not. In addition to that, it can display a text when your screen is locked (e.g. "I'll be back"; currently implemented for the Cinnamon desktop).

![EPSON DM-D110 BusyLight](busylight.gif)

## Hardware Setup
```
/sbin/modprobe ftdi_sio
echo "1208 0780" > /sys/bus/usb-serial/drivers/ftdi_sio/new_id

#/etc/udev/rules.d/50-dmd110.rules:
ATTR{idProduct}=="0780", ATTR{idVendor}=="1208", RUN+="/sbin/modprobe -q ftdi_sio" RUN+="/bin/sh -c 'echo 1208 0780 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id'",  OWNER="root", MODE="0666"
```

Replace the vendor/device id for your display.

## Software Setup
1. Create a config file `~/.config/busylight.json` with the settings and texts you want to display:
   ```
    {
      "DisplaySerialPort": "/dev/ttyUSB0",
      "SoundcardName": "Generic",
      "MessageBusy1": "   !!! MEETING !!!",
      "MessageBusy2": "Please do not disturb.",
      "MessageNormal1": "Welcome!",
      "MessageNormal2": "Please come in.",
      "MessageAbsent1": "I'll be back...",
      "MessageAbsent2": "(sooner or later)"
    }
   ```
   The correct soundcard name can be found by executing `cat /proc/asound/cards` (the name in square brackets).
2. Let the script run in background.
