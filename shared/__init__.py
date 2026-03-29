import shared.bytes, shared.packet

def get_arg(arg_name):
    import sys
    for index, arg in enumerate(sys.argv):
        if arg == arg_name and index < len(sys.argv) - 1:
            return sys.argv[index + 1].strip("'").strip('"')

    return
