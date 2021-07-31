import sys
import socket

def server(IPADDR, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((IPADDR, int(PORT)))
        s.listen()
        while True:
            clsock, claddr = s.accept()
            print(f"addr: {claddr}")
            clsock.close()

def client(IPADDR, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IPADDR, int(PORT)))
        

def main():
    arg = sys.argv
    if 2 <= len(arg):
        cmd = arg[1]
        if cmd == "sv":
            if 4 <= len(arg):
                server(arg[2], arg[3])
        elif cmd == "cl":
            if 4 <= len(arg):
                client(arg[2], arg[3])
        else:
            print("Unexpected argument(sv or cl)")
    else:
        print("Requires an argument")

if __name__ == "__main__":
    main()
