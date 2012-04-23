import re
import sys
import traceback
from io import StringIO
from ucb import main, trace
from scheme_tokens import *
from scheme_utils import *
from scheme_primitives import *

from random import choice
from types import GeneratorType

# Name of file containing Scheme definitions.
SCHEME_PRELUDE_FILE = "scheme_prelude.scm"

# Name of file containing prompts to use for random prompt generation.
PROMPT_FILE = "prompts"

class PrimitiveFunction(SchemeValue):
    """A Scheme function implemented directly in Python."""

    def __init__(self, func):
        """The function that applies Python function FUNC to its operands."""
        self.func = func

    def type_name(self):
        return "primitive procedure"

    def apply_step(self, args, evaluation):
        try:
            evaluation.set_value(self.func(*args))
        except TypeError:
            raise SchemeError("{0} received an incorrect number of arguments".format(repr(self.func)))

    def __repr__(self):
        return "PrimitiveFunction({0})".format(repr(self.func))

class LambdaFunction(SchemeValue):
    """A function defined by lambda expression or the complex define form."""

    def __init__(self, formals, body, env):
        """A function whose formal parameter list is FORMALS (in Scheme format),
        whose body is the single Scheme expression BODY, and whose environment
        is the EnvironFrame ENV.  A lambda expression containing multiple expressions,
        such as (lambda (x) (set! y x) (+ x 1)) can be handled by
        using (begin (set! y x) (+ x 1)) as the body."""
        self.formals = formals
        self.body = body
        self.env = env

    def type_name(self):
        return "closure"

    def apply_step(self, args, evaluation):
        evaluation.set_expr(self.body, self.env.make_call_frame(self.formals, args))

    def write(self, out):
        print("<(lambda ", file=out, end='')
        self.formals.write(out)
        print(" ", end='', file=out)
        self.body.write(out)
        print("), {0}>".format(repr(self.env)), file=out, end='')

    def __repr__(self):
        return "LambdaFunction({0}, {1}, {2})" \
               .format(repr(self.formals), repr(self.body), repr(self.env))

## LambdaFunction Utility Function ##
def make_single_body(exprs):
    """Utility function to make a single Scheme expression for the
    LambdaFunction class from multiple individual Scheme
    expressions. Returns the unchanged single expression if there is
    only one such expression."""
    if exprs.nullp() or exprs.cdr.nullp():
        return exprs.car
    else:
        return Pair(Evaluation._BEGIN_SYM, exprs)

class EnvironFrame:
    """An environment frame, representing a mapping from Scheme symbols to
    Scheme values, possibly enclosed within another frame."""

    def __init__(self, enclosing):
        """An empty frame that is attached to the frame ENCLOSING."""
        self.inner = {}
        self.enclosing = enclosing

    def __getitem__(self, sym):
        return self.find(sym).inner[sym]

    def __setitem__(self, sym, val):
        self.find(sym).inner[sym] = val

    def __repr__(self):
        if self.enclosing is None:
            return "<Global frame at {0}>".format(hex(id(self)))
        else: 
            return "<Frame at {0} --> {1}>".format(hex(id(self)),
                                                   repr(self.enclosing))

    def find(self, sym):
        """The environment frame at or enclosing SELF that defined SYM.  It
        is an error if it does not exist."""
        e = self
        while e is not None:
            if sym in e.inner:
                return e
            e = e.enclosing
        raise SchemeError("unknown identifier: {0}".format(str(sym)))

    def make_call_frame(self, formals, vals):
        """A new local frame attached to SELF in which the symbols in
        the Scheme formal parameter list FORMALS are bound to the
        Scheme values in the Python list VALS.  FORMALS has either of the
        formats allowed by the Evaluation.check_formals method.  If
        the last cdr in FORMALS is a null list (that is, if FORMALS is
        an ordinary Scheme list), then the number of formals must be the same
        as the number of VALS, and each symbol in FORMALS is bound to the
        corresponding value in VALS.  If the last cdr in FORMALS is a
        symbol, then the number of values in VALS  must be at least as large as
        the number of preceding ("normal") formal symbols, and the last
        formal symbol is bound to a Scheme list containing the remaining
        values in VALS (which may be 0)."""

        # FORMALS is a Scheme list (last one could be pair), VALS is a Python list

        # Error checking
        if scm_listp(formals) and len(vals) > formals.length():
            raise SchemeError("too many arguments provided")

        # Defining formals
        call_frame = EnvironFrame(self)
        i = 0
        while formals.pairp():
            try:
                call_frame.define(formals.car,vals[i])
            except IndexError:
                raise SchemeError("too few arguments provided")
            formals = formals.cdr
            i += 1
        if formals.symbolp():
            rest = make_list(*vals[i:])
            call_frame.define(formals,rest)

        return call_frame

    def define(self, sym, val):
        """Define Scheme symbol SYM to have value VAL in SELF."""
        self.inner[sym] = val

class Evaluation:
    """An Evaluation represents the information needed to evaluate an
    expression: the expression and the environment in which it is to be
    evaluated.  The step method performs at least part of the evaluation of
    the expression, either leaving behind the final value, or else another
    intermediate expression and environment to be further evaluated."""

    def __init__(self, expr, env):
        """An evaluation of EXPR in the environment ENV."""
        self.expr = expr
        self.env = env
        self.value = None

    def set_value(self, value):
        """Set the value of SELF to VALUE, completing the evaluation."""
        assert value is not None
        self.expr = None
        self.value = value

    def set_expr(self, expr, env = None):
        """Replace SELF's expression with EXPR.  If ENV is non-null, replace
        the environment in which EXPR is being evaluated with ENV."""
        self.expr = expr
        if env is not None:
            self.env = env

    def evaluated(self):
        """True iff this evaluation is finished."""
        return self.value is not None

    def step(self):
        """Either complete SELF's computation, causing all remaining
        side effects and producing a value, or else partially perform the
        remaining computation, leaving SELF with an expression and environment
        that denote the remaining computation."""
        expr = self.expr
        if expr.symbolp():
            # Exception for failed lookup defined in EnvironFrame
            value = self.env[expr]
            self.set_value(value)
        elif expr.atomp():
            self.set_value(expr)
        elif not scm_listp(expr):
            raise SchemeError("malformed list: {0}".format(str(self.expr)))
        else:
            op = expr.car
            if op.symbolp():
                Evaluation.SPECIAL_FORMS.get(op, Evaluation.do_call_form)(self)
            else:
                self.do_call_form()

    def full_eval(self, expr, env = None):
        """The value of EXPR when evaluated in environment ENV (SELF.env by
        default."""
        return Evaluation(expr, env or self.env).step_to_value()

    def step_to_value(self):
        """Perform evaluation steps on SELF until a value is reached."""
        while not self.evaluated():
            self.step()
        return self.value

    # Special forms.  Each of these methods is called when
    # SELF.expr apparently contains the kind of special form the method
    # handles.  It checks the syntactic validity of the form, and partially 
    # evaluates it, either leaving the final value or an expression
    # that carries out the rest of the computation.

    def do_quote_form(self):
        self.check_form(2, 2)
        self.set_value(self.expr.cdr.car)

    def do_lambda_form(self):
        self.check_form(3)
        formals = self.expr.nth(1)  # gets the arguments
        self.check_formals(formals)
        fn = LambdaFunction(formals,make_single_body(self.expr.cdr.cdr),self.env)
        self.set_expr(fn)

    # To handle tail-recursion for conditionals, make sure the final
    # result of the conditional uses set_expr as opposed to set_value

    def do_if_form(self):
        self.check_form(3, 4)
        cond = self.full_eval(self.expr.nth(1))
        if cond:
            ans = self.expr.nth(2)
        else:
            if self.expr.length() == 3:
                ans = UNSPEC
            else:
                ans = self.expr.nth(3)
        self.set_expr(ans)

    def do_and_form(self):
        self.check_form(1)

        if self.expr.length() == 1:
            self.set_value(TRUE)
            return

        rest_expr = self.expr.cdr
        while rest_expr.cdr.pairp():
            if not self.full_eval(rest_expr.car):
                self.set_expr(rest_expr.car)
                return
            rest_expr = rest_expr.cdr
        self.set_expr(rest_expr.car)

    def do_or_form(self):
        self.check_form(1)

        if self.expr.length() == 1:
            self.set_value(FALSE)
            return

        rest_expr = self.expr.cdr
        while rest_expr.cdr.pairp():
            if self.full_eval(rest_expr.car):
                self.set_expr(rest_expr.car)
                return
            rest_expr = rest_expr.cdr
        self.set_expr(rest_expr.car)

    def do_cond_form(self):
        self.check_form(1)
        clauses = self.expr.cdr

        while clauses.pairp():
            clause = clauses.car
            self.check_form(1, expr = clause)

            # Determining truthfulness of test expression
            if clause.car is self._ELSE_SYM:
                try:
                    self.check_form(2, expr = clause)
                except SchemeError:
                    raise SchemeError("badly formed else clause")
                if not clauses.cdr.nullp():
                    raise SchemeError("else clause must be the last clause in cond")
                test = TRUE
            else:
                test = self.full_eval(clause.car)

            # if true, evaluate expression sequence
            if test:
                if clause.length() == 1:
                    self.set_value(test)
                elif clause.cdr.car is self._ARROW_SYM:
                    if clause.cdr.cdr.nullp():
                        raise SchemeError("no function specified for 'cond'")
                    self.set_expr(make_list(clause.nth(2), test))
                else:
                    expr_seq = clause.cdr
                    self.evaluate_expr_seq_and_set_expr_as_last(expr_seq)
                return
            clauses = clauses.cdr

        self.set_value(UNSPEC)

    def do_set_bang_form(self):
        self.check_form(3, 3)
        to_set = self.expr.nth(1)
        new_value = self.full_eval(self.expr.nth(2))

        if not to_set.symbolp():
            raise SchemeError("first argument is not a symbol!")

        # Undefined symbol handled in find
        e = self.env.find(to_set)
        e.define(to_set, new_value)
        self.set_value(UNSPEC)

    def do_define_form(self):
        self.check_form(3)
        target = self.expr.nth(1)

        # Defining variables (symbols)
        if target.symbolp():
            self.check_form(3,3)
            value = self.expr.nth(2)
            self.env.define(target,self.full_eval(value))
            self.set_value(UNSPEC)

        elif not target.pairp():
            raise SchemeError("bad argument to define")

        # Defining functions
        else:
            self.check_formals(target.cdr)
            self.env.define(target.car, self.full_eval(LambdaFunction(target.cdr,make_single_body(self.expr.cdr.cdr), self.env)))
            self.set_value(UNSPEC)

    def do_begin_form(self):
        self.check_form(2)
        for k in range(1, self.expr.length()-1):
            self.full_eval(self.expr.nth(k))
        self.set_expr(self.expr.nth(self.expr.length()-1))

    def do_let_form(self):
        self.check_form(3)
        bindings = self.expr.cdr.car  # of form ((VAR1 INIT1)(VAR2 INIT2)...)
        exprs = self.expr.cdr.cdr  # of form (BODY1)(BODY2)...

        # Check that bindings is of the correct form
        try:
            self.check_form(0, expr = bindings)
        except SchemeError:
            raise SchemeError("badly formed bindings - incorrect number of subforms")
        
        # Create new env frame and bindings
        symbols = NULL
        vals = []
        while bindings.pairp():
            binding = bindings.car

            # Check that each binding is in the form (symbol value)
            try:
                self.check_form(2, 2, expr = binding)
            except SchemeError:
                raise SchemeError("badly formed binding - incorrect binding format")

            symbols = Pair(binding.car,symbols)
            vals.append(self.full_eval(binding.cdr.car))
            bindings = bindings.cdr
        let_frame = self.env.make_call_frame(symbols, list(reversed(vals)))

        # Evaluating the body in new frame
        for _ in range(0, exprs.length()-1):
            self.full_eval(exprs.car, let_frame)
            exprs = exprs.cdr
        self.set_expr(exprs.car, let_frame)

    # Extra credit
    def do_let_star_form(self):
        self.check_form(3)
        bindings = self.expr.cdr.car  # of form ((VAR1 INIT1)(VAR2 INIT2)...)
        exprs = self.expr.cdr.cdr  # of form (BODY1)(BODY2)...

        # Check that bindings is of the correct form
        try:
            self.check_form(0, expr = bindings)
        except SchemeError:
            raise SchemeError("badly formed bindings - incorrect number of subforms")
        
        # Create new EMPTY env frame
        let_frame = self.env.make_call_frame(NULL,[])
        while bindings.pairp():
            binding = bindings.car

            # Check that each binding is in the form (symbol value)
            try:
                self.check_form(2, 2, expr = binding)
            except SchemeError:
                raise SchemeError("badly formed binding - incorrect binding format")

            let_frame.define(binding.car,self.full_eval(binding.cdr.car, let_frame))
            bindings = bindings.cdr

        # Evaluating the body in new frame
        for _ in range(0, exprs.length()-1):
            self.full_eval(exprs.car, let_frame)
            exprs = exprs.cdr
        self.set_expr(exprs.car, let_frame)

    def do_case_form(self):
        self.check_form(2)
        k = self.full_eval(self.expr.nth(1))
        clauses = self.expr.cdr.cdr

        while clauses.pairp():
            clause = clauses.car
            data = clause.car
            # if empty expr_seq but still matches, then defaults to TRUE
            expr_seq = clause.cdr

            # if an else clause
            if data is self._ELSE_SYM:
                try:
                    self.check_form(2, expr = clause)
                except SchemeError:
                    raise SchemeError("badly formed else clause")
                if not clauses.cdr.nullp():
                    raise SchemeError("else clause must be the last clause in cond")
                self.evaluate_expr_seq_and_set_expr_as_last(expr_seq, TRUE)
                return

            # if one piece of data
            elif data.atomp():
                if k.eqvp(data):
                    self.evaluate_expr_seq_and_set_expr_as_last(expr_seq, TRUE)
                    return

            # otherwise check each datum
            while data.pairp():
                datum = data.car
                if k.eqvp(datum):
                    self.evaluate_expr_seq_and_set_expr_as_last(expr_seq, TRUE)
                    return
                data = data.cdr
                
            clauses = clauses.cdr

        self.set_value(UNSPEC)

    # Symbols that are used in special forms.

    _AND_SYM = Symbol.string_to_symbol("and")
    _ARROW_SYM = Symbol.string_to_symbol("=>")
    _BEGIN_SYM = Symbol.string_to_symbol("begin")
    _CASE_SYM = Symbol.string_to_symbol("case")
    _COND_SYM = Symbol.string_to_symbol("cond")
    _DEFINE_SYM = Symbol.string_to_symbol("define")
    _ELSE_SYM = Symbol.string_to_symbol("else")
    _IF_SYM = Symbol.string_to_symbol("if")
    _LAMBDA_SYM = Symbol.string_to_symbol("lambda")
    _LET_SYM = Symbol.string_to_symbol("let")
    _LET_STAR_SYM = Symbol.string_to_symbol("let*")
    _OR_SYM = Symbol.string_to_symbol("or")
    _QUOTE_SYM = Symbol.string_to_symbol("quote")
    _SET_BANG_SYM = Symbol.string_to_symbol("set!")

    # Mapping of symbols that introduce special forms to the methods that
    # handle the forms.
    SPECIAL_FORMS = {
        _AND_SYM :     do_and_form,
        _BEGIN_SYM :   do_begin_form,
        _CASE_SYM :    do_case_form,
        _COND_SYM :    do_cond_form,
        _DEFINE_SYM :  do_define_form,
        _IF_SYM :      do_if_form,
        _LAMBDA_SYM :  do_lambda_form,
        _LET_SYM :     do_let_form,
        _LET_STAR_SYM: do_let_star_form,
        _OR_SYM :      do_or_form,
        _QUOTE_SYM  :  do_quote_form,
        _SET_BANG_SYM: do_set_bang_form,
    }

    # Function calls

    def do_call_form(self):
        self.check_form(1)
        op = self.full_eval(self.expr.car)
        args = []
        rest = self.expr.cdr
        # Slightly optimized to not traverse the expression multiple times
        while not rest.nullp():
            args.append(self.full_eval(rest.car))
            rest = rest.cdr
        op.apply_step(args, self)

    # Utility methods for checking the structure of Scheme values that
    # represent programs.

    def check_form(self, min, max = None, expr = None):
        """Check EXPR (default SELF.expr) is a proper list whose length is
        at least MIN and no more than MAX (default: no maximum). Raises
        a SchemeError if this is not the case."""
        if expr is None:
            expr = self.expr
        # Checks that the expr is a list
        if not scm_listp(expr):
            raise SchemeError("badly formed expression")
        L = expr.length()
        if L < min:
            raise SchemeError("too few operands in form")
        elif max is not None and L > max:
            raise SchemeError("too many operands in form")

    @staticmethod
    def check_formals(formal_list):
        """Check that FORMAL_LIST is a valid parameter list having either 
        the form (sym1 sym2 ... symn) or else (sym1 sym2 ... symn . symrest),
        where each symx is a distinct symbol."""
        distinct = set()
        while not formal_list.nullp():
            if formal_list.pairp():
                item_to_check = formal_list.car
            else:
                item_to_check = formal_list

            if not item_to_check.symbolp():
                raise SchemeError("argument #{0} is not a valid symbol".format(index))
            elif item_to_check in distinct:
                raise SchemeError("formal parameters provided are not distinct")

            if item_to_check is formal_list:
                break
            else:
                distinct.add(item_to_check)
                formal_list = formal_list.cdr

    def evaluate_expr_seq_and_set_expr_as_last(self, expr_seq, default=UNSPEC):
        """Utility method for do_cond_form and do_case_form. Evaluates
        all of the expressions within expr_seq, then sets the
        expression of the evaluation as the last of these expressions."""
        # Loops to evaluate possible returns first so it
        # checks for possible SchemeErrors
        if expr_seq.nullp():
            self.set_expr(default)
            return
        while expr_seq.cdr.pairp():
            self.full_eval(expr_seq.car)
            expr_seq = expr_seq.cdr
        # Returns the last of the options
        self.set_expr(expr_seq.car)

def scm_eval(sexpr):
    # To begin with, this function simply returns SEXPR unchanged, without
    # doing any evaluation.  This allows you to test your solution to
    # problem 1: the interpreter will just echo all the expressions in your
    # input when you type
    #    python3 scheme.py tests.scm
    # (or other file full of Scheme expressions).  When you are finished
    # with Problem 1, replace the return statement below with 
    #    return Evaluation(sexpr, the_global_environment).step_to_value()
    # which is what evaluation is supposed to do.

    return Evaluation(sexpr, the_global_environment).step_to_value()

def scm_apply(func, arg0, *other_args):
    """If OTHER_ARGS is empty, apply the function value FUNC to the argument 
    list in ARG0 (a Scheme list).  Otherwise, the values of ARG0 and all but
    the last value in OTHER_ARGS are first added (with scm_cons) to
    the beginning of the last argument in OTHER_ARGS (which must be 
    a Scheme list), and then passed to the value of FUNC."""
    if other_args:
        check_type(other_args[-1], scm_listp, len(other_args), 'apply')
        args = [arg0]
        for i in range(len(other_args)-1):
            args.append(other_args[i])
        rest = other_args[-1]
    else:
        check_type(arg0, scm_listp, 0, 'apply')
        args = []
        rest = arg0

    while not rest.nullp():
        args.append(rest.car)
        rest = rest.cdr
    
    evaluation = Evaluation(None, None)
    func.apply_step(args, evaluation)
    return evaluation.step_to_value()


def call_with_input_file(filename, proc):
    """Temporarily set the current input port to the file named by FILENAME,
    (a string) and call PROC.  Always restores the input port when done."""
    with open(filename) as inp:
        call_with_input_source(inp, proc)

def call_with_input_source(source, proc):
    """Temporarily set the current input port to read lines from the
    SOURCE (an iterator returning lines or a string).  Always restores
    the input port when done."""
    global input_port
    input_port0 = input_port
    try:
        input_port = Buffer(tokenize_lines(source))
        proc()
    finally:
        input_port = input_port0
    
def read_eval_print(prompt = None):
    """Read and evaluate from the current input port until the end of file.
    If PROMPT is not None, use it to prompt for input and print values of
    each expression."""
    gen_string = isinstance(prompt, GeneratorType)
    while True:
        try:
            if gen_string:
                print(next(prompt), end = " ")
            elif prompt is not None:
                print(prompt, end = "")
            sys.stdout.flush()
            expr = scm_read()  # Get the expression as objects
            if expr is THE_EOF_OBJECT:
                return
            val = scm_eval(expr)   
            if prompt is not None and val is not UNSPEC:
                scm_write(val)
                scm_newline()
        except SchemeError as exc:
            if not exc.args[0]:
                print("Error", file=sys.stderr)
            else:
                print("Error: {0}".format(exc.args[0]), file=sys.stderr)
            sys.stderr.flush()

def scm_read():
    def read_tail():
        """Assuming that input is positioned inside a Scheme list or pair,
        immediately before a final parenthesis or another item in the list,
        return the remainder of the list from that point.  Thus, returns
        (2 3) when positioned at the carat in "(1 ^ 2 3)", returns
        () when positioned at the carat in "(1 2 3 ^ )", and returns
        the pair (2 . 3) when positioned at the carat in (1 ^ 2 . 3)."""
        if input_port.current is None:
            raise SchemeError("unexpected EOF")
        syntax, val = input_port.current
        if syntax == ")":
            input_port.pop()
            return NULL
        elif syntax == ".":
            input_port.pop()
            # to recognize malformed pairs
            rest = read_tail()
            if rest.nullp() or not rest.cdr.nullp():
                raise SchemeError("malformed pair")
            else:
                return rest.car
        else:
            return Pair(scm_read(), read_tail())

    if input_port.current is None:
        return THE_EOF_OBJECT

    syntax, val = input_port.pop()

    if syntax == NUMERAL:
        return Number(val)
    elif syntax == BOOLEAN:
        return boolify(val)
    elif syntax == SYMBOL:
        return Symbol.string_to_symbol(val)
    elif syntax == "'":
        return make_list(Evaluation._QUOTE_SYM, scm_read())
    elif syntax == "(":
        return read_tail()
    else:
        raise SchemeError("unexpected token: {0}".format(repr(val)))

def scm_load(sym):
    check_type(sym, scm_symbolp, 0, "load")
    call_with_input_file(str(sym), read_eval_print)
    return UNSPEC

##
## Initialization
##

_PRIMITIVES = (
    ("eqv?", scm_eqvp),
    ("eq?", scm_eqp),
    ("equal?", scm_equalp),
    ("atom?", scm_atomp),

    ("pair?", scm_pairp),
    ("null?", scm_nullp),
    ("list?", scm_listp),
    ("cons", scm_cons),
    ("car", scm_car),
    ("cdr", scm_cdr),
    ("length", scm_length),
    ("set-car!", scm_set_car),
    ("set-cdr!", scm_set_cdr),
    ("list", scm_list),
    ("append", scm_append),

    ("integer?", scm_integerp),
    ("+", scm_add),
    ("-", scm_sub),
    ("*", scm_mul),
    ("/", scm_div),
    ("quotient", scm_quo),
    ("modulo", scm_modulo),
    ("remainder", scm_remainder),
    ("floor", scm_floor),
    ("ceil", scm_ceil),
    ("<", scm_lt),
    (">", scm_gt),
    ("=", scm_eq),
    ("<=", scm_le),
    (">=", scm_ge),

    ("boolean?", scm_booleanp),
    ("not", scm_not),
    ("symbol?", scm_symbolp),

    ("write", scm_write),
    ("display", scm_display),
    ("newline", scm_newline),
    ("read", scm_read),
    ("load", scm_load),

    ("eval", scm_eval),
    ("apply", scm_apply),

    ("error", scm_error),
    (["exit", "bye"], scm_exit),

    ("word", sscm_word),
    ("first", sscm_first),
    (["bf", "butfirst"], sscm_butfirst),
    ("last", sscm_last),
    (["bl", "butlast"], sscm_butlast),
    (["sentence", "se"], sscm_sentence),

    (['forward', 'fd'], tscm_forward),
    (['backward', 'back', 'bk'], tscm_backward),
    (['right', 'rt'], tscm_right),
    (['left', 'lt'], tscm_left),
    ('circle', tscm_circle),
    (['setpos', 'setposition', 'goto'], tscm_setposition),
    (['seth', 'setheading'], tscm_setheading),
    (['penup', 'pu'], tscm_penup),
    (['pendown', 'pd'], tscm_pendown),
    (['showturtle', 'st'], tscm_showturtle),
    (['hideturtle', 'ht'], tscm_hideturtle),
    ('clear', tscm_clear),
    ('color', tscm_color),
    ('begin_fill', tscm_begin_fill),
    ('end_fill', tscm_end_fill),
    ('exitonclick', tscm_exitonclick),
    ('speed', tscm_speed),
)

def define_primitives(frame, bindings):
    """Enter each of the (name, function) bindings in BINDINGS into FRAME,
    an environment frame."""
    for names, func in bindings:
        if type(names) is str:
            names = (names,)
        for name in names:
            frame.define(Symbol.string_to_symbol(name),
                         PrimitiveFunction(func))

def create_global_environment():
    """Initialize the_global_environment to a fresh environment defining the
    predefined names."""
    global the_global_environment

    the_global_environment = EnvironFrame(None)
    
    # Uncomment the following line after you finish with Problem 4.
    scm_load(Symbol.string_to_symbol(SCHEME_PRELUDE_FILE))
    define_primitives(the_global_environment, _PRIMITIVES)

def gen_prompt_string():
    with open(PROMPT_FILE) as prompt_file:
        prompt_strings = prompt_file.read().split('\n')
    while True:
        yield choice(prompt_strings)

input_port = None

@main
def run(*argv):
    global input_port

    if argv:
        try:
            input_file = open(argv[0])
        except IOError as exc:
            print("could not open {0}: {1}".format(argv[0], exc.args[0]),
                  file=sys.stderr)
            sys.exit(1)
    else:
        input_file = sys.stdin
        
    input_port = Buffer(tokenize_lines(input_file))
    create_global_environment()
    # Change to customize prompt string
    read_eval_print(gen_prompt_string())

