import sys
import site_packages_path
sys.path.remove(site_packages_path.path)
del sys.modules["executing"]
del sys.modules["executing.executing"]

from single_file_icecream import ic

ic(ic(1+2))
