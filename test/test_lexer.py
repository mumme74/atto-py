import unittest
from pathlib import Path

from src.lexer import Token, TokenTypes, Lexer, AttoSyntaxError
from mocks import MockLexer

class TestTokenBuild(unittest.TestCase):
    """Tests that Token builds properly"""

    def setUp(self):
        self.mocklex = MockLexer("__eq 1 1")
        self.tok = Token(self.mocklex, TokenTypes.IDENT, 0)

    def test_init(self):
        self.assertEqual(self.tok.start_pos, 0)
        self.assertEqual(self.tok.end_pos, -1)
        self.assertEqual(self.tok.type, TokenTypes.IDENT)
        self.assertIs(self.tok.lexer, self.mocklex)

    def test_text_unclosed(self):
        self.assertEqual(self.tok.text(), "")

    def test_text_clos_from_init(self):
        tok = Token(self.mocklex, TokenTypes.IDENT, 0, 4)
        self.assertEqual(tok.type, TokenTypes.EQ)
        self.assertEqual(tok.text(), "__eq")

    def test_text_closed(self):
        self.tok.close(4)
        self.assertEqual(self.tok.text(), "__eq")

    def test_text_onech_num(self):
        tok = Token(self.mocklex, TokenTypes.IDENT, 5)
        tok.close(6)
        self.assertEqual(tok.text(), "1")

class TestTextValue(unittest.TestCase):
    """Tests that Token reports text and value correctly"""

    def test_text_string(self):
        mocklex = MockLexer('"This is a string."')
        tok = Token(mocklex, TokenTypes.STRING, 0)
        tok.close(19)
        self.assertEqual(tok.text(), '"This is a string."')
        self.assertEqual(tok.value(), "This is a string.")

    def test_ident(self):
        mocklex = MockLexer("name")
        tok = Token(mocklex, TokenTypes.IDENT, 0)
        tok.close(4)
        self.assertEqual(tok.type, TokenTypes.IDENT)
        self.assertEqual(tok.text(), "name")
        self.assertEqual(tok.value(), "name")

    def test_number(self):
        mocklex = MockLexer("1234")
        tok = Token(mocklex, TokenTypes.NUMBER, 0)
        tok.close(4)
        self.assertEqual(tok.text(), "1234")
        self.assertEqual(tok.value(), 1234)


class TestTokenLineCol(unittest.TestCase):
    """Tests that Token reports line and column correctly"""

    def create(self, pos):
        self.mocklex = MockLexer("if < 1 2\n print 2")
        return Token(self.mocklex, TokenTypes.IDENT, pos)

    def test_line_col_begin(self):
        tok = self.create(0)
        tok.close(2)
        line, col = tok.line_col()
        self.assertEqual(line, 1)
        self.assertEqual(col, 0)

    def test_line_col_first_line(self):
        tok = self.create(3)
        tok.close(4)
        line, col = tok.line_col()
        self.assertEqual(line, 1)
        self.assertEqual(col, 3)

    def test_line_col_line2(self):
        tok = self.create(10)
        tok.close(15)
        line, col = tok.line_col()
        self.assertEqual(line, 2)
        self.assertEqual(col, 1)


class TestLexer(unittest.TestCase):
    """Tests that Lexer can tokenize as expected"""

    def test_empty(self):
        lex = Lexer("", Path())
        self.assertEqual(len(lex.tokens), 0)

    def test_one_token(self):
        lex = Lexer("one", Path())
        self.assertEqual(len(lex.tokens), 1)
        tok = lex.tokens[0]
        self.assertEqual(tok.type, TokenTypes.IDENT)
        self.assertEqual(tok.text(), "one")

    def test_statement(self):
        lex = Lexer("__eq 1 2", Path())
        self.assertEqual(len(lex.tokens), 3)
        self.assertEqual(lex.tokens[0].text(), '__eq')
        self.assertEqual(lex.tokens[1].text(), '1')
        self.assertEqual(lex.tokens[2].text(), '2')
        self.assertEqual(lex.tokens[0].type, TokenTypes.EQ)

    def test_build_in(self):
        T = TokenTypes
        types = (T.ADD, T.NEG, T.MUL, T.DIV, T.INV, T.REM, T.EQ, T.LESS,
                 T.HEAD, T.TAIL, T.PAIR, T.FUSE, T.LITR, T.STR, T.WORDS, T.IN,
                 T.OUT)
        op = ('add','neg','mul','div','inv','rem','eq','lt','head',
              'tail','pair','fuse','litr','str','words','input','print')

        for op, type in zip(op, types):
            lex = Lexer(f"__{op}", Path())
            self.assertEqual(lex.tokens[0].type, type)
            self.assertEqual(lex.tokens[0].text(), f"__{op}")

    def test_fn(self):
        lex = Lexer("fn 1 is", Path())
        self.assertEqual(lex.tokens[0].type, TokenTypes.FN)
        self.assertEqual(lex.tokens[2].type, TokenTypes.IS)

    def test_if(self):
        lex = Lexer("if = 1 2", Path())
        self.assertEqual(lex.tokens[0].type, TokenTypes.IF)

    def test_number(self):
        lex = Lexer(" 1234 ", Path())
        self.assertEqual(lex.tokens[0].type, TokenTypes.NUMBER)
        self.assertEqual(lex.tokens[0].text(), "1234")
        self.assertEqual(lex.tokens[0].value(), 1234)


class TestAttoSyntaxError(unittest.TestCase):
    """Tests that AttoSyntaxError works"""

    def test_init(self):
        lex = Lexer(" 1245", Path("fake/fakefile.at"))
        tok = lex.tokens[0]
        err = AttoSyntaxError("TestError", tok)
        self.assertEqual(err.msg, "TestError fakefile.at:1 col: 1")

    def test_lex_raise(self):
        with self.assertRaisesRegex(AttoSyntaxError, "Unrecognized char faker.at:2 col: 1"):
            Lexer("\n \b", Path("fake/faker.at"))


if __name__ == "__main__":
    unittest.main()
