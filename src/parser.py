"""This module parses the tokenized source text.

It is implemented as a simple recursive descent parser.
Output is an Abstract syntax tree that the interpreter uses.
"""
from __future__ import annotations
from typing import Dict, List
from src.lexer import Token, TokenTypes, Lexer, AttoSyntaxError

class EOFerror(Exception):
    """Used to indicate END of file"""
    pass

class ASTnode:
    """A node in the Abstract syntax tree"""
    def __init__(self,
                 token: Token | None = None,
                 left: ASTnode | None = None,
                 right: ASTnode |None = None):
        self.left:  ASTnode | None = left
        self.right: ASTnode | None = right
        self.token: Token   | None = token


class Func:
    """All parsed functions currently in scope

    Parameters
    ----------
    nameTok : Token
        The token that defines this functions name

    Attributes
    ----------
    nameTok : Token
        The token that defined this functions name
    params : List[Token]
        The tokens for each parameter (arguments)
    body : ASTnode
        A root for the AST tree for the body of this function
    """
    def __init__(self, nameTok: Token):
        self.nameTok: Token = nameTok
        self.parm: List[Token] = []
        self.body: ASTnode

    def name(self) -> str:
        """Get the name of the function"""
        return self.nameTok.value()

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
    funcs : Dict[str, Func], Optional
        Functions already parsed, used for corelib
    """

    def __init__(self, source: str, funcs: Dict[str, Func]=None):
        self.lexer = Lexer(source)
        self._pos = -1
        self.funcs: Dict[str, Func] = {} if funcs is None else funcs
        self._parse_funcs()

    def _back(self) -> Token:
        self._pos = self._pos -1 if self._pos > -1 else -1

    def _next(self) -> Token:
        self._pos += 1
        try:
            return self.lexer.tokens[self._pos]
        except IndexError:
            raise EOFerror()

    def _expect(self, tok_type: TokenTypes) -> Token:
        tok = self._next()
        if not tok.is_type(tok_type):
            line, col = tok.line_col()
            raise AttoSyntaxError(
                f"Expected an {tok_type} at line: {line}, col: {col}")

        return tok

    def _parse_funcs(self) -> None:
        try:
            while True:
                self._expect(TokenTypes.FN)
                self._parse_func()
        except EOFerror:
            pass

    def _parse_func(self) -> None:
        self._cur_func = Func(self._expect(TokenTypes.IDENT))
        self.funcs[self._cur_func.nameTok.value()] = self._cur_func

        self._parse_fn_args(self._cur_func)
        self._expect(TokenTypes.IS)

        self._cur_func.body = self._parse_expr()

    def _parse_fn_args(self, func: Func) -> None:
        while tok := self._next():
            if not tok.is_type(TokenTypes.IDENT):
                self._back()
                break
            func.parm.append(tok)

    def _parse_expr(self) -> ASTnode:
        while tok := self._next():
            match tok.type:
                case TokenTypes.FN:
                    self._back() #reached end of function body
                    return None
                case TokenTypes.IDENT:
                    if tok.text() in self._cur_func.params():
                        return ASTnode(tok) # reached end of chain
                    elif tok.text() in self.funcs:
                        return self._parse_call(tok)
                    line, col = tok.line_col()
                    raise AttoSyntaxError(
                        f"Could not find identifer {tok.text()}, " +
                        f" at line: {line}, col: {col}")
                case TokenTypes.STRING | TokenTypes.NUMBER | TokenTypes.TRUE | \
                    TokenTypes.FALSE | TokenTypes.NULL:
                    return ASTnode(tok) #reached epsilon
                case TokenTypes.IF:
                    return ASTnode(tok, self._parse_expr(),
                               ASTnode(None,
                                       self._parse_expr(),
                                       self._parse_expr()))
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
                    line, col = tok.line_col()
                    type = tok.type
                    raise AttoSyntaxError(
                        f"Unexpected token: {type} at line: {line}, col: {col}")

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

