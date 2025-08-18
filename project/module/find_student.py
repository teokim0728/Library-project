def find_student(barcode):
    f = open("logfile.txt",'a')
    f = open("studentdata.txt",'r')
    barcode = str(barcode).split()
    while True:
        try:
            line = f.readline()
            if not line: break
            line = line.split()
            if(line[0] == barcode[1]): return line
        except:
            pass
    f.close()
    return 0