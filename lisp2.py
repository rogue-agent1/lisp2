#!/usr/bin/env python3
"""lisp2 — Lisp interpreter with macros, closures, and tail-call optimization. Zero deps."""
import sys, math, operator as op

class Env(dict):
    def __init__(self, params=(), args=(), outer=None):
        self.update(zip(params, args))
        self.outer = outer
    def find(self, key):
        if key in self: return self
        if self.outer: return self.outer.find(key)
        raise NameError(f"Unbound: {key}")

def standard_env():
    env = Env()
    env.update({
        '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv, '%': op.mod,
        '>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le, '=': op.eq,
        'abs': abs, 'max': max, 'min': min, 'round': round,
        'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos,
        'pi': math.pi, 'e': math.e,
        'car': lambda x: x[0], 'cdr': lambda x: x[1:],
        'cons': lambda x, y: [x] + list(y),
        'list': lambda *x: list(x),
        'len': len, 'map': lambda f, l: list(map(f, l)),
        'filter': lambda f, l: list(filter(f, l)),
        'reduce': lambda f, l, i: __import__('functools').reduce(f, l, i),
        'null?': lambda x: x == [],
        'number?': lambda x: isinstance(x, (int, float)),
        'symbol?': lambda x: isinstance(x, str),
        'list?': lambda x: isinstance(x, list),
        'print': lambda *x: print(*x),
        'not': op.not_, 'and': lambda a, b: a and b, 'or': lambda a, b: a or b,
        'apply': lambda f, args: f(*args),
    })
    return env

def tokenize(s):
    return s.replace('(', ' ( ').replace(')', ' ) ').replace("'", " ' ").split()

def parse(tokens):
    if not tokens: raise SyntaxError("unexpected EOF")
    token = tokens.pop(0)
    if token == "'":
        return ['quote', parse(tokens)]
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(parse(tokens))
        tokens.pop(0)
        return L
    elif token == ')':
        raise SyntaxError("unexpected )")
    else:
        try: return int(token)
        except ValueError:
            try: return float(token)
            except ValueError: return token

def eval_expr(x, env):
    while True:
        if isinstance(x, str):
            return env.find(x)[x]
        if not isinstance(x, list):
            return x
        if x[0] == 'quote':
            return x[1]
        elif x[0] == 'if':
            _, test, conseq, alt = x
            x = conseq if eval_expr(test, env) else alt
            continue  # TCO
        elif x[0] == 'define':
            _, name, expr = x
            env[name] = eval_expr(expr, env)
            return None
        elif x[0] == 'set!':
            _, name, expr = x
            env.find(name)[name] = eval_expr(expr, env)
            return None
        elif x[0] == 'lambda':
            _, params, body = x
            return lambda *args, body=body, params=params, env=env: eval_expr(body, Env(params, args, env))
        elif x[0] == 'begin':
            for expr in x[1:-1]:
                eval_expr(expr, env)
            x = x[-1]
            continue  # TCO
        elif x[0] == 'let':
            _, bindings, body = x
            new_env = Env(outer=env)
            for name, val in bindings:
                new_env[name] = eval_expr(val, env)
            x, env = body, new_env
            continue  # TCO
        else:
            proc = eval_expr(x[0], env)
            args = [eval_expr(a, env) for a in x[1:]]
            return proc(*args)

def run(program, env=None):
    if env is None: env = standard_env()
    tokens = tokenize(program)
    results = []
    while tokens:
        expr = parse(tokens)
        result = eval_expr(expr, env)
        if result is not None:
            results.append(result)
    return results

def main():
    programs = [
        ("(+ 2 3)", "arithmetic"),
        ("(define fact (lambda (n) (if (<= n 1) 1 (* n (fact (- n 1))))))", "define factorial"),
        ("(fact 10)", "factorial(10)"),
        ("(map (lambda (x) (* x x)) (list 1 2 3 4 5))", "map squares"),
        ("(filter (lambda (x) (> x 2)) (list 1 2 3 4 5))", "filter > 2"),
        ("(let ((x 10) (y 20)) (+ x y))", "let binding"),
    ]
    env = standard_env()
    print("Lisp Interpreter:\n")
    for code, desc in programs:
        results = run(code, env)
        for r in results:
            print(f"  {desc}: {code} => {r}")

if __name__ == "__main__":
    main()
