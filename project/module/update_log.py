from time import localtime,time,strftime
from project.module.find_student import *
from project.module.find_book import *
from dotenv import load_dotenv
import os
import random
import tkinter as tk
import math,re,inspect,sys

def encrypt(text, key):
    encrypted_text = ""
    for i in range(len(text)):
        encrypted_text += chr(ord(text[i]) * ord(key[i % len(key)]))
    return encrypted_text

def decrypt(encrypted_text, key):
    decrypted_text = ""
    for i in range(len(encrypted_text)):
        decrypted_text += chr(ord(encrypted_text[i]) // ord(key[i % len(key)]))
 
    decrypted_text = re.sub(r'\n', '', decrypted_text)
    decrypted_text = re.sub(r'\x00', '', decrypted_text)       
    return decrypted_text

def update_log(state, s_id = '//', isbn = '//'):
    KEY = get_key()
    date =  localtime(time())
    f = open("logfile.txt",'a',encoding='UTF8')
    if (state == 0): state = "Borrowed"
    elif(state == 1): state = "Returned"
    elif (state == 2): state = "Error" 
    elif (state == 3): state = "Error - Name not found"
    elif (state == 4): state = "Error - Book not found"
    elif (state == 5): state = "Student information inputted"
    elif (state == 6): state = "ISBN data inputted"
    elif (state == 7): state = "Successfully booted"
    elif (state == 8): state = "Information found in borrowed_books file"
    elif (state == 9): state = "Logfile browsed"
    elif (state == 10): state = "Logfile attempted to be browsed but failed"
    elif (state == 11): state = "Fine given"
    elif (state == 12): state = "Gmail sent"
    f.write(encrypt(strftime("[%Y-%m-%d %I:%M:%S]",date) + " " + str(s_id) +" "+ str(isbn) + " " + str(state),KEY) + "\n")
    return 0

def get_key():
    load_dotenv()
    return os.getenv("password")
    
def read_log(key):
    try:
        f = open("logfile.txt",'r',encoding='UTF8')
        message_list = []
        for line in f:
            date = ''
            name = ''
            title = ''
            msg = ''
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
            msg = ' '.join(a[4:]) + " "
            msg.replace('\x00','')
            message = date + msg + "[" + name + title + "]"
            message = re.sub(r'\n', '', message)
            message = re.sub(r'\x00', '', message)
            message += '\n'
            message_list.append(message)
        return message_list
    except IndexError:
        return ["Logfile error, please try merging logfile.txt in git."]

if __name__ == "__main__":
    exit()