import itertools
import threading
import time


def grouper(iterable, n, fillvalue=None):
    """
    delar upp en iterable i n delar. Bra att ha vid frågor mot api när antalet tillåtna
    element är begränsat
    källa:
    https://stackoverflow.com/questions/434287/what-is-the-most-pythonic-way-to-iterate-over-a-list-in-chunks
    """

    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue='')


def weekdays_in_month(year: int, month: int):
    """[summary]
	
	:param year: [description]
	:type year: int
	:param month: [description]
	:type month: int
	"""
    try:
        import pendulum
    except ImportError as exc:
        print(exc)
        print(f"The module {exc.name} is required!")
    start = pendulum.datetime(year=year, month=month, day=1)
    end = start._end_of_month()
    delta = start - end
    noWeekdays = 0
    for d in delta:
        if d.day_of_week < 5:
            noWeekdays += 1
    year = str(year)
    month = str(month)
    if int(month) < 10:
        month = '0' + month
    period = year + month

    return period, noWeekdays


class Spinner():
    """
    original code is copied from: https://gist.github.com/cevaris/87afc14c7a4e5e44ad21
    some revision is done to make it work with python3
    """

    spinner_cycle = itertools.cycle(['-', '/', '|', '\\'])

    def __init__(self):
        self.stop_running = threading.Event()
        self.spin_thread = threading.Thread(target=self.init_spin)

    def start(self):
        self.spin_thread.start()

    def stop(self):
        self.stop_running.set()
        self.spin_thread.join()

    def init_spin(self):
        while not self.stop_running.is_set():
            print(self.spinner_cycle.__next__(), end='\r')
            time.sleep(0.25)
