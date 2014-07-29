#coding=utf-8
import pprint
import types

def p(v):
    if type(v) is types.ClassType:
        pprint.pprint(vars(v))
    else:
        pprint.pprint(v)
