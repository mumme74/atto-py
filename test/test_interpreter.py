import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from src.interpreter import Interpreter

test_dir = Path(__file__).absolute().parent

class TestInterpreter(unittest.TestCase):
    def setUp(self):
        pass

    def test_init_no_corelib(self):
        interp = Interpreter(False)
        self.assertFalse(interp.use_corelib)
        self.assertIsNone(Interpreter._corelib_funcs)
        self.assertIsNone(Interpreter._corelib_code)

    def test_hello_world_no_core(self):
        interp = Interpreter(False)
        f = StringIO()
        with redirect_stdout(f):
            interp.exec("""
                fn main is
                    __print "Hello world"
            """)
        self.assertEqual(f.getvalue(), "Hello world\n")

    def test_init(self):
        interp = Interpreter()
        self.assertTrue(interp.use_corelib)
        self.assertIsNotNone(Interpreter._corelib_funcs)

    def test_hello_world(self):
        interp = Interpreter()
        f = StringIO()
        with redirect_stdout(f):
            interp.exec("""
                fn main is
                    print "Hello world"
            """)
        self.assertEqual(f.getvalue(), "Hello world\n")

    def test_count_300(self):
        code = """
            fn count_to n is
                if = n 0
                    print "Finished!"
                count_to - n 1

            fn main is
                count_to 300
        """
        interp = Interpreter()
        f = StringIO()
        with redirect_stdout(f):
            interp.exec(code)
        self.assertEqual(f.getvalue(), "Finished!\n")

    def test_exec_file(self):
        interp = Interpreter()
        f = StringIO()
        with redirect_stdout(f):
            interp.exec_file(test_dir / "factorial_testcode.at")

        self.assertEqual(f.getvalue(), '\n'.join(
                         ["fact(0.0) = 1.0",
                          "fact(1.0) = 1.0",
                          "fact(2.0) = 2.0",
                          "fact(3.0) = 6.0",
                          "fact(4.0) = 24.0",
                          "fact(5.0) = 120.0",
                          "fact(6.0) = 720.0",
                          ""]))