import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import strftime,localtime,time
import time
from datetime import timedelta
import datetime
import inspect,logging,re,os
from dotenv import load_dotenv
from project.module.update_log import update_log

def send_gmail(gmail,altmessage = "",bookname = ""):
    if __name__ != "__main__" and gmail != "":
        desired_time = datetime.datetime.now()+ timedelta(days=7)
        date = desired_time.strftime("%Y-%m-%d %I:%M:%S")
        email = "seoulacademylibrary@gmail.com"
        load_dotenv()
        password = os.getenv("gmailpassword")
        subject = "Seoul Academy Library"
        bookname = re.sub(r'\n', '', bookname)
        message = f"""Hello, this is Seoul Academy Library.

We would like to inform you that you have borrowed the book: '{bookname}'.
You must return the book until {date}, else it would cause an initial fine of ₩2000, and additional ₩1000 per day.

Thank you for using Seoul Academy Library system.

Best regards, Seoul Academy.
        """
        if altmessage != "":
            message = altmessage
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = gmail
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, password)
            server.sendmail(email, gmail, msg.as_string())
            server.quit()
            update_log(12,gmail)
        except Exception as e:
            print(f"Fatal Error while sending an email: {e}")
            update_log(f"Fatal Error while sending an email: {e}")
    else:
        print("Warning! Please do not open this file!")