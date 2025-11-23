"""This module parses the tokenized source text.

It is implemented as a simple recursive descent parser.
Output is an Abstract syntax tree that the interpreter uses.
"""

from __future__ import annotations
from typing import Dict, List
from src.lexer import Token, TokenTypes, Lexer, AttoSyntaxError
from pathlib import Path


class EOFerror(Exception):
    """Used to indicate END of file"""

    pass


class ASTnode:
    """A node in the Abstract syntax tree"""

    def __init__(
        self,
        token: Token | None = None,
        left: ASTnode | None = None,
        right: ASTnode | None = None,
    ):
        self.left: ASTnode | None = left
        self.right: ASTnode | None = right
        self.token: Token | None = token


class Func:
    """All parsed functions currently in scope

    Parameters
    ----------
    name_tok : Token
        The token that defines this functions name

    Attributes
    ----------
    name_tok : Token
        The token that defined this functions name
    params : List[Token]
        The tokens for each parameter (arguments)
    body : ASTnode
        A root for the AST tree for the body of this function
    late_binding_start_pos : int
        The body pos for this function, used to do late binding of identifiers
    """

    def __init__(self, name_tok: Token):
        self.name_tok: Token = name_tok
        self.parm: List[Token] = []
        self.body: ASTnode | None
        self.late_binding_startpos: int | None

    def name(self) -> str:
        """Get the name of the function"""
        return self.name_tok.text()

    def params(self):
        """Get a list of param names"""
        return [tok.value() for tok in self.parm]


class Parser:
    """The parser class, build the AST tree

    Attributes
    ----------
    lexer : Lexer
        The lexer used to tokenize the code
    funcs : Dict[str, Func]
        All parsed functions this program contains

    Parameters
    ----------
    source : str
        The source code to parse
    path : Path
        The path to source-code file
    funcs : Dict[str, Func], Optional
        Functions already parsed, used for corelib
    """

    def __init__(self, source: str, path: Path, funcs: Dict[str, Func] | None = None):
        self.lexer = Lexer(source, path)
        self._pos = -1
        self.funcs: Dict[str, Func] = {} if funcs is None else funcs
        self._parse_funcs()

    def _back(self) -> None:
        self._pos = self._pos - 1 if self._pos > -1 else -1

    def _next(self) -> Token:
        self._pos += 1
        try:
            return self.lexer.tokens[self._pos]
        except IndexError:
            raise EOFerror()

    def _last_body_pos(self):
        while tok := self._next():
            if tok.is_type(TokenTypes.FN):
                self._back()
                return self._pos

    def _expect(self, tok_type: TokenTypes) -> Token:
        tok = self._next()
        if not tok.is_type(tok_type):
            raise AttoSyntaxError(f"Expected {tok_type}", tok)

        return tok

    def _parse_funcs(self) -> None:
        try:
            while True:
                self._expect(TokenTypes.FN)
                self._parse_func_sig()
        except EOFerror:
            pass

        for func in self.funcs.values():
            self._parse_late_binding(func)

    def _parse_func_sig(self) -> None:
        self._cur_func = Func(self._expect(TokenTypes.IDENT))
        self.funcs[self._cur_func.name_tok.text()] = self._cur_func

        try:
            self._parse_fn_args(self._cur_func)
            self._expect(TokenTypes.IS)
        except EOFerror:
            last_tok = (
                self._cur_func.parm[-1]
                if self._cur_func.parm
                else self._cur_func.name_tok
            )
            raise AttoSyntaxError(f"Expected {TokenTypes.IS} near", last_tok)

        self._cur_func.late_binding_startpos = self._pos
        self._last_body_pos()

    def _parse_fn_args(self, func: Func) -> None:
        while tok := self._next():
            if not tok.is_type(TokenTypes.IDENT):
                self._back()
                break
            func.parm.append(tok)

    def _parse_late_binding(self, func: Func):
        if func.late_binding_startpos is not None:
            self._cur_func = func
            self._pos = func.late_binding_startpos
            func.body = self._parse_expr()
            func.late_binding_startpos = None

    def _parse_expr(self) -> ASTnode | None:
        while tok := self._next():
            match tok.type:
                case TokenTypes.FN:
                    self._back()  # reached end of function body
                    return None
                case TokenTypes.IDENT:
                    if tok.text() in self._cur_func.params():
                        return ASTnode(tok)  # reached end of chain
                    elif tok.text() in self.funcs:
                        return self._parse_call(tok)
                    raise AttoSyntaxError(
                        f"Could not find identifier {tok.text()} at", tok
                    )
                case (
                    TokenTypes.STRING
                    | TokenTypes.NUMBER
                    | TokenTypes.TRUE
                    | TokenTypes.FALSE
                    | TokenTypes.NULL
                ):
                    return ASTnode(tok)  # reached epsilon
                case TokenTypes.IF:
                    node = ASTnode(
                        tok,
                        self._parse_expr(),
                        ASTnode(None, self._parse_expr(), self._parse_expr()),
                    )
                    if node.left is None:
                        raise AttoSyntaxError("Expected if condition", tok)
                    elif node.right.left is None:  # type: ignore[union-attr]
                        raise AttoSyntaxError("Expected true expression", tok)
                    elif node.right.right is None:  # type: ignore[union-attr]
                        raise AttoSyntaxError("Expected false expression", tok)
                    return node
                case TokenTypes.ADD:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.NEG:
                    return ASTnode(tok, self._parse_expr())
                case TokenTypes.MUL:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.DIV:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.INV:
                    return ASTnode(tok, self._parse_expr())
                case TokenTypes.REM:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.EQ:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.LESS:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.HEAD:
                    return ASTnode(tok, self._parse_expr())
                case TokenTypes.TAIL:
                    return ASTnode(tok, self._parse_expr())
                case TokenTypes.PAIR:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.FUSE:
                    return ASTnode(tok, self._parse_expr(), self._parse_expr())
                case TokenTypes.LITR:
                    return ASTnode(tok, self._parse_expr())
                case TokenTypes.STR:
                    return ASTnode(tok, self._parse_expr())
                case TokenTypes.WORDS:
                    return ASTnode(tok, self._parse_expr())
                case TokenTypes.IN:
                    ident = self._expect(TokenTypes.IDENT)
                    return ASTnode(tok, ASTnode(ident))
                case TokenTypes.OUT:
                    return ASTnode(tok, self._parse_expr())
                case _:
                    raise AttoSyntaxError(f"Unexpected token: {tok.type} at", tok)
        return None

    def _parse_call(self, tok: Token):
        tok.type = TokenTypes.CALL
        # grab as many parameters as there are in the function definition
        func = self.funcs[tok.text()]
        args = [self._parse_expr() for _ in func.parm]
        node = ASTnode(tok)

        if args:
            # store the actual arg in the right slot, leave left for next args
            n = node.left = ASTnode(None, None, args.pop(0))
            while args:
                n.left = ASTnode(None, None, args.pop(0))
                n = n.left

        return node
