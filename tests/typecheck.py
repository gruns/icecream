from icecream import IceCreamDebugger, ic
from icecream.icecream import Sentinel


def configure_width(debugger: IceCreamDebugger, width: int) -> None:
    debugger.configureOutput(lineWrapWidth=width)


configure_width(ic, 120)
ic.configureOutput(lineWrapWidth=42)
ic.configureOutput(prefix='debug| ', lineWrapWidth=Sentinel.absent)
ic.configureOutput(prefix='debug| ')
