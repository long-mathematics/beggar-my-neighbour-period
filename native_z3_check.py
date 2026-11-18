#!/usr/bin/env python3
"""Independent native Z3 backend for the minimum-period finite exclusion.

Uses ctypes to call libz3.so's C API (Z3_eval_smtlib2_string), without the
z3-solver Python wheel. The ordinary-gap constraints and face itineraries are
imported from prove_minimum.py; their arithmetic AST is translated to SMT-LIB.
The separate native solver path provides an alternate verification backend,
not an independent derivation of the constraint model.

Usage: python native_z3_check.py [--lib /path/to/libz3.so.4] [--json out.json]
"""
from __future__ import annotations
import argparse, ctypes, importlib.util, json, sys, time, types
from pathlib import Path

class Expr:
    __slots__=('s',)
    def __init__(self,s): self.s=s
    def __add__(self,b): return op('+',self,b)
    def __radd__(self,a): return op('+',a,self)
    def __sub__(self,b): return op('-',self,b)
    def __rsub__(self,a): return op('-',a,self)
    def __mul__(self,b): return op('*',self,b)
    def __rmul__(self,a): return op('*',a,self)
    def __lt__(self,b): return op('<',self,b)
    def __le__(self,b): return op('<=',self,b)
    def __gt__(self,b): return op('>',self,b)
    def __ge__(self,b): return op('>=',self,b)
    def __eq__(self,b): return op('=',self,b)
    def __ne__(self,b): return op('distinct',self,b)
    def __mod__(self,b): return op('mod',self,b)
    def __bool__(self): raise TypeError('Cannot coerce symbolic expression to bool')
    def eq(self,other): return self.s == other.s
    __hash__=None
    def __repr__(self): return self.s

def enc(e):
    if isinstance(e,Expr): return e.s
    if isinstance(e,bool): return 'true' if e else 'false'
    if isinstance(e,int): return str(e) if e>=0 else f'(- {-e})'
    raise TypeError(f'Unexpected term {e!r}')

def op(tag,*es):return Expr(f'({tag} {" ".join(enc(e) for e in es)})')
def And(*es):return op('and',*es)
def Or(*es):return op('or',*es)
def Not(e):return op('not',e)
def Sum(es):return op('+',*list(es)) if len(es) else Expr('0')
def If(cond,a,b):return op('ite',cond,a,b)
def Int(name):return Expr(name)
def IntVal(value):return Expr(enc(value))

# This shim exposes exactly the subset of Z3Py used in the lower bound model.
shim=types.ModuleType('z3')
for name in ('And','Or','Not','Sum','If','Int','IntVal'):
    setattr(shim,name,globals()[name])

class NativeLib:
    def __init__(self,path):
        self.z=ctypes.CDLL(path)
        z=self.z
        z.Z3_mk_config.restype=ctypes.c_void_p
        z.Z3_mk_context.argtypes=[ctypes.c_void_p];z.Z3_mk_context.restype=ctypes.c_void_p
        z.Z3_eval_smtlib2_string.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
        z.Z3_eval_smtlib2_string.restype=ctypes.c_char_p
        z.Z3_del_context.argtypes=[ctypes.c_void_p]
        z.Z3_del_config.argtypes=[ctypes.c_void_p]
        z.Z3_get_version.argtypes=[ctypes.POINTER(ctypes.c_uint)]*4
        a,b,c,d=(ctypes.c_uint() for _ in range(4))
        z.Z3_get_version(ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d))
        self.version='.'.join(map(str,(a.value,b.value,c.value,d.value)))
    def check(self,text):
        z=self.z
        cfg=z.Z3_mk_config();ctx=z.Z3_mk_context(cfg)
        try:
            out=z.Z3_eval_smtlib2_string(ctx,text.encode('ascii'))
            result=out.decode('utf8') if out else '(null)'
        finally:
            z.Z3_del_context(ctx);z.Z3_del_config(cfg)
        return result.strip()

backend=None
class Solver:
    def __init__(self):self.terms=[]
    def add(self,*terms):self.terms.extend(terms)
    def smt(self):
        # Declaring unused Int vars is harmless and avoids tracking symbols.
        names=[f'gap_{i}' for i in range(18)]+[f'rank_{i}' for i in range(16)]
        return ('(set-logic QF_LIA)\n'+''.join(f'(declare-const {n} Int)\n' for n in names)
               +''.join(f'(assert {enc(t)})\n' for t in self.terms)+'(check-sat)\n')
    def check(self):return backend.check(self.smt())
shim.Solver=Solver


def main():
    global backend
    parser=argparse.ArgumentParser()
    parser.add_argument('--lib',default='libz3.so.4')
    parser.add_argument('--json',type=Path)
    args=parser.parse_args()
    backend=NativeLib(args.lib)
    sys.modules['z3']=shim
    path=Path(__file__).with_name('prove_minimum.py')
    spec=importlib.util.spec_from_file_location('bmn_original_model',path)
    model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
    result={'native_z3':backend.version, 'method':'existing exact gap model + native C API SMT-LIB solving','periods':[]}
    start=time.perf_counter()
    for period in range(2,6):
        count=0; colorings=0; t0=time.perf_counter()
        for case in model.skeletons(period):
            count+=1; colorings+=case['rank_coloring_count']
            solver=model.gap_problem(case,ordinary_count=36)
            status=solver.check()
            if status!='unsat':
                raise RuntimeError(f'p={period} skeleton {count}: {status}')
        assert (count,colorings)==model.EXPECTED[period]
        entry={'period':period,'skeletons':count,'represented_rank_assignments':colorings,'all_unsat':True,'seconds':round(time.perf_counter()-t0,3)}
        print(entry,flush=True);result['periods'].append(entry)
    result['elapsed_seconds']=round(time.perf_counter()-start,3)
    if args.json:args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(f'PASS: complete p=2,..,5 exclusions using native libz3 {backend.version}')

if __name__=='__main__':main()
