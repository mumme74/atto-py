"""This module executes the actual atto code."""

from __future__ import annotations
from typing import Dict, List, Type
from pathlib import Path
from copy import deepcopy

from src.parser import Parser, ASTnode, Func
from src.lexer import TokenTypes, AttoSyntaxError

this_path = Path(__file__).absolute().parent

class AttoRuntimeError(RuntimeError):
    """When a runtime error happens in the interpreter"""
    pass

# possible value types
_Vlu = Type[None | bool | float | str ]
Value = Type[_Vlu| List[_Vlu]]

class Frame:
    """A context frame for each function call"""
    def __init__(self, caller: Frame, args: List[Value], func: Func):
        self.caller = caller
        self.args = args
        self.func = func


class Interpreter:

    _corelib_code: str | None = None
    _corelib_funcs: Dict[str, Func] | None = None

    def __init__(self, use_corelib=True):
        # initialize core lib
        if not Interpreter._corelib_code and use_corelib:
            with open(this_path.parent / "corelib" / "core.at", mode="r") as f:
                Interpreter._corelib_code = f.read()

            core_parser = Parser(Interpreter._corelib_code)
            Interpreter._corelib_funcs = core_parser.funcs

        self.use_corelib = use_corelib

    def exec_file(self, path: Path) -> int:
        try:
            with open(path, mode="r", encoding="utf8") as f:
                source = f.read()
        except (FileNotFoundError, IOError) as e:
            print(f"Error opening file: {path}: {e}")
            return 1
        else:
            return self.exec(source)

    def exec(self, source: str) -> int:
        funcs = deepcopy(Interpreter._corelib_funcs)
        try:
            self.parser = Parser(source, funcs)
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
                lst = self._eval_node(node.left, frame)
                if not isinstance(lst, list):
                    line, col = node.left.token.line_col()
                    raise AttoRuntimeError(
                        f"Trying to get head of a non list at line: {line} col: {col}")
                return lst[0]

            case TokenTypes.TAIL:
                lst = self._eval_node(node.left, frame)
                if not isinstance(lst, list):
                    line, col = node.left.token.line_col()
                    raise AttoRuntimeError(
                        f"Trying to get tail of a non list at line: {line} col: {col}")
                return lst[-1]

            case TokenTypes.PAIR:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)
                return [left, right]

            case TokenTypes.FUSE:
                left = self._eval_node(node.left, frame)
                right = self._eval_node(node.right, frame)

                if not isinstance(left, list):
                    n = left
                elif not isinstance(right, list):
                    n = right
                if n:
                    line, col = n.token.line_col()
                    raise AttoRuntimeError(
                        f"Trying to fuse non list at line: {line} col: {col}")

                return [e for e in left] + [e for e in right]

            case TokenTypes.LITR:
                left = self._eval_node(node.left, frame)
                if isinstance(left, float):
                    return left
                elif isinstance(left, str):
                    try:
                        return float(left)
                    except ValueError:
                        pass
                # catches when left is a list
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
                raise RuntimeError(
                    f"Unhandled token type {node.token.type}")
