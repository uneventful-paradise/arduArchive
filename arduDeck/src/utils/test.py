import platform, sys

print('Impl:', platform.python_implementation())
print('Version:', sys.version.split()[0])
print('Arch:', platform.architecture()[0])
print('Exe:', sys.executable)