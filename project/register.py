from project.read_log import *
from project.main import *
def register(id,pw,key):
    f = open("admin.txt",'a',encoding='UTF8')
    f.write(encrypt(id,key) + " " + encrypt(pw,key) + "\n")
    return "Your information has been appended to the file!"