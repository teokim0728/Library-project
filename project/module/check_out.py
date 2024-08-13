from project.module.insert_borrowed_books import *
from project.module.update_log import *
from time import localtime,time

def check_out(isbn:int,s_id:int):
    update_log(0,s_id,isbn)
    insert_borrowed_books(s_id,isbn)