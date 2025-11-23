"""This module executes the actual atto code."""

from __future__ import annotations
from typing import Dict, List, Union, cast
from pathlib import Path
from copy import deepcopy
from sys import setrecursionlimit

from src.parser import Parser, ASTnode, Func
from src.lexer import Token, TokenTypes, AttoSyntaxError

# Path to src folder
SRC_PATH = Path(__file__).absolute().parent

# Path to core lib file
CORE_LIB_PATH = SRC_PATH.parent / "corelib" / "core.at"

# Allow for complex factorials to not smash recursion limit
setrecursionlimit(10**6)

# possible value types
Value = Union[None | bool | float | str | List[None | bool | float | str]]

class AttoMissingMainError(RuntimeError):
    """When main function is missing."""
    def __init__(self, msg):
        super().__init__(f"RuntimeError: {msg}")


class AttoRuntimeError(RuntimeError):
    """When a runtimerror error happens"""
    def __init__(self, msg: str, tok: Token, frame: Frame):
        line, col = tok.line_col()
        super().__init__(
            f"RuntimeError: {msg} {tok.lexer.path.name}:{line} col: {col}")
        self.frame = frame
        self.tok   = tok

    def traceback(self, limit: int=15) -> List[str]:
        """Generate a traceback for this error.

        Attributes
        ----------
        limit : int
            Limit long backtraces to this length
        """

        tb = []
        stack = 0
        frm: Frame | None = self.frame
        tok: Token | None = self.tok
        while frm and tok and limit - stack > 0:
            line, col = tok.line_col()
            file = tok.lexer.path.name
            tb.append((f"Calling: {tok.text()} from within function {frm.func.name()} "
                       f"at {file}:{line} col:{col}"))
            limit -= 1
            tok = frm.caller_tok
            frm = frm.caller_frm

        if frm:
            tb.append('...')

        return tb

    def __str__(self):
        msg = super().__str__()
        return f"{msg}\n\nTraceback:\n{'\n'.join(self.traceback())}"


class Frame:
    """A context frame for each function call.
    That is the the runtime info while fn is eceuted.

    Attributes
    ----------
    caller_frm : Frame
        The frame that called this frame. The parent in a stacktrace.
    caller_tok : Token
        The token that called this frame.
    args : List[Value]
        Arguments for this frame
    func : Func
        The Func object, parsed representation of the function to execute
    """

    def __init__(self, caller_frm: Frame | None, caller_tok: Token | None,
                 args: List[Value], func: Func):
        self.caller_frm = caller_frm
        self.caller_tok = caller_tok
        self.args = args
        self.func = func


class Interpreter:
    """The interpreter class, executes the parsed source code.

    It loads a source file or plain source text, lets the Parser parse it into
    an AST tree, then walks that tree to execute our program.

    By default it loads the atto corelib and mixes that into the function
    signatures of our program. It is possible to exclude corelib, but not
    recomended.

    Attributes
    ----------
    use_codelib : bool
        Wheater we use corelib, defaults to True
    parser : Parser
        The Parser instance that parsed the AST tree

    Parameters
    ----------
    use_corelib : bool, optional(True)
        Wheather we should load corelib, recomend to leave as is if not in
        a unittest mode
    """

    _corelib_code: str | None = None
    _corelib_funcs: Dict[str, Func] | None = None

    def __init__(self, use_corelib=True):
        # initialize core lib as a singleton pattern
        if not Interpreter._corelib_code and use_corelib:
            with open(CORE_LIB_PATH, mode="r") as f:
                Interpreter._corelib_code = f.read()

            core_parser = Parser(Interpreter._corelib_code, CORE_LIB_PATH)
            Interpreter._corelib_funcs = core_parser.funcs

        self.use_corelib = use_corelib

    def exec_file(self, path: Path) -> int:
        """Loads an atto source file as then executes it.

        Parameters
        ----------
        path : Path
            The path to the file to load, relative to project main.py file

        Returns
        -------
        int : The result of the last execution in program
        """

        try:
            with open(path, mode="r", encoding="utf8") as f:
                source = f.read()
        except (FileNotFoundError, IOError) as e:
            print(f"Error opening file: {path}: {e}")
            return 1
        else:
            return self.exec(source, path)

    def exec(self, source: str, path: Path|None = None) -> int:
        """Execute atto source text and return the last execution result.

        Parameters
        ----------
        source : str
            The source text to execute
        path : Path | None, Optional(None)
            The path where source text came from.
            Displays filename in error messages.
        """

        funcs = deepcopy(Interpreter._corelib_funcs) if self.use_corelib else {}
        if path is None:
            path = Path()
        try:
            self.parser = Parser(source, path, funcs)
        except AttoSyntaxError as e:
            print(e)
            return 1
        else:
            return self._eval()

    def _eval(self) -> int:
        if not "main" in self.parser.funcs:
            raise AttoMissingMainError(
                    "Function main is not found in the source.")

        frame = Frame(None, None, [], self.parser.funcs['main'])
        node = frame.func.body
        vlu = self._eval_node(node, frame)

        if vlu is None:
            return 0
        elif isinstance(vlu, float):
            return int(vlu)
        elif isinstance(vlu, str):
            try:
                return int(vlu)
            except (TypeError, ValueError):
                return 0
        else:
            return 0


    def _eval_node(self, node: ASTnode | None, frame: Frame) -> Value:
        """Evaluates each AST node recursivly

        This is the tree-traversal method for each AST node.
        A more grown up interpreter would use this step to compile to bytecode
        instead and let the Intpreter stage come after the compile stage.
        As atto is as simple as possible we evaluate directly from the AST tree.

        Parameters
        ----------
        node : ASTnode
            The node to evaluate
        frame : Frame
            The function frame currently executing.
            When you think of a call stack, each entry in a callstack is a Frame

        Returns
        -------
        Value : The result of current expression
        """

        # This function is a bit lengthy, although that is nothing compared to
        # cpythons internal eval loop which in the past spanned several 1000 lines.
        # doing this in one function, instead of delegating from a router function
        # is actually simpler and more efficient (less call overhead and scattering).
        # Each entry is rather neatly structured due to the match case construct.
        assert node is not None
        assert node.token is not None

        match node.token.type:
            case TokenTypes.IDENT:
                name = node.token.text()
                return frame.args[frame.func.params().index(name)]

            case TokenTypes.NUMBER | TokenTypes.STRING | TokenTypes.TRUE | \
                 TokenTypes.FALSE | TokenTypes.NULL:
                return node.token.value()

            case TokenTypes.IF:
                expr = self._eval_node(node.left, frame)
                if expr:
                    return self._eval_node(node.right.left, frame)# type: ignore [union-attr]
                else:
                    return self._eval_node(node.right.right, frame)# type: ignore [union-attr]

            case TokenTypes.ADD:
                # The parser ensures node left and node right are populated.
                left = self._eval_node(node.left, frame) # type: ignore [union-attr]
                right = self._eval_node(node.right, frame) # type: ignore [union-attr]
                self.check_type(left, (float, str), node.left, frame)
                self.check_type(right, (float, str), node.right, frame)
                return left + right # type: ignore [operator]

            case TokenTypes.NEG:
                vlu = self._eval_node(node.left, frame)
                self.check_type(vlu, (float,), node, frame)
                return -vlu # type: ignore [operator]

            case TokenTypes.MUL:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                self.check_type(left, (float,), node.right, frame)
                self.check_type(right, (float,), node.right, frame)
                return left * right # type: ignore [operator]

            case TokenTypes.DIV:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                self.check_type(left, (float,), node.right, frame)
                self.check_type(right, (float,), node.right, frame)
                return left / right # type: ignore [operator]

            case TokenTypes.INV:
                left = self._eval_node(node.left, frame)
                self.check_type(left, (float,), node.right, frame)
                return 1 / left # type: ignore [operator]

            case TokenTypes.REM:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                self.check_type(left, (float,), node.right, frame)
                self.check_type(right, (float,), node.right, frame)
                return left % right # type: ignore [operator]

            case TokenTypes.EQ:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return left == right

            case TokenTypes.LESS:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                self.check_type(left, (float, str), node.right, frame)
                self.check_type(right, (float, str), node.right, frame)
                return left < right # type: ignore [operator]

            case TokenTypes.HEAD:
                left = self._eval_node(node.left, frame)
                if isinstance(left, (list, str)):
                    return left[0] if left else None
                return None

            case TokenTypes.TAIL:
                left = self._eval_node(node.left, frame)
                if isinstance(left, (list, str)):
                    return left[1:] if len(left) > 1 else None
                return None

            case TokenTypes.PAIR:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return cast(Value, [left, right])

            case TokenTypes.FUSE:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)

                if isinstance(left, list):
                    if isinstance(right, list):
                        return cast(Value, left + right)
                    left.append(right)
                    return cast(Value, left)
                elif isinstance(right, list):
                    return cast(Value, [left] + right)
                return cast(Value, [left, right])

            case TokenTypes.LITR:
                left = self._eval_node(node.left, frame)
                if isinstance(left, float):
                    return left
                elif isinstance(left, str):
                    try:
                        return float(left)
                    except ValueError:
                        pass
                # also catches when left is a list
                line, col = node.left.token.line_col() # type: ignore [union-attr]
                value = node.left.token.value() # type: ignore [union-attr]
                raise AttoRuntimeError(
                    (f"Failed to convert {value} to "
                     f"number at line: {line}, col: {col}"),
                    node.token, frame)

            case TokenTypes.STR:
                left = self._eval_node(node.left, frame)
                if (isinstance(left, list)):
                    lst = [str(e) for e in left]
                    return ' '.join(lst)
                return str(left)

            case TokenTypes.WORDS:
                left = self._eval_node(node.left, frame)
                if isinstance(left, str):
                    return cast(Value, left.split())

            case TokenTypes.IN:
                if node.left:
                    return input(self._eval_node(node.left, frame))
                return input()

            case TokenTypes.OUT:
                left = self._eval_node(node.left, frame)
                if isinstance(left, bool):
                    print(str(left).lower())
                elif left is None:
                    print("null")
                else:
                    print(left)
                return None

            case TokenTypes.CALL:
                new_func = self.parser.funcs[node.token.text()]
                # get the args
                args = []
                n:ASTnode = node
                while n := n.left: # type: ignore [assignment]
                    args.append(self._eval_node(n.right, frame))

                # uncomment to debug interpreter function calls
                # print("Calling", new_func.name(), "args", args, "from", node.token.line_col())

                # do the call
                new_frm = Frame(frame, node.token, args, new_func)
                return self._eval_node(new_func.body, new_frm)

            case _:
                raise AttoRuntimeError(
                    f"Unhandled token type {node.token.type}",
                    node.token, frame)

        return None # make mypy happy

    def check_type(self, vlu: Value, types: tuple, node: ASTnode|None, frm: Frame):
        """Checks whether type is of type, raises an error otherwise

        Parameters
        ----------
        vlu : Value
            The value to check
        types : tuple[any]
            A list of valid types
        node : ASTnode
            The ASTnode to generate the error from
        frm : Frame
            The frame to generate the error from
        """

        for t in types:
            if isinstance(vlu, t):
                return

        assert node is not None
        msg = f"Expected types {[type(t) for t in types]} but got {type(vlu)}"
        raise AttoRuntimeError(msg, node.token, frm) # type: ignore [arg-type]
