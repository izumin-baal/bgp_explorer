def main():
    data = bgp()
    arg = sys.argv
    if 2 <= len(arg):
        cmd = arg[1]
        if cmd == "sv":
            if 4 <= len(arg):
                server(arg[2], arg[3])
        elif cmd == "cl":
            if 4 <= len(arg):
                client(arg[2], arg[3], data)
        else:
            print("Unexpected argument(sv or cl)")
    else:
        print("Requires an argument")

if __name__ == "__main__":
    main()
