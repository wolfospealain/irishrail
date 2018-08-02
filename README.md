# IrishRail
Live Irish Rail Station Display

Written in Python, using the Irish Rail API http://api.irishrail.ie/realtime/, displays live station information.

```
usage: irishrail.py [-h] [-l] [-m MINUTES] [-s SPEED] [-p PAGES] [-t]
                    [station]

irishrail.py version 18.08. Live Irish Rail Station Display.
https://github.com/wolfospealain/irishrail

positional arguments:
  station               station name or code

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            list station names and codes
  -m MINUTES, --minutes MINUTES
                        schedule lookahead in minutes (default: 60)
  -s SPEED, --speed SPEED
                        update speed in milliseconds (default: 60000)
  -p PAGES, --pages PAGES
                        pages to display: arrivals, departures, both (default)
  -t, --text            text output only

ESC to leave fullscreen. F11 to toggle.
```
