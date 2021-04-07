"""
Utility to see which version files differ.
"""

from collections import defaultdict
from glob import glob
from pathlib import Path

result = defaultdict(list)

for filename in glob("icecream_*.py"):
    group = result[hash(Path(filename).read_text())]
    group.append(filename.replace("icecream_", "").replace(".py", ""))
    group.sort()

for group in sorted(result.values()):
    print(group)

"""
The result is that the files fall into these groups:
['py27', 'pypy27']
['py35', 'pypy35']
['py36', 'py37', 'py38', 'py39', 'pypy36']
"""
