import sys
import getopt


#get instance name from param
def load_param():

    name1 = None 
    name2 = None
    program = None
    argv = sys.argv[1:]
 
    try:
        opts, args = getopt.getopt(argv, "f:s:p:")  # 短选项模式
     
    except:
        print("Error")
 
    for opt, arg in opts:
        if opt in ['-f']:
            name1 = arg
        if opt in ['-s']:
            name2 = arg
        if opt in ['-p']:
            program = arg

    return name1, name2, program