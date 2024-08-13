from project.module.update_log import *
from project.module.update_borrowed_books import *
from time import localtime,time
def return_book(isbn,s_id):
    update_log(1,s_id,isbn)
    return update_borrow_books(s_id,isbn)

