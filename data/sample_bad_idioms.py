# Bad: using range(len()) instead of enumerate
names = ["Alice", "Bob", "Charlie"]
for i in range(len(names)):
    print(i, names[i])

# Bad: building list with a loop instead of list comprehension
squares = []
for i in range(10):
    squares.append(i * i)

# Bad: not using zip() to iterate over two lists
first = [1, 2, 3]
second = [4, 5, 6]
for i in range(len(first)):
    print(first[i], second[i])

# Bad: comparing to True with ==
flag = True
if flag == True:
    print("flag is true")

# Bad: comparing to None with ==
value = None
if value == None:
    print("value is none")

# Bad: not using context manager for file handling
f = open("README.md", "r")
content = f.read()
f.close()

# Bad: mutable default argument
def add_item(item, items=[]):
    items.append(item)
    return items

# Bad: not using any()
numbers = [1, 2, 3, 4, 5]
found = False
for n in numbers:
    if n > 3:
        found = True
        break