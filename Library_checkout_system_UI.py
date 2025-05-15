import threading
import time,datetime
from time import localtime, strptime
from flask import Flask, render_template, request, redirect, url_for
from project.module.find_book import *
from project.module.find_student import *
from project.module.return_book import *
from project.module.check_out import *
from project.module.is_in_borrowed_books import *
from project.module.update_log import *
from project.module.update_borrowed_books import *
from project.module.update_fine import *
from project.module.send_gmail import *
from project.read_log import *
from project.register import register
import slack_sdk
import sys
import re

if sys.platform == 'win32': 
    import winsound as sd

app = Flask(__name__)

INVALID = 0
YES = 1
NO = 0

DEBUG = False #WARNING!!!! DO NOT CHANGE THIS TO TRUE!!!!

lb = r'\n'
try:
    slack_token = 'xoxb-7003132549716-6997776435477-MQvsG7QEj8lKhPdfv6uEIAAq'

    client = slack_sdk.WebClient(token=slack_token)
except: print("Slack launching has failed.")

def beep(fr=2000, tm=700):
    if(sys.platform == 'win32'):
        sd.Beep(fr, tm)
    pass

def success():
    beep(440, 350)
    beep(659, 350)

def message(msg, title="ERROR", code=16):
    pass

def send_slack_message(msg):
    if not DEBUG:
        try:
            client.chat_postMessage(channel='#seoul-academy-library-messenger', text=msg)
            return
        except:
            return
    else: pass

student_name = ""
book_name = ""
student_info = ""

@app.errorhandler(Exception)
def handle_error(error):
    beep()
    message(str(error))
    print(str(error))
    update_log("Error: " + str(error))
    return render_template('error.html', error=error)

@app.route('/')
def init():
    return redirect(url_for('index'))

@app.route('/home', methods=['POST', 'GET'])
def index():
    global student_name, book_name, student_info, logdata
    student_name = ""
    book_name = ""
    student_info = ""
    logdata = ""
    return render_template('index.html')

CHECKOUT = True

@app.route('/book', methods=['POST'])
def book():
    global student_name, book_name, student_info, CHECKOUT
    if request.method == 'POST':
        student_barcode = request.form.get('student_barcode', False)
        student_info = find_student(student_barcode)
        if student_info != INVALID:
            student_name = f"{student_info[1]} {student_info[2]}"
            CHECKOUT = True
            return render_template('book.html', name=student_name, barcode=student_barcode)
        else:
            return render_template('error.html', error="Either you are not yet registered or the input is wrong.")

@app.route('/main', methods=['POST'])
def checkout():
    global student_name, book_name, student_info, CHECKOUT
    if request.method == 'POST':
        book_barcode = request.form.get('book_barcode', False)
        book_info = find_book(book_barcode)
        if book_info == INVALID:
            return render_template('error.html', error="Either the book is not yet registered or the input is wrong.")
        else:
            if is_in_borrowed_books(book_info[0], student_info[0]) == YES and CHECKOUT == True:
                CHECKOUT = False
                fine = return_book(book_info[0], student_info[0])
                send_slack_message(f"{student_info[1]} returned {re.sub(lb, '', book_info[1])}.")
                message("You successfully returned " + book_info[1], "Notification", 64)
                try:
                    send_gmail(student_info[3], f"""Hello, this is Seoul Academy Library.

We would like to inform you that you have successfully returned the book: '{re.sub(lb, '', book_info[1])}'.

Thank you for using Seoul Academy Library system.

Best regards, Seoul Academy.
                    """)
                except:
                    pass
                if os.path.exists(f"book_history/{book_barcode}.txt"):
                    f = open(f"book_history/{book_barcode}.txt",'a')
                else:
                    f = open(f"book_history/{book_barcode}.txt",'w')
                current_time = time.localtime(time.time())
                current_time = strftime('%Y-%m-%d %H:%M:%S',current_time)
                f.write(f"{current_time} {student_info[1]} {student_info[2]} returned {re.sub(lb, '', book_info[1])}\n")
                f.close()

                if os.path.exists(f"student_history/{student_info[0]}.txt"):
                    f = open(f"student_history/{student_info[0]}.txt",'a')
                else:
                    f = open(f"student_history/{student_info[0]}.txt",'w')
                f.write(f"{current_time} {student_info[1]} {student_info[2]} returned {book_barcode} {re.sub(lb, '', book_info[1])}\n")

                success()
                return render_template('returning_complete.html', name=student_name, bookname=book_info[1], fine=fine)
            elif is_in_borrowed_books(book_info[0], student_info[0]) == NO and CHECKOUT == True:
                CHECKOUT = False
                check_out(book_info[0], student_info[0])
                send_slack_message(f"{student_info[1]} borrowed {re.sub(lb, '', book_info[1])}. Please be in mind that there would be late fees if you don't return it on time.")
                message("You successfully borrowed " + book_info[1], "Notification", 64)
                try:
                    send_gmail(student_info[3], "", book_info[1])
                except:
                    pass
                if os.path.exists(f"book_history/{book_barcode}.txt"):
                    f = open(f"book_history/{book_barcode}.txt",'a')
                else:
                    f = open(f"book_history/{book_barcode}.txt",'w')
                current_time = time.localtime(time.time())
                current_time = strftime('%Y-%m-%d %H:%M:%S',current_time)
                f.write(f"{current_time} {student_info[1]} {student_info[2]} borrowed {re.sub(lb, '', book_info[1])}\n")
                f.close()

                if os.path.exists(f"student_history/{student_info[0]}.txt"):
                    f = open(f"student_history/{student_info[0]}.txt",'a')
                else:
                    f = open(f"student_history/{student_info[0]}.txt",'w')
                f.write(f"{current_time} {student_info[1]} {student_info[2]} borrowed {book_barcode} {re.sub(lb, '', book_info[1])}\n")

                success()
                return render_template('borrowing_complete.html', name=student_name, bookname=book_info[1])
            elif CHECKOUT == False:
                return redirect(url_for('index'))

@app.route('/admin', methods=['GET'])
def admin():
    return render_template('admin.html')

@app.route('/login', methods=['POST', 'GET'])
def adminlogin():
    global logdata, current_borrowed_books_data
    admin_name = request.form.get('admin_name', False)
    password = request.form.get('password', False)
    key = get_key()
    logdata = login(admin_name, password, key)
    current_borrowed_books_data = borrowed_book_list(key)
    return redirect("/log")

@app.route('/credit', methods=['POST', 'GET'])
def credit():
    return render_template('credits.html')

@app.route('/log', methods=['POST', 'GET'])
def log_page():
    global logdata, current_borrowed_books_data
    current_borrowed_books_data_with_due_date = []
    for item in current_borrowed_books_data:
        item.replace("\n","")
        item = item.split()
        borrowedtime = item[0] + " " + item[1]
        borrowedtime = time.strptime(borrowedtime,"[%Y-%m-%d %H:%M:%S]")
        duetime = time.localtime(time.mktime(borrowedtime) + 86400*14)
        duetime = time.strftime("%Y-%m-%d %H:%M:%S",duetime)
        a = duetime + " " + " ".join(item[2:])
        a = a.replace("[","")
        a = a.replace("]","")
        a = a.replace("/","")
        current_borrowed_books_data_with_due_date.append(a)
    return render_template('log.html', logdata=logdata, current_borrowed_books_data=current_borrowed_books_data_with_due_date)

@app.route('/register', methods=['POST', 'GET'])
def register1(): 
    return render_template('register.html')

@app.route('/register/process', methods=['POST', 'GET'])
def registration():
    admin_name = request.form.get('admin_name', False)
    password = request.form.get('password', False)
    key = request.form.get('key', False)
    register(admin_name, password, key)
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

def check_unreturned_books():
    print("Unreturned Book Checking Is Enabled!")
    key = get_key()
    while True:
        with open("borrowed_books.txt", 'r', encoding='UTF8') as f:
            current_time = localtime(time.time())
            for line in f:
                line = decrypt(line, key)
                line = line.split()
                line_containing_time = line[0] + " " + line[1]
                borrowed_time = strptime(line_containing_time, "[%Y-%m-%d %I:%M:%S]")
                student_id = line[2]
                isbn = line[3]
                book_name = find_book(isbn)[1]
                int_current_time = time.mktime(current_time)
                int_borrowed_time = time.mktime(borrowed_time)
                days_passed = int(int_current_time - int_borrowed_time) / (60 * 60 * 24)  # 60 = second / 60 = minute / 24 = hours
                if days_passed > 14:
                    email = find_student("1 " + student_id)[3]
                    send_gmail(email, f"""Hello, this is Seoul Academy Library.

We would like to inform you that you have unreturned books: '{book_name}'.
Please return it as soon as possible, or it will occur additional late fee.

Thank you for using Seoul Academy Library system.

Best regards, Seoul Academy.
                    """)
        time.sleep(43200)  # Checking occurs every 12 hours


@app.route('/search', methods=['POST', 'GET'])
def search():
    isbn_for_searching = request.form.get('isbn_for_searching', False)
    if os.path.exists(f"book_history/{isbn_for_searching}.txt"):
        history = []
        name = find_book(isbn_for_searching)
        name = " ".join(name[1:])
        f = open(f"book_history/{isbn_for_searching}.txt")
        for line in f:
            history.append(line)
        return render_template('search.html', book_history = history,book_name = name)
    else:
        return render_template('no_result.html')
    
@app.route('/students', methods=['POST', 'GET'])
def students():
    students = []
    with open("studentdata.txt", "r") as f:
        for line in f:
            parts = line.split()
            student = {
                'id': int(parts[0]),
                'name': parts[1] + ' ' + parts[2],
                'email': parts[3]
            }
            students.append(student)
    return render_template('students.html', student_information=students)


@app.route('/students/<int:user_id>')
def individual_students(user_id):
    try:
        f = open(f"student_history/{user_id}.txt")
        information = []
        name = ""
        for line in f:
            parts = line.split()
            name = parts[2] + " " + parts[3]
            info = {
                'date': parts[0] + " " + parts[1],
                'state': parts[4],
                'isbn': parts[5],
                'title': " ".join(parts[6:])
            }
            information.append(info)
        return render_template('individual_student.html', sname = name, s_information = information)
    except:
        return render_template('no_result_students.html')

if __name__ == '__main__':
    check_unreturned_books_thread = threading.Thread(target=check_unreturned_books)
    check_unreturned_books_thread.daemon = True
    check_unreturned_books_thread.start()
    app.run(debug=DEBUG)
