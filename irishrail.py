#!/usr/bin/python3

import untangle
import os
import argparse
from datetime import datetime
from tkinter import *
from threading import Thread
from time import sleep
import logging

"""
Live Irish Rail Station Display
https://github.com/wolfospealain/irishrail
http://api.irishrail.ie/realtime/
"""


class IrishRailStations:
    url = "http://api.irishrail.ie/realtime/realtime.asmx/getAllStationsXML"

    def __init__(self):
        while True:
            try:
                xml = untangle.parse(self.url)
                break
            except Exception as error:
                logging.debug(error)
        self.index = {}
        self.codes = []
        for station in xml.ArrayOfObjStation.children:
            self.codes.append(station.StationCode.cdata.strip().upper())
            self.index.update({station.StationDesc.cdata.upper(): station.StationCode.cdata.upper()})

    def lookup(self, station):
        if station in self.codes:
            return station
        elif station in self.index.keys():
            return self.index[station]
        else:
            return None

    def list(self):
        text = ""
        for station in sorted(self.index.keys()):
            text += station + ": " + self.index[station] + "\n"
        return text


class IrishRailTrain:

    def __init__(self, code, due, origin, destination, origin_time, destination_time, expected, late, status,
                 last_location=""):
        self.code = code
        self.due = due
        self.origin = origin
        self.destination = destination
        self.origin_time = origin_time
        self.destination_time = destination_time
        self.expected = expected
        self.late = late
        self.status = status
        self.last_location = last_location

    def __lt__(self, other):
        return self.due < other.due


class IrishRailStationData:
    url = "http://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML_WithNumMins?StationCode={}&NumMins={}"

    def __init__(self, station="MLLOW", minutes=6):
        self.station = station
        self.minutes = minutes

    def update(self):
        try:
            xml = untangle.parse(self.url.format(self.station, self.minutes))
            self.arrivals = []
            self.departures = []
            self.updated = datetime.now()
            for entry in xml.ArrayOfObjStationData.children:
                self.station_name = entry.Stationfullname.cdata
                if entry.Stationfullname != entry.Origin:
                    train = IrishRailTrain(entry.Traincode.cdata.strip(), int(entry.Duein.cdata), entry.Origin.cdata,
                                           entry.Destination.cdata, entry.Origintime.cdata, entry.Destinationtime.cdata,
                                           entry.Exparrival.cdata, int(entry.Late.cdata), entry.Status.cdata,
                                           entry.Lastlocation.cdata)
                    self.arrivals.append(train)
                else:
                    train = IrishRailTrain(entry.Traincode.cdata.strip(), int(entry.Duein.cdata), entry.Origin.cdata,
                                           entry.Destination.cdata, entry.Origintime.cdata, entry.Destinationtime.cdata,
                                           entry.Expdepart.cdata, int(entry.Late.cdata), entry.Status.cdata)
                    self.departures.append(train)
        except Exception as error:
            logging.debug(error)

    def late(self, minutes):
        if minutes < 0:
            return " (" + str(-minutes) + "m early) "
        elif minutes > 0:
            return " (" + str(minutes) + "m late) "
        else:
            return " "

    def arrivals_board(self):
        output = "LIVE STATION INFORMATION: " + self.station_name
        output += "\nUpdated: " + str(self.updated)[:16]
        output += "\n\nARRIVALS\n"
        for train in sorted(self.arrivals):
            output += "\n" + str(train.due) + "m\t" + train.origin + " to " + train.destination + " " + train.code + " " + train.origin_time + "-" + train.destination_time + " " + "\n\tDue " + train.expected + self.late(train.late) + (train.status if train.status != "No Information" else " ") + ("\n\t" + train.last_location if train.last_location.strip() != "" else "") + "\n"
        return output

    def departures_board(self):
        output = "LIVE STATION INFORMATION: " + self.station_name
        output += "\nUpdated: " + str(self.updated)[:16]
        output += "\n\nDEPARTURES\n"
        for train in sorted(self.departures):
            output += "\n" + str(train.due) + "m\t" + train.origin + " to " + train.destination + " " + train.code + " " + train.origin_time + "-" + train.destination_time + " " + "\n\tDeparts " + train.expected + self.late(train.late) + (train.status if train.status != "No Information" else " ") + "\n"
        return output

    def text(self):
        output = "LIVE STATION INFORMATION: " + self.station_name
        output += "\n\nARRIVALS\n"
        for train in sorted(self.arrivals):
            output += "\n" + str(
                train.due) + "m\t" + train.origin + " to " + train.destination + " " + train.code + " (" + train.origin_time.replace(
                ":", "") + "-" + train.destination_time.replace(":",
                                                                "") + ") " + "Due " + train.expected + self.late(train.late) + (
                          train.status if train.status != "No Information" else " ") + " " + (
                          train.last_location if train.last_location.strip() != "" else "")
        output += "\n\nDEPARTURES\n"
        for train in sorted(self.departures):
            output += "\n" + str(
                train.due) + "m\t" + train.origin + " to " + train.destination + " " + train.code + " " + train.origin_time + "-" + train.destination_time+ " " + "Departs " + train.expected + self.late(train.late) + (
                          train.status if train.status != "No Information" else " ")
        output += "\n\nUpdated: " + str(self.updated)[:16]
        return output


class GUI:

    def __init__(self, screen, data_link, speed=60000, pages="both", text_colour="orange", background_colour="black",
                 font="Courier New", font_size=28):
        self.data_link = data_link
        self.text_colour = text_colour
        self.background_colour = background_colour
        self.font = font
        self.font_size = font_size
        self.pages = pages
        self.screen = screen
        self.screen.title("Irish Rail Live")
        self.screen.configure(background=self.background_colour)
        self.screen.resizable(width=YES, height=YES)
        self.screen.attributes("-fullscreen", True)
        self.screen.bind("<F11>", self.toggle_fullscreen)
        self.screen.bind("<Escape>", self.end_fullscreen)
        self.text = Text(self.screen, font=(self.font, self.font_size, "bold"), bg=self.background_colour,
                         fg=self.text_colour, border=0, relief=FLAT,
                         highlightbackground="Black")
        self.text.pack(expand=True, fill='both', padx=50, pady=50)
        self.screen.after(0, self.download_update, speed)
        self.screen.after(0, self.write_page, speed, pages)
        self.screen.after(0, self.flash, "cursor", self.text_colour, self.background_colour)

    def toggle_fullscreen(self, event=None):
        self.screen.attributes("-fullscreen", not self.screen.attributes("-fullscreen"))

    def end_fullscreen(self, event=None):
        self.screen.attributes("-fullscreen", False)

    def flash(self, tag, on, off):
        colour = self.text.tag_cget(tag, "background")
        self.text.tag_configure(tag, background=on if colour == off else off)
        self.screen.after(500, self.flash, tag, on, off)

    def download_update(self, delay):
        update = Thread(target=self.data_link.update())
        update.start()
        self.screen.after(delay, self.download_update, delay)

    def write_page(self, delay, page):
        if page == "both":
            delay = int(delay / 2)
            page = "arrivals"
        if page == "arrivals":
            text = self.data_link.arrivals_board()
            if self.pages == "both":
                page = "departures"
        else:
            text = self.data_link.departures_board()
            if self.pages == "both":
                page = "arrivals"
        self.text.delete("1.0", END)
        self.text.insert(INSERT, " ", "cursor")
        self.text.mark_set("insert", "1.0")
        character_speed = 10
        typing_delay = 0
        for position in range(0, len(text)):
            typing = text[position]
            update_text = lambda typing=typing: self.text.insert(INSERT, typing)
            self.screen.after(typing_delay, update_text)
            typing_delay += character_speed
        self.screen.after(delay, self.write_page, delay, page)


def parse_command_line(version):
    description = "%(prog)s version " + version + ". " \
                  + "Live Irish Rail Station Display. https://github.com/wolfospealain/irishrail"
    parser = argparse.ArgumentParser(description=description, epilog="ESC to leave fullscreen. F11 to toggle.")
    parser.add_argument("-l", "--list", help="list station names and codes", action="store_true",
                        dest="list", default=False)
    parser.add_argument("-m", "--minutes", help="schedule lookahead in minutes (default: 60)", action="store",
                        dest="minutes", default=60)
    parser.add_argument("-s", "--speed", help="update speed in milliseconds (default: 60000)", action="store",
                        dest="speed", default=60000)
    parser.add_argument("-p", "--pages", help="pages to display: arrivals, departures, both (default)", action="store",
                        dest="pages", default="both")
    parser.add_argument("-t", "--text", help="text output only", action="store_true",
                        dest="text", default=False)
    parser.add_argument("station", help="station name or code", nargs="?")
    args = parser.parse_args()
    return args


def main():
    version = "18.08"
    icon = "/usr/share/icons/gnome/256x256/apps/utilities-terminal.png"
    args = parse_command_line(version)
    print("\nConnecting ...")
    stations = IrishRailStations()
    if args.list or not args.station or not stations.lookup(args.station.upper()):
        print("\n" + stations.list())
    else:
        data_link = IrishRailStationData(stations.lookup(args.station.upper()), args.minutes)
        if not args.text:
            screen = Tk(className="Display")
            screen.wm_iconphoto(True, PhotoImage(file=icon))
            app = GUI(screen, data_link, args.speed, args.pages)
            screen.mainloop()
        else:
            while True:
                data_link.update()
                os.system('clear')
                print("\n" + data_link.text())
                sleep(60)


if __name__ == '__main__':
    main()
