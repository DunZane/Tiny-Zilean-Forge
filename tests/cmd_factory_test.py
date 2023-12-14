import unittest

from core.cpu.cmd_factory import CpuCmdGenerator
from core.mem.cmd_factory import MemCmdGenerator
from core.processes.cmd_factory import ProcessesGenerator


class Test_CUP_Shell(unittest.TestCase):
    # 测试
    # drift_parameters = {'type':"Blip",'duration':3,'shape':None}
    # drift_parameters = {'type': "Recurrent", "duration": 30, 'shape': None}
    # drift_parameters = {'type': 'Gradual', 'duration': None, 'shape': [[1, 2], [2, 1]]}
    # drift_parameters = {'type': "Sudden", "duration": -1, 'shape': None}
    # drift_parameters = {'type': "Incremental", "duration": -1, "shape": [3, 10]}

    def test_gradual(self):
        sg = CpuCmdGenerator()
        sc = sg.generate_script({"type": "Gradual", "duration": -1, "shape": [[1, 2, 3, 4], [4, 3, 2, 1]]})
        print(sc)

    def test_sudden(self):
        sg = CpuCmdGenerator()
        sc = sg.generate_script({"type": "Sudden", "duration": -1, "shape": None})
        print(sc)

    def test_blip(self):
        sg = CpuCmdGenerator()
        sc = sg.generate_script({"type": "Blip", "duration": 7, "shape": None})
        print(sc)

    def test_recurrent(self):
        sg = CpuCmdGenerator()
        sc = sg.generate_script({"type": "Recurrent", "duration": 25, "shape": None})
        print(sc)

    def test_increment(self):
        sg = CpuCmdGenerator()
        sc = sg.generate_script({"type": "Incremental", "duration": 25, "shape": [3, 6]})
        print(sc)


class Test_MEM_Shell(unittest.TestCase):

    def test_sudden(self):
        sg = MemCmdGenerator()
        cmds = sg.generate_script({"type": "Sudden", "duration": -1, "shape": None})
        print(cmds)

    def test_blip(self):
        sg = MemCmdGenerator()
        cmds = sg.generate_script({"type": "Blip", "duration": 7, "shape": None})
        print(cmds)

    def test_recurrent(self):
        sg = MemCmdGenerator()
        cmds = sg.generate_script({"type": "Recurrent", "duration": 25, "shape": None})
        print(cmds)

    def test_increment(self):
        sg = MemCmdGenerator()
        cmds = sg.generate_script({"type": "Recurrent", "duration": 25, "shape": None})
        print(cmds)

    def test_gradual(self):
        sg = MemCmdGenerator()
        cmds = sg.generate_script({"type": "Gradual", "duration": -1, "shape": [[1, 2, 3, 4], [4, 3, 2, 1]]})
        print(cmds)


if __name__ == '__main__':
    unittest.main()
