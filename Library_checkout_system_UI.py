import threading
import time
import datetime as dt
from time import localtime, strftime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from project.module.find_book import *  # find_book
from project.module.find_student import *  # find_student
from project.module.return_book import *  # return_book
from project.module.check_out import *  # check_out
from project.module.is_in_borrowed_books import *  # is_in_borrowed_books
from project.module.update_log import *  # update_log
from project.module.update_borrowed_books import *  # borrowed_book_list (?)
from project.module.update_fine import *  # update_fine (if used elsewhere)
from project.module.send_gmail import *  # send_gmail
from project.read_log import *  # get_key, login, borrowed_book_list, decrypt
from project.register import register
import slack_sdk
import sys
import re
import dotenv
from functools import wraps
import os
from pathlib import Path

# -------------------------
# Environment & constants
# -------------------------
dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY가 환경 변수에 설정되지 않았습니다. .env 파일을 확인하세요.")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#seoul-academy-library-messenger")

DEBUG = False  # WARNING: Do NOT change to True in production

# Sentinel values (avoid collisions: INVALID must differ from NO)
INVALID = -1
YES = 1
NO = 0

# Linebreak pattern used in original logs
lb = r"\n"

# -------------------------
# App & integrations
# -------------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Optional Slack client
slack_client = None
if SLACK_BOT_TOKEN:
    try:
        slack_client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)
    except Exception as e:
        print(f"[WARN] Slack client init failed: {e}")
        slack_client = None

# Optional Windows beep
if sys.platform == "win32":
    import winsound as sd  # type: ignore
else:
    sd = None


def beep(fr: int = 2000, tm: int = 700) -> None:
    if sd is not None:
        try:
            sd.Beep(fr, tm)
        except Exception:
            pass


def success() -> None:
    beep(440, 350)
    beep(659, 350)


def message(msg: str, title: str = "ERROR", code: int = 16) -> None:
    # Placeholder (GUI message box previously). We surface via flash + logs.
    update_log(f"{title}: {msg}")


def send_slack_message(msg: str) -> None:
    if not slack_client or DEBUG:
        return
    try:
        slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=msg)
    except Exception:
        # Slack failing should not break the app
        pass


# -------------------------
# Auth decorator
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("adminlogin"))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------
# Error handler
# -------------------------
@app.errorhandler(Exception)
def handle_error(error):
    try:
        beep()
    except Exception:
        pass
    msg = str(error)
    message(msg, title="Unhandled Exception", code=16)
    print(msg)
    # Render user-friendly error page with HTTP 500
    return render_template("error.html", error=error), 500

# -------------------------
# Cache deleter
# -------------------------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# BLOCKED_HOSTS = {"http://127.0.0.1:5000/log", "http://127.0.0.1:5000/student"} 

# @app.before_request
# def block_invalid_subdomains():
#     host = request.host.split(":")[0]
#     if host in BLOCKED_HOSTS:
#         session.pop("student_info", None)
#         session.pop("checkout_ready", None)
#         return redirect(url_for("index"))

# -------------------------
# Helpers
# -------------------------
def _ensure_dirs():
    Path("book_history").mkdir(parents=True, exist_ok=True)
    Path("student_history").mkdir(parents=True, exist_ok=True)


def _now_string() -> str:
    return strftime("%Y-%m-%d %H:%M:%S", localtime(time.time()))


def _write_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line)


def _parse_timestamp_flex(ts: str) -> dt.datetime:
    # Try multiple common formats, with or without brackets
    ts = ts.strip()
    ts = ts.strip("[]")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M:%S"):
        try:
            return dt.datetime.strptime(ts, fmt)
        except ValueError:
            continue
    # As a last resort, now
    return dt.datetime.now()


# -------------------------
# Common routes
# -------------------------
@app.route("/")
def init():
    return redirect(url_for("index"))


@app.route("/home", methods=["POST", "GET"])
def index():
    
    session.pop("student_info", None)
    session.pop("checkout_ready", None)
    return render_template("index.html")


@app.route("/book", methods=["POST"])  # Student barcode -> identify student
def book():
    
    student_barcode = request.form.get("student_barcode", "").strip()
    if not student_barcode:
        return render_template("error.html", error="Student barcode is required."), 400

    student_info = find_student(student_barcode)
    if student_info == INVALID or not student_info:
        return render_template(
            "error.html",
            error="Either you are not yet registered or the input is wrong.",
        ), 404

    # Expecting: (student_id, first_name, last_name, email, ...)
    try:
        student_name = f"{student_info[1]} {student_info[2]}".strip()
    except Exception:
        student_name = "Student"

    session["student_info"] = list(student_info)  # JSON-serializable
    session["checkout_ready"] = True
    return render_template("book.html", name=student_name, barcode=student_barcode)

@app.route("/addbook", methods=["POST","GET"])  # Manually add book
def addbook():
    student_info = session.get("student_info")
    book_barcode = request.form.get("book_barcode", "").strip()
    book_name = request.form.get("book_name", "").strip()
    if not book_name:
        return render_template("error.html", error="Book name is required."), 400
    try:
        with open("isbndata.txt", "a", encoding="utf-8") as f:
            f.write(f"\n{book_barcode} {book_name}")
        check_out(book_barcode, student_info[0])
        update_log(13, student_info[0], book_barcode)
        student_id = student_info[0]
        student_name = f"{student_info[1]} {student_info[2]}".strip()
        current_time = _now_string()
        student_email = student_info[3] if len(student_info) > 3 else None
        _write_line(Path(f"book_history/{book_barcode}.txt"), f"{current_time} {student_name} borrowed {book_name}\n")
        _write_line(Path(f"student_history/{student_id}.txt"),f"{current_time} {student_name} borrowed {book_barcode} {book_name}\n")
        if student_email:
            try:
                send_gmail(
                    student_email,
                    f"""Hello, this is Seoul Academy Library.

We would like to inform you that you have successfully borrowed the book: '{book_name}'.

Thank you for using Seoul Academy Library system.

Best regards, Seoul Academy.
""",
                )
            except Exception:
                pass
    except Exception as e:
        return render_template("error.html", error=str(e)), 500
    return render_template("borrowing_complete.html", name=student_info[1], bookname=book_name)

@app.route("/main", methods=["POST"])  # Book barcode -> checkout/return
def checkout():
    if not session.get("checkout_ready") or not session.get("student_info"):
        return redirect(url_for("index"))

    student_info = session["student_info"]
    book_barcode = request.form.get("book_barcode", "").strip()
    if not book_barcode:
        return render_template("error.html", error="Book barcode is required."), 400

    book_info = find_book(book_barcode)
    if book_info == INVALID or not book_info:
        return render_template(
            "book_not_found.html",
            error="Either the book is not yet registered or the input is wrong.",
            book_barcode = book_barcode
        )
    
    # Expecting: (isbn, title, ...)
    isbn = book_info[0]
    title = re.sub(lb, "", book_info[1]) if len(book_info) > 1 else "(Untitled)"
    student_id = student_info[0]
    student_name = f"{student_info[1]} {student_info[2]}".strip()
    student_email = student_info[3] if len(student_info) > 3 else None

    # One-shot guard to avoid double-processing (per session)
    session["checkout_ready"] = False

    # Decide return vs checkout
    try:
        already_borrowed = is_in_borrowed_books(isbn, student_id)
    except Exception:
        already_borrowed = NO

    _ensure_dirs()
    current_time = _now_string()

    if already_borrowed == YES:
        # Return flow
        try:
            fine = return_book(isbn, student_id)
        except Exception:
            fine = 0
        send_slack_message(f"{student_info[1]} returned {title}.")
        message(f"You successfully returned {title}", "Notification", 64)

        # Email (best-effort)
        if student_email:
            try:
                send_gmail(
                    student_email,
                    f"""Hello, this is Seoul Academy Library.

We would like to inform you that you have successfully returned the book: '{title}'.

Thank you for using Seoul Academy Library system.

Best regards, Seoul Academy.
""",
                )
            except Exception:
                pass

        # History files
        _write_line(Path(f"book_history/{book_barcode}.txt"), f"{current_time} {student_name} returned {title}\n")
        _write_line(
            Path(f"student_history/{student_id}.txt"),
            f"{current_time} {student_name} returned {book_barcode} {title}\n",
        )

        success()
        return render_template("returning_complete.html", name=student_name, bookname=title, fine=fine)

    else:
        # Checkout flow
        try:
            check_out(isbn, student_id)
        except Exception as e:
            # Re-arm for retry on error
            session["checkout_ready"] = True
            raise e

        send_slack_message(
            f"{student_info[1]} borrowed {title}. Please be mindful of late fees if not returned on time."
        )
        message(f"You successfully borrowed {title}", "Notification", 64)

        if student_email:
            try:
                # Original code passed (to, subject, title). Keep compatibility.
                send_gmail(student_email, "", title)
            except Exception:
                pass

        _write_line(Path(f"book_history/{book_barcode}.txt"), f"{current_time} {student_name} borrowed {title}\n")
        _write_line(Path(f"student_history/{student_id}.txt"),f"{current_time} {student_name} borrowed {book_barcode} {title}\n")

        success()
        return render_template("borrowing_complete.html", name=student_name, bookname=title)


@app.route("/admin", methods=["POST","GET"])  # Admin login page
def admin():
    session.pop("student_info", None)
    session.pop("checkout_ready", None)
    return render_template("admin.html")


@app.route("/login", methods=["POST", "GET"])
def adminlogin():
    if request.method == "POST":
        admin_name = request.form.get("admin_name", "").strip()
        password = request.form.get("password", "").strip()
        key = get_key()
        logdata = login(admin_name, password, key)
        if logdata != INVALID and logdata is not None:
            session["admin_name"] = admin_name
            session["admin_logged_in"] = True
            return redirect(url_for("log_page"))
        else:
            return render_template("error.html", error="Invalid login credentials."), 403
    return render_template("admin.html")


@app.route("/credit", methods=["POST", "GET"])  # Credits page
def credit():
    return render_template("credits.html")


# -------------------------
# Login-required routes
# -------------------------
@app.route("/log", methods=["POST", "GET"])  # Admin log dashboard
@login_required
def log_page():
    key = get_key()
    current_borrowed_books_data = borrowed_book_list(key)
    current_borrowed_books_data_with_due_date = []
    for raw in current_borrowed_books_data:
        line = str(raw).replace("\n", " ")
        m = re.search(r"\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s*(?P<rest>.*)", line)
        if not m:
            m2 = re.search(r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(?P<rest>.*)", line)
        else:
            m2 = None
        ts = m.group("ts") if m else (m2.group("ts") if m2 else None)
        rest = m.group("rest") if m else (m2.group("rest") if m2 else line)
        try:
            borrowed_dt = _parse_timestamp_flex(ts) if ts else dt.datetime.now()
            due_dt = borrowed_dt + dt.timedelta(days=14)
            due_str = due_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            due_str = _now_string()
        rest_clean = rest.replace("[", "").replace("]", "").replace("/", "")
        current_borrowed_books_data_with_due_date.append(f"{due_str} {rest_clean}")

    logdata = read_log(key)
    return render_template(
        "log.html",
        logdata=logdata,
        current_borrowed_books_data=current_borrowed_books_data_with_due_date,
    )


@app.route("/register", methods=["POST", "GET"])  # Registration page
def register1():
    
    return render_template("register.html")


@app.route("/register/process", methods=["POST"])  # Registration submit
def registration():
    
    admin_name = request.form.get("admin_name", "")
    password = request.form.get("password", "")
    key = request.form.get("key", "")
    register(admin_name, password, key)
    return redirect(url_for("index"))


@app.route("/about")
def about():
    
    return render_template("about.html")

@app.route('/returnbooks', methods=['POST'])
def return_books():
    book_info = request.form['book_info']
    f = open("borrowed_books.txt", "r", encoding="utf-8")
    lines = f.readlines()
    f.close()
    try:
        for line in lines:
            line = decrypt(line, get_key())
            if book_info[3] in line:
                parts = line.split()
                student_id = parts[2] if len(parts) >= 2 else None
                isbn = parts[3] if len(parts) >= 3 else None
                admin_id = session.get("admin_name", "Unknown Admin")
                student_email = find_student("1 " + student_id)[3] if find_student("1 " + student_id) != 0 else None
                title = ''.join(find_book(isbn)[1:]) if find_book(isbn)!=0 else "Unknown Book"
                break
        return_book(isbn, student_id)
        if student_email:
                try:
                    send_gmail(
                        student_email,
                        f"""Hello, this is Seoul Academy Library.

    We would like to inform you that you have successfully returned the book: '{title}'.

    Thank you for using Seoul Academy Library system.

    Best regards, Seoul Academy.
    """,
                    )
                except Exception:
                    pass
        current_time = strftime("%Y-%m-%d %H:%M:%S", localtime(time.time()))
        student_name = find_student(f". {parts[2]}")[1] + " " + find_student(f". {parts[2]} .")[2]
        # History files
        _write_line(Path(f"book_history/{isbn}.txt"), f"{current_time} {student_name} returned {title}\n")
        _write_line(Path(f"student_history/{parts[2]}.txt"),f"{current_time} {student_name} returned {book_info} {title}\n",)
        return redirect(url_for('log_page'))
    except Exception as e:
        return render_template("error.html", error=f"Error processing return: {str(e)}"), 500



# -------------------------
# Overdue book checker (background thread)
# -------------------------
def check_unreturned_books():
    print("Unreturned Book Checking Is Enabled!")
    key = get_key()
    while True:
        try:
            if not Path("borrowed_books.txt").exists():
                time.sleep(43200)  # 12 hours
                continue
            with open("borrowed_books.txt", "r", encoding="utf-8") as f:
                current_time = dt.datetime.now()
                for line in f:
                    try:
                        dec = decrypt(line, key)
                    except Exception:
                        dec = line
                    parts = dec.split()
                    if len(parts) < 4:
                        continue
                    line_containing_time = parts[0] + " " + parts[1]
                    borrowed_time = _parse_timestamp_flex(line_containing_time)
                    student_id = parts[2]
                    isbn = parts[3]
                    try:
                        book_name = find_book(isbn)[1]
                    except Exception:
                        book_name = isbn
                    days_passed = (current_time - borrowed_time).total_seconds() / (60 * 60 * 24)
                    if days_passed > 14:
                        try:
                            email = find_student("1 " + student_id)[3]
                        except Exception:
                            email = None
                        if email:
                            try:
                                send_gmail(
                                    email,
                                    f"""Hello, this is Seoul Academy Library.

We would like to inform you that you have unreturned books: '{book_name}'.
Please return it as soon as possible, or additional late fees may occur.

Thank you for using Seoul Academy Library system.

Best regards, Seoul Academy.
""",
                                )
                            except Exception:
                                pass
        except Exception as e:
            update_log(f"Overdue check error: {e}")
        time.sleep(43200)  # every 12h


@app.route("/search", methods=["POST"])  # Book history search by ISBN
def search():
    isbn_for_searching = request.form.get("isbn_for_searching", "").strip()
    if not isbn_for_searching:
        return render_template("no_result.html")
    hist_path = Path(f"book_history/{isbn_for_searching}.txt")
    if hist_path.exists():
        history = []
        try:
            name_info = find_book(isbn_for_searching)
            name = " ".join(name_info[1:]) if name_info and len(name_info) > 1 else isbn_for_searching
        except Exception:
            name = isbn_for_searching
        with hist_path.open("r", encoding="utf-8") as f:
            history.extend(f.readlines())
        return render_template("search.html", book_history=history, book_name=name)
    else:
        return render_template("no_result.html")


@app.route("/students", methods=["POST", "GET"])  # List students
@login_required
def students():
    students = []
    path = Path("studentdata.txt")
    if not path.exists():
        return render_template("students.html", student_information=students)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            try:
                sid = int(parts[0])
            except ValueError:
                continue
            student = {
                "id": sid,
                "name": parts[1] + " " + parts[2],
                "email": parts[3],
            }
            students.append(student)
    return render_template("students.html", student_information=students)


@app.route("/students/<int:user_id>")  # Individual student history
@login_required
def individual_students(user_id: int):
    path = Path(f"student_history/{user_id}.txt")
    if not path.exists():
        return render_template("no_result_students.html")
    information = []
    sname = ""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 7:
                continue
            # Format: YYYY-mm-dd HH:MM:SS First Last action isbn Title...
            date = parts[0] + " " + parts[1]
            first = parts[2]
            last = parts[3]
            state = parts[4]
            isbn = parts[5]
            title = " ".join(parts[6:])
            sname = f"{first} {last}"
            information.append({
                "date": date,
                "state": state,
                "isbn": isbn,
                "title": title,
            })
    return render_template("individual_student.html", sname=sname, s_information=information)


# -------------------------
# App entry
# -------------------------
if __name__ == "__main__":
    # Start overdue checker thread (daemon)
    check_unreturned_books_thread = threading.Thread(target=check_unreturned_books, name="overdue-checker", daemon=True)
    check_unreturned_books_thread.start()

    # Use host='0.0.0.0' if running in Docker/remote. Port from env if provided.
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=DEBUG)
