
# # Warning! this code is not used anymore, but I wanted to leave a mark on what we have overcame. Thank you!
# # Taehun Kim




# import ctypes
# import winsound as sd
# from os import system
# from time import localtime,time
# from project.module.find_book import *
# from project.module.find_student import *
# from project.module.return_book import *
# from project.module.check_out import * 
# from project.module.is_in_borrowed_books import *
# from project.module.update_log import *
# from project.module.update_borrowed_books import *
# from project.module.update_fine import *
# from project.module.send_gmail import *
# import slack_sdk
# INVALID = 0
# YES = 1
# NO = 0
# PERIOD = 7

# slack_token = 'xoxb-7003132549716-6997776435477-EAzMiYwySutbpcUwdVvaTVmS'

# client = slack_sdk.WebClient(token=slack_token)

# def message(msg,title="ERROR",code = 16):
#     ctypes.windll.user32.MessageBoxW(0, msg, title, code, 0x00010000)

# def slackmessage(msg):
#     client.chat_postMessage(channel='#seoul-academy-library-messenger',text = msg)

# def beep(fr = 2000, tm = 700):
#     sd.Beep(fr,tm)

# def success():
#     beep(440,350)
#     beep(659,350)

# f = open("logfile.txt",'a')
# f = open("studentdata.txt",'a')
# f = open("isbndata.txt",'a')
# f = open("borrowed_books.txt",'a')
# f = open("admin.txt",'a')
# f.close()

# tm = localtime(time.time())
# update_log(7)
# def main():
#     while(True):
#         try:
#             while(True):
#                 barcode = 0
#                 s_id = 0
#                 isbn = 0
#                 student_name = ''
#                 barcode = str(input("Please scan the id card. "))
#                 system('cls')
#                 if(find_student(barcode) == 0):
#                     message("Either you are not yet registered or the input is wrong. ")
#                     update_log(3, barcode[1])
#                     system('cls')
#                     continue
#                 s_id = find_student(barcode)[0]
#                 student_name = find_student(barcode)[1]+ " " + find_student(barcode)[2]
#                 try:
#                     email_address = find_student(barcode)[3]
#                 except:
#                     email_address = ""
#                 if not s_id == INVALID: break
#             update_log(5,s_id)
#             while(True):
#                 print("Hello, " + student_name+ ", ", end = '')
#                 barcode = str(input("Please scan the book that you might want to borrow or return. "))
#                 system('cls')
#                 if(find_book(barcode) == 0):
#                     message("Either the books is not yet registered or the input is wrong. ")
#                     update_log(4,s_id,barcode)
#                     system('cls')
#                     continue
#                 isbn = find_book(barcode)[0]
#                 if not isbn == INVALID: break
#             update_log(6,s_id,isbn)
#             system('cls')
#             if(is_in_borrowed_books(isbn,s_id) == YES):
#                 return_book(isbn,s_id)
#                 client.chat_postMessage(channel='#seoul-academy-library-messenger',text = f"{student_name} returned {re.sub(r'\n', '', find_book(isbn)[1])}.")
#                 print("Thank you for using the Library Checkout System Developed by Seoul Academy Computer Club.")
#                 success()
#                 message("You successfully returned " + find_book(isbn)[1],"notification",64)
#                 send_gmail(find_student("1 " + s_id)[3],f"""Hello, this is Seoul Academy Library.

# We would like to inform you that you have successfully returned the book: '{re.sub(r'\n', '', find_book(isbn)[1])}'.

# Thank you for using Seoul Academy Library system.

# Best regards, Seoul Academy.
# """)

#             else:
#                 check_out(isbn,s_id)
#                 client.chat_postMessage(channel='#seoul-academy-library-messenger',text = f"{student_name} borrowed {re.sub(r'\n', '', find_book(isbn)[1])}. Please be in mind that there would be late fees if you don't return it on time.")
#                 print("Thank you for using the Library Checkout System Developed by Seoul Academy Computer Club.")
#                 success()
#                 message("You successfully borrowed " + find_book(isbn)[1],"notification",64)
#                 send_gmail(email_address,"",find_book(isbn)[1])
#             system('cls')
#             continue
#         except Exception as e:
#             update_log("Error: " + str(e))
#             print(str(e))
#             beep(880)

# if __name__ == "__main__":
#     main()
#THIS FILE IS NOT USED ANYMORE!!!