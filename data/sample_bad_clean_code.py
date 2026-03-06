import os, sys, json
import os
import math

x=1
y =2
z= 3

def calculate_total( items,tax ):
    total=0
    for i in range(len(items)):
        total=total+items[i]
    total=total+(total*tax)
    return total

def calculate_total_v2( items,tax ):
    total=0
    for i in range(len(items)):
        total=total+items[i]
    total=total+(total*tax)
    return total

def calculate_total_v3( items,tax ):
    total=0
    for i in range(len(items)):
        total=total+items[i]
    total=total+(total*tax)
    return total

def get_user_name(u):
    if u['name']=="":
        return "unknown"
    else:
        return u['name']

def get_user_email(u):
    if u['email']=="":
        return "unknown"
    else:
        return u['email']

def get_user_age(u):
    if u['age']==None:
        return 0
    else:
        return u['age']

class   userManager:
    def __init__(self,users):
        self.users=users
        self.data=[]
        self.temp=[]
        self.result=[]

    def getUsers( self ):
        result=[]
        for i in range(len(self.users)):
            result.append(self.users[i])
        return result

    def getActiveUsers( self ):
        result=[]
        for i in range(len(self.users)):
            result.append(self.users[i])
        return result

    def getInactiveUsers( self ):
        result=[]
        for i in range(len(self.users)):
            result.append(self.users[i])
        return result

    def processUser(self,u):
        name=""
        email=""
        age=0
        if u['name']=="":
            name="unknown"
        else:
            name=u['name']
        if u['email']=="":
            email="unknown"
        else:
            email=u['email']
        if u['age']==None:
            age=0
        else:
            age=u['age']
        return {'name':name,'email':email,'age':age}

    def processUsers(self,users):
        result=[]
        for i in range(len(users)):
            name=""
            email=""
            age=0
            if users[i]['name']=="":
                name="unknown"
            else:
                name=users[i]['name']
            if users[i]['email']=="":
                email="unknown"
            else:
                email=users[i]['email']
            if users[i]['age']==None:
                age=0
            else:
                age=users[i]['age']
            result.append({'name':name,'email':email,'age':age})
        return result

def load_config(path):
    f=open(path)
    data=json.load(f)
    f.close()
    return data

def load_config_v2(path):
    f=open(path)
    data=json.load(f)
    f.close()
    return data

def save_config(path,data):
    f=open(path,'w')
    json.dump(data,f)
    f.close()

def save_config_v2(path,data):
    f=open(path,'w')
    json.dump(data,f)
    f.close()

l = lambda x,y: x+y
m = lambda x,y: x*y
n = lambda x,y: x-y

ITEMS=[]
USERS=[]
CONFIG={}
DATA  =  []
