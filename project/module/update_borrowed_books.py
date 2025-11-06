from project.module.update_fine import *
from time import *
def update_borrow_books(s_id, isbn):
    key = get_key()
    with open("borrowed_books.txt", 'r', encoding='UTF8') as f:
        borrowed_date = ''
        current_date = localtime(time())
        lines = []
        for line in f:
            line = decrypt(line, key)
            line = line.split()
            if line[3] != isbn:
                lines.append(line)
            else:
                borrowed_date = line[0] + " " + line[1]
        borrowed_date = strptime(borrowed_date, "[%Y-%m-%d %I:%M:%S]")
    with open("borrowed_books.txt", 'w', encoding='UTF8') as f:
        for line in lines:
            line = encrypt(line[0] + " " + line[1] + " " + line[2] + " " + line[3], key) + '\n'
            f.write(line)
    return update_fine(s_id, current_date, borrowed_date)
