import tkinter as tk
from tkinter import messagebox
from project.module.update_log import *
from project.module.send_gmail import *

f = open("admin.txt",'a')
def login(admin_name,password,key):
    f = open("admin.txt",'r',encoding='UTF8')
    for line in f:
        try:
            line = line.split()
            ID = decrypt(line[0],key)
            PW = decrypt(line[1],key)
            if admin_name == ID and password== PW:
                update_log(9,ID,PW)
                return read_log(key)
        except Exception as e:
            update_log(e)
            return e
    update_log(10)
    return

def borrowed_book_list(key):
    f = open("admin.txt",'r',encoding='UTF8')
    try:
        f = open("borrowed_books.txt",'r',encoding='UTF8')
        message_list = []
        for line in f:
            date = ''
            name = ''
            title = ''
            a = decrypt(line,key)
            a = str.split(a)
            date = a[0] + " " + a[1] + " "
            if(find_student(". "+str(a[2]))):
                name = find_student(". "+str(a[2]))[1] + " " + find_student(". "+str(a[2]) + " .")[2] + " / "
            else: name = a[2] + " | "
            if(find_book(a[3])):
                title = find_book(int(a[3]))[1]
                title.replace('\n','')
            else: title = a[3]
            message = date + "[" + name + title + "]"
            message = re.sub(r'\n', '', message)
            message = re.sub(r'\x00', '', message)
            message += '\n'
            message_list.append(message)
        return message_list
    except IndexError:
        return ["Logfile error, please try merging logfile.txt in git."]