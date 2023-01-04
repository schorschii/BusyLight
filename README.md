# Office BusyLight

This script displays a "Please do not disturb" text on a EPSON DM-D110 USB display when your microphone is in use.

## Hardware Setup
```
/sbin/modprobe ftdi_sio
echo "1208 0780" > /sys/bus/usb-serial/drivers/ftdi_sio/new_id

#/etc/udev/rules.d/50-dmd110.rules:
ATTR{idProduct}=="0780", ATTR{idVendor}=="1208", RUN+="/sbin/modprobe -q ftdi_sio" RUN+="/bin/sh -c 'echo 1208 0780 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id'",  OWNER="root", MODE="0666"
```

Replace the vendor/device id for your display.

## Software Setup
1. Find the correct device for `soundcardDevice = '/proc/asound/card1/pcm0c/sub0/status'` and enter it in the script.
2. Let the script run in background.
