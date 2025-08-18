from time import localtime, time, strftime
from time import struct_time
from project.module.update_log import * 
from project.module.send_gmail import send_gmail
import ctypes
import time,slack_sdk

slack_token = 'xoxb-7003132549716-6997776435477-EAzMiYwySutbpcUwdVvaTVmS'

client = slack_sdk.WebClient(token=slack_token)

def slackmessage(msg):
    client.chat_postMessage(channel='#seoul-academy-library-messenger',text = msg)

def message(msg,title="ERROR"):
    ctypes.windll.user32.MessageBoxW(0, msg, title, 64, 0x00010000)

def update_fine(s_id: str, current_time: struct_time, borrowed_time: struct_time):
    int_current_time = time.mktime(current_time)
    int_borrowed_time = time.mktime(borrowed_time)
    days_passed = int(int_current_time-int_borrowed_time)/(60*60*24)
    fine = 0
    if days_passed > 14:
        days_passed = int(days_passed)
        fine = 1000*(days_passed-15) # change this if there is a change in policies
        update_log(11,s_id,str(fine))
        name = find_student("1 " + s_id)[1] + " " + find_student("1 " + s_id)[2]
        slackmessage(f"Dear {name}, please be noticed that you have a late fee of ₩{fine} since you have passed the return date.")
        send_gmail(find_student("1 " + s_id)[3],f"""
This is Seoul Academy Library.                   

Dear {name}, please be noticed that you have a late fee of ₩{fine} since you have passed the return date.

Thank you for using Seoul Academy Library system.

Best regards, Seoul Academy.
""")
    return fine

