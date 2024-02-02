from typing import Dict
from pygments.style import Style
from pygments.token import _TokenType

class SolarizedDark(Style):
    BASE03: str
    BASE02: str
    BASE01: str
    BASE00: str
    BASE0: str
    BASE1: str
    BASE2: str
    BASE3: str
    YELLOW: str
    ORANGE: str
    RED: str
    MAGENTA: str
    VIOLET: str
    BLUE: str
    CYAN: str
    GREEN: str
    styles: Dict[_TokenType, str]
