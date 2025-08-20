import os
from project.module.update_log import *
def is_in_borrowed_books(isbn,s_id):
    borrowed = open("borrowed_books.txt", "r", encoding='UTF8')
    existing_info = False
    key = get_key()
    for line in borrowed:
        line = decrypt(line,key)
        line = ''.join(line)
        line = line.split()
        if line[2] == s_id and line[3] == isbn:
            existing_info = True
            update_log(8,s_id,isbn)
    borrowed.close()
    return existing_info
