# how many upper case chars in text
text = "bdrgkehdg DFHLDCFH hkhHIHohoHH OHO oHHH"
count = 0
for chars in text:
    if chars.isupper():
        count += 1

print(str(count))

# swap two numbers
rr = 23
result = rr%10 * 10 + int(rr/10)
print(result)

# decorators
# What is a decorator in Python?
""" Image result for decorators in python
 A decorator in Python is a function that takes another function as its argument,  
 and returns yet another function . 
 Decorators can be extremely useful as they allow the extension of an existing function, 
 without any modification to the original function source code
"""

def decorator_list(fnc):
    def inner(list_of_tuples):
        return [fnc(val[0], val[1]) for val in list_of_tuples]
    return inner


@decorator_list
def add_together(a, b):
    return a + b


#print(add_together([(1, 3), (3, 17), (5, 5), (6, 7)]))
#print(decorator_list(add_together))

# Part 2
def meta_decorator(power):
    def decorator_list1(fnc):
        def inner1(list_of_tuples):
            return [(fnc(val[0], val[1])) ** power for val in list_of_tuples]
        return inner1
    return decorator_list1

# passed power value from decorator
@meta_decorator(2)
def add_together1(a, b):
    return a + b


print(add_together1([(1, 3), (3, 17), (5, 5), (6, 7)]))

# What is pickling and unpickling?
"""Ans: Pickle module accepts any Python object and converts it into a string representation 
and dumps it into a file by using dump function, this process is called pickling. 

While the process of retrieving original Python objects from the stored string representation 
is called unpickling."""

#  What are the generators in python?
"""Ans: Functions that return an iterable set of items are called generators."""

# What is a dictionary in Python?
"""Ans: The built-in datatypes in Python is called dictionary. 
It defines one-to-one relationship between keys and values. 
Dictionaries contain pair of keys and their corresponding values. 
Dictionaries are indexed by keys.

Let’s take an example:

The following example contains some keys. Country, Capital & PM. Their corresponding values are India, Delhi and Modi respectively.

1
dict={'Country':'India','Capital':'Delhi','PM':'Modi'}
1
print dict[Country]
Output:India"""


"""
 Whenever Python exits, why isn’t all the memory de-allocated?
Ans:

Whenever Python exits, especially those Python modules which are having circular references to other objects or the objects that are referenced from the global namespaces are not always de-allocated or freed.
It is impossible to de-allocate those portions of memory that are reserved by the C library.
On exit, because of having its own efficient clean up mechanism, 
Python would try to de-allocate/destroy every other object.
"""


"""
 What advantages do NumPy arrays offer over (nested) Python lists?
Ans: 

Python’s lists are efficient general-purpose containers. They support (fairly) efficient insertion, deletion, appending, and concatenation, and Python’s list comprehensions make them easy to construct and manipulate.
They have certain limitations: they don’t support “vectorized” operations like elementwise addition and multiplication, and the fact that they can contain objects of differing types mean that Python must store type information for every element, and must execute type dispatching code when operating on each element.
NumPy is not just more efficient; it is also more convenient. You get a lot of vector and matrix operations for free, which sometimes allow one to avoid unnecessary work. And they are also efficiently implemented.
NumPy array is faster and You get a lot built in with NumPy, FFTs, convolutions, fast searching, basic statistics, linear algebra, histograms, etc. 
"""

"""How to add values to a python array?
Ans: Elements can be added to an array using the append(), extend() and the insert (i,x) functions.

Example:"""

import array
a=arr.array('d', [1.1 , 2.1 ,3.1] )
a.append(3.4)
print(a)
a.extend([4.5,6.3,6.8])
print(a)
a.insert(2,3.8)
print(a)

"""
Does Python have OOps concepts?
Ans: Python is an object-oriented programming language. 
This means that any program can be solved in python by creating an object model. 
However, Python can be treated as procedural as well as structural language.
"""

"""
How is Multithreading achieved in Python?
Ans: 

Python has a multi-threading package but if you want to multi-thread to speed your code up, 
then it’s usually not a good idea to use it.
Python has a construct called the Global Interpreter Lock (GIL). 
The GIL makes sure that only one of your ‘threads’ can execute at any one time. 
A thread acquires the GIL, does a little work, then passes the GIL onto the next thread.
This happens very quickly so to the human eye it may seem like your threads are executing in parallel, 
but they are really just taking turns using the same CPU core.
All this GIL passing adds overhead to execution. 
This means that if you want to make your code run faster then using the threading package often isn’t a good idea.
"""

"""Explain how you can set up the Database in Django.
Ans: You can use the command edit mysite/setting.py, it is a normal python module with module level representing Django settings.

Django uses SQLite by default; it is easy for Django users as such it won’t require any other type of installation. In the case your database choice is different that you have to the following keys in the DATABASE ‘default’ item to match your database connection settings.

Engines: you can change the database by using ‘django.db.backends.sqlite3’ , ‘django.db.backeneds.mysql’, ‘django.db.backends.postgresql_psycopg2’, ‘django.db.backends.oracle’ and so on
Name: The name of your database. In the case if you are using SQLite as your database, in that case, database will be a file on your computer, Name should be a full absolute path, including the file name of that file.
If you are not choosing SQLite as your database then settings like Password, Host, User, etc. must be added.
Django uses SQLite as a default database, it stores data as a single file in the filesystem. If you do have a database server—PostgreSQL, MySQL, Oracle, MSSQL—and want to use it rather than SQLite, then use your database’s administration tools to create a new database for your Django project. Either way, with your (empty) database in place, all that remains is to tell Django how to use it. This is where your project’s settings.py file comes in.

We will add the following lines of code to the setting.py file:

DATABASES = {
     'default': {
          'ENGINE' : 'django.db.backends.sqlite3',
          'NAME' : os.path.join(BASE_DIR, 'db.sqlite3'),
     }
}"""

"""
Explain the use of session in Django framework?
Ans: Django provides a session that lets you store and retrieve data on a per-site-visitor basis. 
Django abstracts the process of sending and receiving cookies, 
by placing a session ID cookie on the client side, 
and storing all the related data on the server side.

So the data itself is not stored client side. This is nice from a security perspective.
"""

"""
List out the inheritance styles in Django.

Ans: In Django, there are three possible inheritance styles:

Abstract Base Classes: This style is used when you only want parent’s class to hold information that you don’t want to type out for each child model.
Multi-table Inheritance: This style is used If you are sub-classing an existing model and need each model to have its own database table.
Proxy models: You can use this model, 
If you only want to modify the Python level behavior of the model, 
without changing the model’s fields.
Next in this Python Interview Question blog, 
let’s have a look at questions related to Web Scraping
"""