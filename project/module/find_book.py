def find_book(barcode):
    f = open('isbndata.txt','r')
    barcode = str(barcode)
    while True:
        try:
            line = f.readline()
            if not line: break
            line = [line[0:line.find(' ')],line[line.find(' ')+1:]]
            if(line[0] == barcode): return line
        except Exception as e:
            print(f"Error occurred while finding book: {e}")
    f.close()
    return 0