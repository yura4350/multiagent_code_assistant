# ruff: noqa

# Unused import
# Bad spacing
# Bad naming
# Bad comparison

import os,sys

x=10
y =20

class   myClass:
    def __init__(self,name):
        self.name=name
    def getName( self ):
        if self.name=="":
            return "no name"
        else:
            return self.name