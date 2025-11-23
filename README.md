# Implementation of the very simple functional language atto.
## Atto was created by Joshua Berretto (zesterer)
This project aims to re-create this very simple Language interpreter in python.

## The original atto language:
Mr Joshua Berretto, github user: zesterer, created this very simple language and the interpreter in rust to show what was possible to in a couple of hundred lines of rust code.  
That intepreter can be found at https://github.com/zesterer/atto/ and will henceforth be namned the reference implementation.

## Why create an interpreter in python?
The purpose of this project is mostly the learning process for me. I am currently studying a course about code quality and programming principles given at Umeå university. That said, another person could just as well test and follow along if he/she wants to understande how a language engine works in an easier language than C. Pyhton should be simpler to follow along in.

## The goal of this project
My goal with this project is to get this interpreter to work with all examples in the examples directory in the reference implementation. Another goal is that the code and implementation should be documented enough so that a skilled python dev with limited langugage engine internals, should be able to grasp whats going on under the hood.

## Project limits
This project does NOT intend to do any optimization efforts either in efficiency or in security. This is a learning tool, not a real langugage you would write real applications in.

## Current state 
Overall the functional part of the goals are satisfied. All examples from reference implementation does work.

Documentation is more or less finished, with many docstrings in the code and a, hopfully, descriptive README.

# The atto language:
Atto is a very simple functional language with unmutable variables. It  has a very simple syntax, with polish notation.
That is the operator goes before the operands.  

## Hello World in atto
```
fn main is 
  print "Hello world!"
```

## Syntax
The language only has two kinds of structures:  
 ```fn <function name> is <expression>```  
 and  
 ```<literal> [expression]```  
 where a literal can be any (almost) character.  
For example **=** is a function from attos corelib  
  
Each expression returns its evaluated value. The last evaluated value in a function is returned.
  
A program should have exactly one *main* function, used as the programs entry point.

## Polish notation 
Note that the '+' operator comes before the the operands.
```
fn add x y is
  + x y
```

This is abit strange at first, but makes the parser simpler.The equivalent in python would be:
```python
def add(x, y): 
  return x + y
```

## Whitespace
The language does not have any significant whitespace. The parser does not care about indentation or anything like that.
A new function declaration just ends the previous function body. You do need to add space between words, as in any language.

## Identifiers
The language allows for an identifier, such as a function- or variablename, to have almost any character. For example the equality **=** operator is actually a function in the corelib that in turn calls the internal function **__eq**

## Functions
A function is declared with this syntax: 
``` 
fn name param1, param2, ... is   
    # "Function body
    ...
```
A function can have zero or more paramaters. When calling a function the same number of arguments are grabbed from the call. example:
```
fn multiply x, y is
    * x y

fn main is
  print multiply 100 20
  # "   ^call    ^args^"
```

The value of the last evaluated expression in a function body is its implicit return value.

### Gothcha: function call:  
As each function call just graps as many arguments from the caller as it needs. That means if yoou forget an argument, you wont get any error messages if there are more to grap from the caller function.
```
fn multiply x, y is
    * x y

fn main is
  print multiply 100
  print "done!"
  # "Function multiply will be called with args 100 and
     the result of calling print "done!", ie null"
```
Note that as we forgot the second argument in the call to multiply, the parser just grabbed the next expressions value. In this case that is the result of the print call on the second row in the main function. Print returns null so this call is equivialent to: ```multiply 100 null``` with "done!" printed before the function call.
  
## Function scope 
Function scope is limited to current function only. There can not be any global variables nor any nested functions. A function can only work with what it gets as input as arguments from the caller.

## Variables: unmutable
Variables are defined as parameters to a function. The only way to set the value is as argument by the caller, inside the function body it is unmutable (Can't change value nor type).
That means that recursion is a very common thing to use while programming, for example to create a loop structure.  
  
## No statements, only expressions
There are only expressions in this language. That means that you build up your return value by chaining togehter expressions. Even an **if** is an expression, that means that **if** behaves as a **ternary if** on other langugages.  
Example:
```
fn is_within_window vlu lower upper is
   if and < vlu upper ! < vlu lower
     true # "return value if vlu is inside window"
     false # "return value if not"
```
The if condition from above example becomes a bit strnge due the polish notation. In python it would be:
```python
def is_within_window(vlu, lower, upper):
    return True if vlu < upper and not vlu < lower else False

# which in python probably should be re-written with statements instead
def is_within_window2(vlu, lower, upper):
    if vlu < upper and vlu > lower:
        return True
    else:
        return False

```
## Comments
All expressions in atto must be chained together in an expression chain. Even comments are actually an expression that simply has the value of the expression directly after it. That is the reason for the need to use strings for a comment.

## Keywords
The keywords in atto language are:
```
fn     is    if      true    false   null 
__add  __neg __mul   __div   __rem   __inv
__eq   __lt  __head  __tail  __fuse  __pair 
__litr __str __words __input __print
```

## Types
Atto has 5 datatypes:
| name  | python equiv. | description |
|-------|---------------|-------------|
| null  | None          | nothing-ness|
| bool  | bool          | true/false  |
| number| float         | any number  |
| string| str           | "string"    |
| list  | list          | build up with pair |

## Corelib
The corelib in atto has these functions
| fn.name | parameters | return | description |
|------   |------------|--------|-------------|
| =       | x y        | bool   | true if x = y |
| <       | x y        | bool   | true if x < y |
| !       | x          | bool   | negate x, not x |
| or      | x y        | bool   | true if x or y  |
| and     | x y        | bool   | true if x and y |
| +       | x y        | number | result of x + y |
| -       | x y        | number | result of x - y |
| neg     | x          | number | negative x, ie: -x |
| *       | x y        | number | result of x * y |
| /       | x y        | number | result of x / y |
| %       | x y        | number | result of x % y |
| head    | x          | value  | first item in the list x or the first char in the string x|
| tail    | x          | list   | the list x without first element |
| fuse  | x y          | list  | Join into one list |
| pair  | x y          | list  | create a list with x and y |
| litr  | x            | number | convert string to number, ie: "5" => 5 |
| str   | x            | string | convert a number to a string, ie: 5 => "5" |
| words | x            | list   | Split a string into a list of words, split on space. |
| input | x            | string | Get input from stdin |
| print | x            | null   | Print x to stdout |
| #     | x y          | value  | Ignore value of x but still execute it, return value of y. Chain expressions together Used in comments for example |
| @     | x y          | value  | Ignore value of y but still excute Y, return value of x, when you don't want side effects to impact the expression. Chain expressions together. |   
| wrap  | x            | list   | Wrap x in a list, ie: [x] |
| empty |              | list   | Create an empty list, ie: [] |
| assert | info x      | bool   | Print info warning if x is not true |
| assert_eq | info x y | bool   | Print info warning if x and y are not equal |
| is_atom | x          | bool   | True if x is not list-like |
| is_str  | x          | bool   | True if x is a string |
| is_bool | x          | bool   | True if x is a bool |
| is_null | x          | bool   | True if x is null |
| len     | l          | number | Return the length of a list |
| skip    | n l        | list   | Return the n-th tail of the list l |
| nth     | n l        | value  | Return the n-th value of the list l |
| in      | x l        | bool   | Return true if x is in the list l |
| split   | x l        | list   | split the list l into 2 sublists at index x. returns: [[sublist1] [sublists2]] |


## Loops
As atto is a functional language it does not have a specific loop construct. Instead you create your own loop by using recursion.   

example of a for loop from 0 to 10
```
fn for10times i is
    # print str fuse "called with i=" str i
    if < i 10
        for10times + i 1
    null

fn main is
    for10times 0
```
The # is used to print stuff, while letting the *if* still be part of the expression chain.  
We also let the loop condition be a simple if expression.

example while loop
```
fn while condition is
    if = true condition
        # print "Continuing..."
        while = input "Continue [Y/N]? " "Y"
    null

fn main is
    while true
```
Here we create a continous recursion loop due to until user answers other than 'Y'. Note that we create the condition while evaluating the argument for the next while call on row 3 inside the while function.
  
  
  
  
-----

# The atto Interpreter
The section of the README is dedicated to the process from reading the source text to evaluating it results. It is not intended to be an exhaustive explaination. Just enogh to get an overview of how it works.

## Definitions
All language interpreters/compilers consists of some or all of these parts.
- **Lexer** (Tokenizer): Lexical analysis, splits the text into subparts and creates Tokens for each entry.
  - A token could be a string, number or a keyword for eaxmple.
- **Parser**: Makes semantic use of the tokens created by lexer. Creates an Abstract Syntax tree. 
  - Handles in what order an expression should be evaluated.
  - A number could be an argument in a functin call for example.
  - Makes sure that the grammar is consistent. For example that *fn* <fn_name> *is* <fn_body> is in that order.

- **Compiler**: Compiles the AST tree to bytecode or machinecode.
  - Converts the tree back to a flat list of instructions.
  -  that a virtual machine or the actual CPU can follow.
- **Bytecode** is used as input to a virtual machine, python, javscript etc. uses this technique.
  - Even java and C# uses bytecode as input to its internal VM although the bytecode is compiled ahead of time instead of each end every time as in a scripted language.
- **Machinecode** is read by a CPU as instructions. Targeting different CPUs requires different compilers.
  - ARM vs x86 has different instruction sets (ISA) as their respective instructions.
  - gcc, clang etc. have lexer, parser and compiler parts built into them. They produce a binary object that the CPU can later execute, even on a different machine as long as it has the same achitecture. If compiled for an operating system It must also match the operating system.

- **VM** (Virtual machine): A program that takes instructions on one form and converts them into machinecode that the CPU can understand.
  - All scripting- and some compiled languages use a VM. In scripting langages the VM is built into the interpreter. 
  - In python for example, the VM is part of cpython as well as lexer, parser and compiler. As they are part of the same process, you don't have to think of them as separate parts.
  - In Java the lexer, parser and compiler part is part of a program that is called a compiler that creates a java class object, which can be combined in a jar package. These are then, at later stage and on a different machine, executed by the Java Virtual Machine (JVM)

## Compiler pipeline i general
The process of converting sourcecode to doing something usefull.
```
Source-code
    |
  Lexer -> Parser -> Compiler -> VM(Bytecode) -> CPU
                          |
                           -> CPU (Machinecode)
```
As the bytecode can be the same regardless of execution enviroment, the compiler becomes much easier to implement in a VM specific language.

## This atto interpreter
It is possible to sidestep some of these steps to simplify an implementation. The reference implementation of atto does this, as well as this implementation of atto.
More specifically we sidestep the Compiler and go directly to the VM step.  

That means we evaluate direcly from the AST tree. This is slower that excuting from a flat list, but it makes the implementation simpler. This technique is call *Tree traversal* or *Walk the tree*.
  
In this specific python based variant of the atto language we actually use the python VM as en extra step before the programinstructions reaches the CPU. A consequence of writing the interpreter in python.  
  
The pipeline here in this atto implementation:
```
Source-code
    |
   Lexer -> Parser -> VM(atto) -> VM(python) -> CPU 
```

In this implementation I name the VM object: Interpreter, and store it in the file interpreter.py in the src directory.

Example src text used below:
```
fn add x y is
    + x y

fn main is
  print add 10 20
```

## Lexer
The Lexer is implemented in the file lexer.py, which can be found in the src directory. 

Lexer splits the source text and categorizes the token as an identifier, a number, a string or a keyword. If it can't make sense of that kind of token, it raises a AttoSyntaxError.  
  
It creates a Token for each part of the source text it finds. This token contains information of type, position in source text, reference to the lexer etc.
Further information, like the value in the source can be retrived by methods of this class.

Given example text above: gives a list of Tokens:
```
[
  Token(fn), 
  Token(add),
  Token(x),
  Token(y),
  Token(is), 
  Token(+), 
  Token(x),
  Token(y)
  Token(fn),
  Token(main),
  Token(print),
  Token(add),
  Token(10),
  Token(20)
]
```

## Parser
The Parser is implemented in the file parser.py, also located in the src directory. 

It first parses all function signatures, then passes each and every function body. This is called *late binding* and is needed as a call to a function at the bottom of a script can't be accessed before we actually parsed its signature. Therefore we apply late binding to our parser.  
  
*Sidenote:* In C and C++ we don't have late binding, we must therefore declare a function signature before we can use it.

If the Parser finds an error, such as function signatures does not match expected, it will generate an AttoSyntaxError.

### Func 
In order keep track of all functions in the program each function is stored in an object of the Func class. This object stores the parameter tokens, the name token for the function and the AST root node for the function body.

Given the input from lexer above it gives this output:
```
{
  "add": Func(Token(add), args=[Token(x), Token(y)], body= 
               ASTnode(+)
               /      \
         ASTnode(x)  ASTnode(y)
  ),
  "main": Func(Token(main), args=[], body=
              ASTnode(print)
               /
        ASTnode(call "add")
            |
        ASTnode(arg)
            |    \
            |    ASTnode(10)
        ASTnode(arg)
            |    \
          None   ASTnode(20)
  )
}
```
Each argument node stores it value as the right node and next argument as its left value. Sort of making a linked list of the tree for the arguments handling.

## Interpreter
The Interpreter is located in the file interpreter.py within the src directory.

This class sets up the interpreter pipeline and evaluates the AST tree. The actual evaluation is done recursively from within the *_eval_node* method. In that function we walk the AST tree and matches the token type associated with that AST node.  

It is implemented with a match - case structure that even though we do much in the same function, we structure each part within its respective case statement in python. Even python uses a big and lengthy eval loop, in cpython 3.9 it spans  [several thousand lines](https://github.com/python/cpython/blob/v3.9.25/Python/ceval.c#L920)

### Frame
As the interpreter calls functions it needs to send some information to the called function. That is done by use of a Frame object, which hold a list of arguments, the caller token and the called function's name token.  
  
This way a called function can get its argument values from the caller. Also if an AttoRuntimeError occurs, we can print a stack trace of the call-chain.

Each and every time a function is called a new Frame object is created, that means when a function calls itself recursively we also create a new Frame object.  
If anyone would want to optimize there is a techinque called *tail call optimization* that gets around that recursive inefficiency.

While excuting given eaxmple above, these Call frame will be created.
```
1. Frame(caller_frm=None, caller_tok=None, args: [], Func(main, ...))
2. Frame(caller_frm=main, caller_tok=Token("add"), args:[10, 20], Func(add, ...))
3. Frame(caller_frm=add, caller_tok=Token("+"), args:[10, 20], Func(+, ...)) 

# Remember that + is actually a function within corelib.
```

This call-chain is used in AttoSyntaxError to generate a traceback, for easier debugging.

### Output of example execution
The output of given example will be: ```30``` printed to stdout.

## Summary
The atto language implementation described here is a simple *Tree Traversal* implementation. As the syntax of the language is very simple, it also makes the internal parts of this project very simple. 

However simple It still contains a Lexer, Parser and a VM to execute the AST parse tree. The Vm is implemented in the class Interpreter.

Given this implementations simple internals, this should give anyone interested a fairly straightforward view about how language engines works internally.
