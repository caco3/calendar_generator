"""Script to generate A4 calendars"""
import calendar
import datetime
from collections import namedtuple
from calendar import month_name, day_name
import logging
from dateutil.easter import *
import PyPDF2

import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
from matplotlib.patches import Rectangle

logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

calendar.setfirstweekday(0) # Monday is 1st day in Europa

class DayNotInMonthError(ValueError):
    pass

class MplCalendar(object):
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.cal = calendar.monthcalendar(year, month)
        # A month of events are stored as a list of lists of list.
        # Nesting, from outer to inner, Week, Day, Event_str
        # Save the events data in the same format
        self.events = [[[] for day in week] for week in self.cal]
        self.colors = [[None for day in week] for week in self.cal]

    def _monthday_to_index(self, day):
        '''The 2-d index of the day in the list of lists.

        If the day is not in the month raise a DayNotInMonthError,
        which is a subclass of ValueError.

        '''
        for week_n, week in enumerate(self.cal):
            try:
                i = week.index(day)
                return week_n, i
            except ValueError:
                pass
         # couldn't find the day
        raise DayNotInMonthError("There aren't {} days in the month".format(day))

    def add_event(self, day, event_str):
        'Add an event string for the specified day'
        week, w_day = self._monthday_to_index(day)
        self.events[week][w_day].append(event_str)

    def color_day(self, day, color):
        'Set square for specified day to specified color'
        week, w_day = self._monthday_to_index(day)
        self.colors[week][w_day] = color
        

    def _render(self, **kwargs):
        'create the calendar figure'
        cm = 1 / 2.54  # centimeters in inches
        plot_defaults = dict(
            sharex=True,
            sharey=True,
            figsize=(21 * cm, 29.7 * cm),
            dpi=600,
        )


        plot_defaults.update(kwargs)
        self.f, self.axs = plt.subplots(
            len(self.cal), 7,
            **plot_defaults
        )

        for week, ax_row in enumerate(self.axs):
            for week_day, ax in enumerate(ax_row):
                ax.set_xticks([])
                ax.set_yticks([])
                if self.colors[week][week_day] is not None:
                    ax.set_facecolor(self.colors[week][week_day])
                if self.cal[week][week_day] != 0:
                    ax.text(.08, .92,
                            str(self.cal[week][week_day]),
                            verticalalignment='top',
                            horizontalalignment='left')
                else: # Square is not part of this month
                    ax.set_facecolor("lightgray")
                contents = "\n".join(self.events[week][week_day])
                ax.text(.08, .7, contents,
                        verticalalignment='top',
                        horizontalalignment='left',
                        fontsize=9)

                if week_day == 6:
                    ax.add_patch(Rectangle((1, -0.05), 0.05, 1,
                                              edgecolor='gray', facecolor='gray', lw=1, clip_on=False))
                if week == len(self.axs) - 1:
                    ax.add_patch(Rectangle((0.05, -0.05), 1, 0.05,
                                                  edgecolor='gray', facecolor='gray', lw=1, clip_on=False))

        # use the titles of the first row as the weekdays
        for n, day in enumerate(day_name):
            self.axs[0][n].text(0.5, 1.1, day, ha="center", va="bottom", size=12, color="white",
                path_effects=[patheffects.withStroke(linewidth=4, foreground='black', capstyle="round")])

        # Place subplots in a close grid
        self.f.subplots_adjust(hspace=0)
        self.f.subplots_adjust(wspace=0)
        self.f.subplots_adjust(top=0.45)
        self.f.suptitle(month_name[self.month] + ' ' + str(self.year),
                   fontsize=40, color="white", fontweight='bold',
                   path_effects=[patheffects.withStroke(linewidth=8, foreground='black', capstyle="round")])

    def show(self, **kwargs):
        'display the calendar'
        self._render(**kwargs)

        plt.show()


    def save(self, filename, **kwargs):
        'save the calendar to the specified image file.'
        self._render(**kwargs)

        # Photo box
        h = 6
        if len(self.axs) == 4:  # February fits on only 4 rows
            h -= 1.2
        if len(self.axs) == 6:  # February fits on only 4 rows
            h += 1.2

        plt.gca().add_patch(Rectangle((-5.95, h - 0.25), 7, h + 0.1,
                edgecolor='gray', facecolor='gray', lw=1, clip_on=False))
        plt.gca().add_patch(Rectangle((-6, h - 0.2), 7, h + 0.1,
                edgecolor='black', facecolor='white', lw=1, clip_on=False))

        plt.savefig(filename, format='pdf', bbox_inches='tight', pad_inches=.5)


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True, help="Year use")
    parser.add_argument("--locale", type=str, required=False, default="de_DE", help="Locale to use, eg. de_DE")

    args = parser.parse_args()
    year = args.year

    # logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    import locale

    locale.setlocale(locale.LC_ALL, args.locale + ".UTF-8")
    logging.info(f"Locale is: {locale.getlocale()}")

    Event = namedtuple('Event', ['name', 'month', 'day', 'color'])

    """Events which are on the same day each year"""
    fix_events = [
        # Christian events (the fixed ones)
        Event("Berchtoldtag", 1, 2, "lightcoral"),
        Event("Drei Könige", 1, 6, "white"),
        Event("Heiligabend", 12, 24, "white"),
        Event("Weihnachten", 12, 25, "lightcoral"),
        Event("Stephanstag", 12,26 , "lightcoral"),

        # Secular events
        Event("Neujahrstag", 1, 1, "lightcoral"),
        Event("Silvester", 12, 31, "lightcoral"),

        # Swiss events
        Event("Tag der\nArbeit", 5, 1, "lightcoral"),
        Event("Bundes-\nfeiertag", 8, 1, "lightcoral")
    ]

    """Events which are on a different date each year"""
    easter_sunday = easter(year)  # YYYY-MM-DD, eg. 2025-04-20
    easter_monday = easter_sunday + datetime.timedelta(days=1)
    holy_thuersday = easter_sunday - datetime.timedelta(days=3)
    good_friday = easter_sunday - datetime.timedelta(days=2)

    ascension = easter_sunday + datetime.timedelta(days=39)
    pentecost = ascension + datetime.timedelta(days=10)
    whit_monday = ascension + datetime.timedelta(days=11)

    flexible_events = [
        Event("Grün-\ndonnerstag", holy_thuersday.month, holy_thuersday.day, "white"),
        Event("Karfreitag",good_friday.month,good_friday.day, "lightcoral"),
        Event("Oster-\nsonntag", easter_sunday.month, easter_sunday.day, "lightcoral"),
        Event("Ostermontag", easter_monday.month, easter_monday.day, "lightcoral"),

        Event("Auffahrt", ascension.month, ascension.day, "lightcoral"),
        Event("Pfingsten", pentecost.month, pentecost.day, "lightcoral"),
        Event("Pfingst-\nmontag", whit_monday.month, whit_monday.day, "lightcoral")
    ]

    pdfWriter = PyPDF2.PdfWriter()
    for month in range(1, 13):
        logging.info(f"Generating page for '{month_name[month]} {year}'...")
        month_page = MplCalendar(year, month)

        for day in range(32):
            try:
                weekday = datetime.datetime(year, month, day).weekday()
                if weekday >= 5:  # Highlight saturday and sunday
                    month_page.color_day(day, "#ffffb4")
            except:  # day is beyond days in month
                pass

        # Mark events
        for e in fix_events:
            if month == e.month:
                month_page.add_event(e.day, e.name)
                month_page.color_day(e.day, e.color)

        for e in flexible_events:
            if month == e.month:
                month_page.add_event(e.day, e.name)
                month_page.color_day(e.day, e.color)

        month_page.save(f"{month:02}.pdf")

        filename = f"{month:02}.pdf"
        pdfFileObj = open(filename, 'rb') # Opens each of the file paths in filename variable.
        pdfReader = PyPDF2.PdfReader(pdfFileObj) # Reads each of the files in the new varaible you've created above and stores into memory.
        pageObj = pdfReader.pages[0] # Reads only those that are in the variable.
        pdfWriter.add_page(pageObj) # Adds each of the PDFs it's read to a new page.

        os.remove(filename)

    logging.info("Merging months...")
    pdfOutput = open(f"{year}.pdf", "wb")
    pdfWriter.write(pdfOutput)
    pdfOutput.close()

    logging.info(f"Enjoy your calendar: {year}.pdf")