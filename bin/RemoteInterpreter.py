#!python3
if __name__ == '__main__':
    from sys import argv, exit
    port = argv[-1]
    try:
        port = int(port)
    except ValueError:
        print('Error: Last argument must be port number.')
        exit()
    import floppy.runner
    floppy.runner.spawnRunner(port)
