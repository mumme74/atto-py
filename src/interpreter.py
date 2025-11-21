"""This module executes the actual atto code."""

from __future__ import annotations
from typing import Dict, List, Type
from pathlib import Path
from copy import deepcopy
from sys import setrecursionlimit

from src.parser import Parser, ASTnode, Func
from src.lexer import TokenTypes, AttoSyntaxError

# Path to src folder
SRC_PATH = Path(__file__).absolute().parent

# Path to core lib file
CORE_LIB_PATH = SRC_PATH.parent / "corelib" / "core.at"

# Allow for complex factorials to not smash recursion limit
setrecursionlimit(10**6)

class AttoRuntimeError(RuntimeError):
    """When a runtime error happens in the interpreter"""
    pass

# possible value types
_Vlu = Type[None | bool | float | str ]
Value = Type[_Vlu| List[_Vlu]]

class Frame:
    """A context frame for each function call.
    That is the the runtime info while fn is eceuted.

    Attributes
    ----------
    caller : Frame
        The frame that called this frame. The parent in a stacktrace.
    args : List[Value]
        Arguments for this frame
    func : Func
        The Func object, parsed representation of the function to execute
    """

    def __init__(self, caller: Frame, args: List[Value], func: Func):
        self.caller = caller
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

        funcs = deepcopy(Interpreter._corelib_funcs)
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
            raise AttoRuntimeError(f"Function main is not found in the source.")

        frame = Frame(None, [], self.parser.funcs['main'])
        node = frame.func.body
        vlu = self._eval_node(node, frame)

        try:
            return int(vlu)
        except (TypeError, ValueError):
            return 0


    def _eval_node(self, node: ASTnode, frame: Frame) -> Value:
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
                    return self._eval_node(node.right.left, frame)
                else:
                    return self._eval_node(node.right.right, frame)

            case TokenTypes.ADD:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return left + right

            case TokenTypes.NEG:
                return -self._eval_node(node.left, frame)

            case TokenTypes.MUL:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return left * right

            case TokenTypes.DIV:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return left / right

            case TokenTypes.INV:
                left = self._eval_node(node.left, frame)
                return 1 / left

            case TokenTypes.REM:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return left % right

            case TokenTypes.EQ:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return left == right

            case TokenTypes.LESS:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return left < right

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
                return [left, right]

            case TokenTypes.FUSE:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)

                if isinstance(left, list):
                    if isinstance(right, list):
                        return left + right
                    left.append(right)
                    return left
                elif isinstance(right, list):
                    return [left] + right
                return [left, right]

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
                line, col = node.left.token.line_col()
                raise AttoRuntimeError(
                    f"Failed to convert {node.left.token.value} to " +
                        "number at line: {line}, col: {col}")

            case TokenTypes.STR:
                left = self._eval_node(node.left, frame)
                if (isinstance(left, list)):
                    lst = [str(e) for e in left]
                    return ' '.join(lst)
                return str(left)

            case TokenTypes.WORDS:
                left = self._eval_node(node.left, frame)
                if isinstance(left, str):
                    return left.split()

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

            case TokenTypes.CALL:
                new_func = self.parser.funcs[node.token.text()]
                # get the args
                args = []
                n = node
                while n := n.left:
                    args.append(self._eval_node(n.right, frame))

                #print("Calling", new_func.name(), "args", args, "from", node.token.line_col())

                # do the call
                new_frm = Frame(frame, args, new_func)
                return self._eval_node(new_func.body, new_frm)

            case _:
                raise AttoRuntimeError(
                    f"Unhandled token type {node.token.type}")
