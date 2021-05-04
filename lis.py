#!/usr/bin/env python

# http://norvig.com/lispy.html

Symbol = str
List = list
Number = (int, float)


def tokenize(chars):
    "Convert input characters to a list of output tokens"
    return chars.replace("(", " ( ").replace(")", " ) ").split()


def read_from_tokens(tokens):
    "Build an expression from a token list "
    if len(tokens) == 0:
        raise SyntaxError("unexpected EOF")
    token = tokens.pop(0)
    if "(" == token:
        L = []
        while tokens[0] != ")":
            L.append(read_from_tokens(tokens))
        tokens.pop(0)  # pop ')'
        return L
    elif ")" == token:
        raise SyntaxError("unexpected ')'")
    else:
        return atom(token)


def atom(token):
    "build a number or fallback to a symbol"
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


def parse(program):
    return read_from_tokens(tokenize(program))


def standard_env():
    import math, operator as op

    env = Env()
    env.update(vars(math))
    env.update(
        {
            "+": op.add,
            "-": op.sub,
            "*": op.mul,
            "/": op.truediv,
            ">": op.gt,
            "<": op.lt,
            ">=": op.ge,
            "<=": op.le,
            "=": op.eq,
            "abs": abs,
            "append": op.add,
            "apply": lambda fn, *x: fn(*x),
            "begin": lambda *x: x[-1],
            "first": lambda x: x[0],
            "tail": lambda x: x[1:],
            "cons": lambda x, y: [x] + list(y),
            "eq?": op.is_,
            "equal?": op.eq,
            "length": len,
            "list": lambda *x: list(x),
            "list?": lambda x: isinstance(x, list),
            "map": map,
            "max": max,
            "min": min,
            "not": op.not_,
            "null?": lambda x: x == [],
            "number?": lambda x: isinstance(x, Number),
            "procedure?": callable,
            "round": round,
            "symbol?": lambda x: isinstance(x, Symbol),
        }
    )
    return env


def repl(prompt="~> "):
    while True:
        val = evaL(parse(input(prompt)))
        if val is not None:
            print(schemestr(val))


def schemestr(exp):
    "convert a python object into a scheme readable string"
    if isinstance(exp, list):
        return "(" + " ".join(map(schemestr, exp)) + ")"
    else:
        return str(exp)


class Procedure(object):
    def __init__(self, params, body, env):
        self.params, self.body, self.env = params, body, env

    def __call__(self, *args):
        # build environment with proc arguments matched to parameters
        return evaL(self.body, Env(self.params, args, self.env))


class Env(dict):
    "An environment: a dict of var:vals with reference to outer Envs "

    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer

    def find(self, var):
        return self if (var in self) else self.outer.find(var)


global_env = standard_env()


def evaL(x, env=global_env):
    if isinstance(x, Symbol):  # variable reference
        return env.find(x)[x]
    elif not isinstance(x, List):  # const literal
        return x
    elif x[0] == "quote":  # (quote exp)
        (_, exp) = x
        return exp
    elif x[0] == "if":  # (if test conseq alt)
        (_, test, conseq, alt) = x
        exp = conseq if evaL(test, env) else alt
        return evaL(exp, env)
    elif x[0] == "define":  # (define var exp)
        (_, var, exp) = x
        env[var] = evaL(exp, env)
    elif x[0] == "set!":  # (set! var exp)
        (_, var, exp) = x
        env.find(var)[var] = evaL(exp, env)
    elif x[0] == "lambda":  # (lambda (var...) body)
        (_, params, body) = x
        return Procedure(params, body, env)
    else:  # (proc arg...)
        proc = evaL(x[0], env)
        args = [evaL(arg, env) for arg in x[1:]]
        return proc(*args)
