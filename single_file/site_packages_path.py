import executing

path = executing.__file__
suffix = "/executing/__init__.py"
assert path.endswith(suffix)
path = path[:-len(suffix)]

if __name__ == '__main__':
    print(path)
