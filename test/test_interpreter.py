import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from src.interpreter import Interpreter, AttoMissingMainError, AttoRuntimeError

TEST_DIR = Path(__file__).absolute().parent
TEST_DATA_DIR = TEST_DIR.parent / "test_data"


class TestInterpreter(unittest.TestCase):
    """Tests that interpreter works"""

    def setUp(self):
        Interpreter._corelib_funcs = None
        Interpreter._corelib_code = None

    def test_init_no_corelib(self):
        interp = Interpreter(False)
        self.assertFalse(interp.use_corelib)
        self.assertIsNone(Interpreter._corelib_funcs)
        self.assertIsNone(Interpreter._corelib_code)

    def test_hello_world_no_core(self):
        interp = Interpreter(False)
        f = StringIO()
        with redirect_stdout(f):
            interp.exec(
                """
                fn main is
                    __print "Hello world"
            """
            )
        self.assertEqual(f.getvalue(), "Hello world\n")

    def test_init(self):
        interp = Interpreter()
        self.assertTrue(interp.use_corelib)
        self.assertIsNotNone(Interpreter._corelib_funcs)

    def test_hello_world(self):
        interp = Interpreter()
        f = StringIO()
        with redirect_stdout(f):
            interp.exec(
                """
                fn main is
                    print "Hello world"
            """
            )
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
            interp.exec_file(TEST_DATA_DIR / "factorial_testcode.at")

        self.assertEqual(
            f.getvalue(),
            "\n".join(
                [
                    "fact(0.0) = 1.0",
                    "fact(1.0) = 1.0",
                    "fact(2.0) = 2.0",
                    "fact(3.0) = 6.0",
                    "fact(4.0) = 24.0",
                    "fact(5.0) = 120.0",
                    "fact(6.0) = 720.0",
                    "",
                ]
            ),
        )


class TestLanguagePrimitives(unittest.TestCase):
    """Tests that the build in language primitives works as expected"""

    def run_code(self, source):
        interp = Interpreter()
        f = StringIO()
        with redirect_stdout(f):
            interp.exec(source)

        return f.getvalue()

    def test_number(self):
        res = self.run_code("fn main is print 123")
        self.assertEqual(res, "123.0\n")

    def test_string(self):
        res = self.run_code("fn main is print \"'str'\"")
        self.assertEqual(res, "'str'\n")

    def test_true(self):
        res = self.run_code("fn main is print true")
        self.assertEqual(res, "true\n")

    def test_false(self):
        res = self.run_code("fn main is print false")
        self.assertEqual(res, "false\n")

    def test_print(self):
        res = self.run_code("fn main is print null")
        self.assertEqual(res, "null\n")

    def test_ident(self):
        res = self.run_code(
            """
            fn ident_test x is
                print x

            fn main is
                ident_test 34
        """
        )
        self.assertEqual(res, "34.0\n")

    def test_if_eq_first(self):
        res = self.run_code(
            """
            fn main is
                print if = 1 1
                    "equal"
                    "not equal"
        """
        )
        self.assertEqual(res, "equal\n")

    def test_if_eq_second(self):
        res = self.run_code(
            """
            fn main is
                print if = 1 2
                    "equal"
                    "not equal"
        """
        )
        self.assertEqual(res, "not equal\n"),

    def test_if_lt_first(self):
        res = self.run_code(
            """
            fn main is
                print if < 1 2
                    "equal"
                    "not equal"
        """
        )
        self.assertEqual(res, "equal\n")

    def test_if_lt_second(self):
        res = self.run_code(
            """
            fn main is
                print if < 2 1
                    "equal"
                    "not equal"
        """
        )
        self.assertEqual(res, "not equal\n")

    def test_add(self):
        res = self.run_code("fn main is print + 1 2")
        self.assertEqual(res, "3.0\n")

    def test_neg(self):
        res = self.run_code("fn main is print - 1 2")
        self.assertEqual(res, "-1.0\n")

    def test_mul(self):
        res = self.run_code("fn main is print * 4 3")
        self.assertEqual(res, "12.0\n")

    def test_div(self):
        res = self.run_code("fn main is print / 12 3")
        self.assertEqual(res, "4.0\n")

    def test_rem(self):
        res = self.run_code("fn main is print % 12 5")
        self.assertEqual(res, "2.0\n")

    def test_str(self):
        res = self.run_code("fn main is print str 12")
        self.assertEqual(res, "12.0\n")

    def test_litr(self):
        res = self.run_code('fn main is print + litr "10" 5')
        self.assertEqual(res, "15.0\n")

    def test_words(self):
        res = self.run_code('fn main is print words "this is a sentence."')
        self.assertEqual(res, "['this', 'is', 'a', 'sentence.']\n")

    def test_pair(self):
        res = self.run_code("fn main is print pair 1 2")
        self.assertEqual(res, "[1.0, 2.0]\n")

    def test_head_list(self):
        res = self.run_code("fn main is print head pair 1 pair 2 3")
        self.assertEqual(res, "1.0\n")

    def test_head_str(self):
        res = self.run_code('fn main is print head "string"')
        self.assertEqual(res, "s\n")

    def test_tail_list(self):
        res = self.run_code("fn main is print tail fuse 1 pair 2 3")
        self.assertEqual(res, "[2.0, 3.0]\n")

    def test_tail_str(self):
        res = self.run_code('fn main is print tail "string"')
        self.assertEqual(res, "tring\n")

    def test_fuse_lists(self):
        res = self.run_code("fn main is print fuse pair 1 2 pair 3 4")
        self.assertEqual(res, "[1.0, 2.0, 3.0, 4.0]\n")

    def test_fuse_left_list(self):
        res = self.run_code("fn main is print fuse pair 1 2 3")
        self.assertEqual(res, "[1.0, 2.0, 3.0]\n")

    def test_fuse_right_list(self):
        res = self.run_code("fn main is print fuse 1 pair 2 3")
        self.assertEqual(res, "[1.0, 2.0, 3.0]\n")

    def test_fuse_numbers(self):
        res = self.run_code("fn main is print fuse 1 2")
        self.assertEqual(res, "[1.0, 2.0]\n")

    def test_fuse_strings(self):
        res = self.run_code('fn main is print fuse "one" "two"')
        self.assertEqual(res, "['one', 'two']\n")


class TestError(unittest.TestCase):
    """Test that errors are raised as they should"""

    def test_missing_main(self):
        src = """fn test is print \"hej\""""
        interp = Interpreter()
        with self.assertRaisesRegex(AttoMissingMainError, "main .* not found"):
            interp.exec(src)

    def test_runtime_error(self):
        src = """
        fn one is print litr "hej"
        fn main is one
        """
        interp = Interpreter()
        with self.assertRaisesRegex(AttoRuntimeError, "Failed .* convert"):
            interp.exec(src)

    def test_runtime_treaceback(self):
        src = """
        fn one is print litr "hej"
        fn main is one
        """
        interp = Interpreter()
        err = None
        try:
            interp.exec(src)
        except AttoRuntimeError as e:
            err = e
        else:
            raise Exception("Expected a AttoRuntimeError")
        tb = err.traceback()
        self.assertEqual(len(tb), 3)
        self.assertRegex(tb[0], "__litr .* litr .* core.at")
        self.assertRegex(tb[1], "litr .* one .* :2")
        self.assertRegex(tb[2], "one .* main .* :3")
