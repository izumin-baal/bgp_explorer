import sys
import socket

def server(IPADDR, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((IPADDR, int(PORT)))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print("Connected by ", addr)
            while True:
                data = conn.recv(1024)
                if not data: break
                conn.sendall(data)

def client(IPADDR, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IPADDR, int(PORT)))
        s.sendall(b"Hello BGP")
        data = s.recv(1024)
    print('Received', repr(data))
        

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
