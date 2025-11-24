import unittest
from pathlib import Path

from src.lexer import Token, TokenTypes, AttoSyntaxError
from src.parser import Parser, ASTnode, Func
from mocks import MockLexer


class TestAstNode(unittest.TestCase):
    """Tests that ASTnode works as expected."""

    def test_empty_init(self):
        ast = ASTnode()
        self.assertIsNone(ast.left)
        self.assertIsNone(ast.right)
        self.assertIsNone(ast.token)

    def test_token_init(self):
        mocklexer = MockLexer("if = 1 2")
        token = Token(mocklexer, TokenTypes.IDENT, 0)
        ast = ASTnode(token)
        self.assertIsNone(ast.left)
        self.assertIsNone(ast.right)
        self.assertIs(ast.token, token)

    def test_all_init(self):
        mocklexer = MockLexer("if = 1 2")
        tokens = (
            Token(mocklexer, TokenTypes.IDENT, 0),
            Token(mocklexer, TokenTypes.NUMBER, 5),
            Token(mocklexer, TokenTypes.NUMBER, 7),
        )
        left = ASTnode(tokens[1])
        right = ASTnode(tokens[2])
        ast = ASTnode(tokens[0], left, right)
        self.assertIs(ast.left, left)
        self.assertIs(ast.right, right)
        self.assertIs(ast.token, tokens[0])


class TestFunc(unittest.TestCase):
    """Tests that Func class works as expected"""

    def setUp(self):
        mocklex = self.mocklex = MockLexer(
            "fn test x y is\n  if = 1 2\n     print _x\n  pring _y"
        )
        tokens = self.tokens = {
            "fn": Token(mocklex, TokenTypes.FN, 0, 2),
            "test": Token(mocklex, TokenTypes.IDENT, 3, 7),
            "x": Token(mocklex, TokenTypes.IDENT, 8, 9),
            "y": Token(mocklex, TokenTypes.IDENT, 10, 11),
            "is": Token(mocklex, TokenTypes.IS, 12, 14),
            "if": Token(mocklex, TokenTypes.IF, 17, 19),
            "=": Token(mocklex, TokenTypes.IDENT, 20, 21),
            "1": Token(mocklex, TokenTypes.NUMBER, 22, 23),
            "2": Token(mocklex, TokenTypes.NUMBER, 24, 25),
            "print": Token(mocklex, TokenTypes.IDENT, 31, 36),
            "_x": Token(mocklex, TokenTypes.IDENT, 37, 39),
            "pring": Token(mocklex, TokenTypes.IDENT, 42, 47),
            "_y": Token(mocklex, TokenTypes.IDENT, 48, 50),
        }
        self.params = [tokens["x"], tokens["y"]]
        self.body = ASTnode(
            tokens["if"],
            ASTnode(tokens["="], ASTnode(tokens["1"], ASTnode(tokens["2"]))),
            ASTnode(
                None,
                ASTnode(tokens["print"], ASTnode(tokens["_x"])),
                ASTnode(tokens["pring"], ASTnode(tokens["_y"])),
            ),
        )

    def test_init(self):
        fun = Func(self.tokens["test"])
        self.assertIs(fun.name_tok, self.tokens["test"])

    def test_name(self):
        fun = Func(self.tokens["test"])
        self.assertEqual(fun.name(), "test")

    def test_params(self):
        fun = Func(self.tokens["test"])
        fun.parm = self.params
        self.assertEqual(fun.params(), ["x", "y"])

    def test_body(self):
        fun = Func(self.tokens["test"])
        fun.body = self.body
        n = fun.body
        self.assertEqual(n.token.text(), "if")
        self.assertEqual(n.left.token.text(), "=")
        self.assertIsNone(n.right.token)


class TestParser(unittest.TestCase):
    """Tests that Parser can parse correctly"""

    def setUp(self):
        self.src = """
        fn test x y is
          if __eq 1 2
            __print x
          __print y
        """

    def test_parse(self):
        parser = Parser(self.src, Path())
        self.assertEqual(len(parser.funcs), 1)
        func = parser.funcs["test"]
        self.assertEqual(func.name(), "test")
        self.assertEqual(func.params(), ["x", "y"])
        ast = func.body
        self.assertEqual(ast.token.text(), "if")
        cond = ast.left
        self.assertEqual(cond.token.text(), "__eq")
        self.assertEqual(cond.left.token.text(), "1")
        self.assertEqual(cond.right.token.text(), "2")
        paths = ast.right
        self.assertEqual(paths.left.token.text(), "__print")
        self.assertEqual(paths.right.token.text(), "__print")
        self.assertEqual(paths.left.left.token.text(), "x")
        self.assertEqual(paths.right.left.token.text(), "y")


class TestParserSyntaxError(unittest.TestCase):
    """Tests That parser specific part of AttoSyntaxError works"""

    def test_bad_fn_def(self):
        src = "fn main print"
        with self.assertRaisesRegex(
            AttoSyntaxError, "Expected TokenTypes.IS near faker.at:1 col: 8"
        ):
            Parser(src, Path("fake/faker.at"))

    def test_bad_unknown_identier(self):
        src = "fn main is __print x"
        with self.assertRaisesRegex(
            AttoSyntaxError, "Could not find identifier x at faker.at:1 col: 19"
        ):
            Parser(src, Path("fake/faker.at"))


if __name__ == "__main__":
    unittest.main()
