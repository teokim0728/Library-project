from time import localtime, time, strftime
from time import struct_time
from project.module.update_log import get_key,encrypt
import time

def insert_borrowed_books(s_id:str,isbn:str):
    key = get_key()
    date =  time.localtime(time.time())
    f = open("borrowed_books.txt",'a', encoding='UTF8')
    f.write(encrypt(strftime("[%Y-%m-%d %I:%M:%S]",date)+ " " + s_id + " " + isbn,key) + "\n")