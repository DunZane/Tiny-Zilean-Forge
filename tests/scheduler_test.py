import unittest

from core.scheduler import Scheduler


class Test_CPU(unittest.TestCase):

    def test_get_recurrent_cpu_utilization(self):
        s = Scheduler('cpu')
        time = s._get_end_time(30)
        print(time)

    def test_start_gradual(self):
        # drift_parameters = {'type': 'Gradual', 'duration': None, 'shape': [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]]}
        s = Scheduler('cpu')
        s.start()

    def test_start_Blip(self):
        # drift_parameters = {'type':"Blip",'duration':3,'shape':None}
        s = Scheduler('cpu')
        s.start()

    def test_start_recurrent(self):
        # drift_parameters = {'type':"Recurrent","duration":30,'shape':None}
        s = Scheduler('cpu')
        s.start()

    def test_start_sudden(self):
        # drift_parameters = {'type':"Sudden","duration":-1,'shape':None}
        s = Scheduler('cpu')
        s.start()

    def test_start_incremental(self):
        # drift_parameters = {'type':"Incremental","duration":-1,"shape":[3,10]}
        s = Scheduler('cpu')
        s.start()


class Test_MEM(unittest.TestCase):

    def test_start_recurrent(self):
        # drift_parameters = {'type':"Recurrent","duration":30,'shape':None,'mode': "transmitted"}
        s = Scheduler('cpu')
        s.start()

    def test_start_blip(self):
        s = Scheduler('cpu')
        s.start()

    def test_start_gradual(self):
        # drift_parameters = {'type': 'Gradual', 'duration': None, 'shape': [[1, 2], [2, 1]], 'mode': "transmitted"}
        s = Scheduler('cpu')
        s.start()

    # 还没有测试通过：调整时间
    def test_start_sudden(self):
        # drift_parameters = {'type': "Sudden", "duration": -1, 'shape': None}
        s = Scheduler('cpu')
        s.start()

    def test_start_incremental(self):
        s = Scheduler('cpu')
        s.start()

    def test_get_end_time(self):
        s = Scheduler('cpu')
        s._get_end_time(590)


if __name__ == '__main__':
    unittest.main()
