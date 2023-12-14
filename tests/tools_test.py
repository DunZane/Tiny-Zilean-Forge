import datetime
import unittest

from core.toolkit.pools import perform_insert
from core.toolkit.tools import get_available_processes_num, get_current_mem_percent


class Test_Tools(unittest.TestCase):
    def test_available_processes_num(self):
        num = get_available_processes_num()
        print(num)

    def test_current_mem_percent(self):
        per = get_current_mem_percent()
        print(per)


class Test_Pool(unittest.TestCase):

    def test_perform_insert(self):
        perform_insert(["Sudden", (datetime.datetime.now(), datetime.datetime.now())], "cpu")