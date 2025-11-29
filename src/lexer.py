"""This module tokenizes the source text."""

from __future__ import annotations
from enum import Enum
from typing import List, Tuple
from pathlib import Path


class AttoSyntaxError(SyntaxError):
    """A custom error when a syntax error occurs in atto source code.

    Parameters
    ----------
    msg : str
        The message to show
    tok : Token
        The lexer token at given error
    """

    def __init__(self, msg: str, tok: Token):
        line, col = tok.line_col()
        super().__init__(f"{msg} {tok.lexer.path.name}:{line} col: {col}")


class TokenTypes(Enum):
    """Lexical tokens"""

    FN = 1
    IS = 2
    IDENT = 3  # may be a built_in, decide when token is closed
    NUMBER = 4
    STRING = 5
    NULL = 6
    TRUE = 7
    FALSE = 8

    # intrinsic (built in from her on)
    # Flow control
    IF = 11
    # Arithmetic
    ADD = 12
    NEG = 13
    MUL = 14
    DIV = 15
    INV = 16
    REM = 17
    # Logical
    EQ = 20
    LESS = 21
    # List manipulation
    HEAD = 30
    TAIL = 31
    PAIR = 32
    FUSE = 33
    # String manipulation
    LITR = 40
    STR = 41
    WORDS = 42
    # I/O
    IN = 50
    OUT = 51
    # call, used by parser
    CALL = 60
    # fail
    FAIL = 100


class Token:
    """Hold info for one lexical token

    Parameters
    ---------
    lexer : Lexer
        The lexer that created this token
    type : TokenTypes
        The token type for this token
    start_pos : int
        The pos in lexer.source that this token starts at
    end_pos : int, Optional
        The end-position in source string, if given closes Token directly

    """

    def __init__(
        self, lexer: Lexer, type: TokenTypes, start_pos: int, end_pos: int = -1
    ):
        self.lexer = lexer
        self.type = type
        self.start_pos = start_pos
        self.end_pos = end_pos

        if end_pos > -1:
            self.close(end_pos)

    def close(self, end_pos: int) -> None:
        """Finish the token by setting the text for it

        Parameters
        ----------
        end_pos : int
            The pos in lexer.source that this token stops at
        """

        self.end_pos = end_pos

        # decide if IDENT was a build in thing
        if self.type == TokenTypes.IDENT:
            match self.text():
                case "__add":
                    self.type = TokenTypes.ADD
                case "__neg":
                    self.type = TokenTypes.NEG
                case "__mul":
                    self.type = TokenTypes.MUL
                case "__div":
                    self.type = TokenTypes.DIV
                case "__rem":
                    self.type = TokenTypes.REM
                case "__inv":
                    self.type = TokenTypes.INV
                case "__eq":
                    self.type = TokenTypes.EQ
                case "__lt":
                    self.type = TokenTypes.LESS
                case "__head":
                    self.type = TokenTypes.HEAD
                case "__tail":
                    self.type = TokenTypes.TAIL
                case "__fuse":
                    self.type = TokenTypes.FUSE
                case "__pair":
                    self.type = TokenTypes.PAIR
                case "__litr":
                    self.type = TokenTypes.LITR
                case "__str":
                    self.type = TokenTypes.STR
                case "__words":
                    self.type = TokenTypes.WORDS
                case "__input":
                    self.type = TokenTypes.IN
                case "__print":
                    self.type = TokenTypes.OUT
                case "fn":
                    self.type = TokenTypes.FN
                case "is":
                    self.type = TokenTypes.IS
                case "if":
                    self.type = TokenTypes.IF
                case "true":
                    self.type = TokenTypes.TRUE
                case "false":
                    self.type = TokenTypes.FALSE
                case "null":
                    self.type = TokenTypes.NULL

    def text(self) -> str:
        """The text value for this token extracted from source text

        Returns
        -------
        str : The source text for this token

        """
        if self.end_pos < 0:
            return ""
        return self.lexer.source[self.start_pos : self.end_pos]

    def value(self) -> str | float | bool | None:
        """Get the as correct type

        If a string it will strip "..." => ...
        If a number convert to a float and return
        All other return the text in the source text

        Returns
        -------
        str | float : The value stored in src text,
        """
        txt = self.text()
        match self.type:
            case TokenTypes.NUMBER:
                return float(txt)
            case TokenTypes.STRING:
                return txt[1:-1]
            case TokenTypes.TRUE:
                return True
            case TokenTypes.FALSE:
                return False
            case TokenTypes.NULL:
                return None
            case _:
                return txt

    def line_col(self) -> Tuple[int, int]:
        """Get the line and column in the source text this token begins at.

        Returns
        -------
        tuple[int, int] : The line and column in source text

        """
        line, col = 1, 0
        for i, c in enumerate(self.lexer.source):
            if i == self.start_pos:
                break

            if c == "\n":
                line, col = line + 1, 0
            else:
                col += 1

        return line, col

    def is_type(self, type: TokenTypes):
        return self.type == type


class LexerStates(Enum):
    """The different states the lexer state machine can be in"""

    DEFAULT = 0
    NUMBER = 1
    STRING = 2
    IDENT = 3


class Lexer:
    """Lexical analysis of the atto source text

    Parameters
    ----------
    source : str
        The atto source text to tokenize
    path : Path
        Path to file where source came from.

    Returns
    -------
    List[Token] : A list of tokens based of the source text

    """

    def __init__(self, source: str, path: Path):
        self.source: str = source
        self.path: Path = path
        self.tokens: List[Token] = []
        self._state = LexerStates.DEFAULT
        self._token: Token | None = None

        for i, c in enumerate(source):
            if self._state == LexerStates.DEFAULT:
                if c.isdigit():
                    self._begin_token(LexerStates.NUMBER, TokenTypes.NUMBER, i)
                elif c.isspace():  # whitespace ignore
                    continue
                elif c == '"':
                    self._begin_token(LexerStates.STRING, TokenTypes.STRING, i)
                elif c > " ":
                    self._begin_token(LexerStates.IDENT, TokenTypes.IDENT, i)
                else:
                    tok = Token(self, TokenTypes.FAIL, i)
                    tok.close(i + 1)
                    raise AttoSyntaxError("Unrecognized char", tok)

            elif self._state == LexerStates.NUMBER:
                if not c.isdigit() and c != ".":
                    self._end_token(i)
            elif self._state == LexerStates.IDENT:
                if c.isspace():
                    self._end_token(i)
            else:  # string
                if c == '"' and source[i - 1] != "\\":
                    self._end_token(i + 1)

        # possible dangling last token
        if self._token:
            self._token.close(len(source))
            self.tokens.append(self._token)

    def _begin_token(self, state: LexerStates, type: TokenTypes, pos: int) -> None:
        self._state = state
        self._token = Token(self, type, pos)

    def _end_token(self, end_pos: int):
        if self._token:
            self._token.close(end_pos)
            self.tokens.append(self._token)
        self._token = None
        self._state = LexerStates.DEFAULT
