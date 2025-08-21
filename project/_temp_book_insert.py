while True:
    barcode = input("바코드를 입력하세요: ")
    name = input("제목을 입력하세요")
    with open("isbndata.txt","a", encoding="utf-8") as f:
        f.write(f"\n{barcode} {name}")
    print("완료!\n")