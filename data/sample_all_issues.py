# ruff: noqa

import os,sys
import os

# --- Code Style Issues ---
# Bad spacing around operators and after commas
def calculate_discount(price,discount_rate):
    discounted=price-(price*discount_rate)
    return discounted

class   orderProcessor:
    def __init__(self,orders):
        self.orders=orders

    def getTotal( self ):
        total=0
        for i in range(len(self.orders)):
            total=total+self.orders[i]['amount']
        return total

# --- Clean Code Issues ---
# Magic numbers, duplicated logic, poor naming
def p(lst):
    r=0
    for i in range(len(lst)):
        if lst[i] > 0:
            r = r + lst[i]
    return r

def p2(lst):
    r=0
    for i in range(len(lst)):
        if lst[i] > 0:
            r = r + lst[i]
    return r

def get_status(code):
    if code == 1:
        return "active"
    elif code == 2:
        return "inactive"
    elif code == 3:
        return "pending"
    elif code == 4:
        return "banned"
    else:
        return "unknown"

# File opened without context manager
def read_data(path):
    f = open(path, 'r')
    data = f.read()
    f.close()
    return data

# --- Idiom Issues ---
# Should use enumerate
items = ["apple", "banana", "cherry"]
for i in range(len(items)):
    print(i, items[i])

# Should use list comprehension
evens = []
for n in range(20):
    if n % 2 == 0:
        evens.append(n)

# Comparing to None with ==
def is_empty(val):
    if val == None:
        return True
    return False

# Mutable default argument
def append_tag(tag, tags=[]):
    tags.append(tag)
    return tags

# Should use any()
scores = [45, 82, 60, 91]
passed = False
for s in scores:
    if s >= 90:
        passed = True
        break

# --- Missing Tests ---
# The following functions have no corresponding test file or unit tests

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b
