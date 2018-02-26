"""
Example unit tests for simulation_tools package
"""
import unittest
import desc.simulation_tools

class simulation_toolsTestCase(unittest.TestCase):
    def setUp(self):
        self.message = 'Hello, world'

    def tearDown(self):
        pass

    def test_run(self):
        foo = desc.simulation_tools.simulation_tools(self.message)
        self.assertEqual(foo.run(), self.message)

    def test_failure(self):
        self.assertRaises(TypeError, desc.simulation_tools.simulation_tools)
        foo = desc.simulation_tools.simulation_tools(self.message)
        self.assertRaises(RuntimeError, foo.run, True)

if __name__ == '__main__':
    unittest.main()
