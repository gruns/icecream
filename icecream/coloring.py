# -*- coding: utf-8 -*-

#
# IceCream - Never use print() to debug again
#
# Ansgar Grunseid
# grunseid.com
# grunseid@gmail.com
#
# License: MIT
#

from pygments.style import Style
from pygments.token import (
    Text, Name, Error, Other, String, Number, Keyword, Generic, Literal,
    Comment, Operator, Whitespace, Punctuation)


# Solarized: https://ethanschoonover.com/solarized/
class SolarizedDark(Style):

    BASE03  = '#002b36' # noqa
    BASE02  = '#073642' # noqa
    BASE01  = '#586e75' # noqa
    BASE00  = '#657b83' # noqa
    BASE0   = '#839496' # noqa
    BASE1   = '#93a1a1' # noqa
    BASE2   = '#eee8d5' # noqa
    BASE3   = '#fdf6e3' # noqa
    YELLOW  = '#b58900' # noqa
    ORANGE  = '#cb4b16' # noqa
    RED     = '#dc322f' # noqa
    MAGENTA = '#d33682' # noqa
    VIOLET  = '#6c71c4' # noqa
    BLUE    = '#268bd2' # noqa
    CYAN    = '#2aa198' # noqa
    GREEN   = '#859900' # noqa

    styles = {
        Text:                   BASE0,
        Whitespace:             BASE03,
        Error:                  RED,
        Other:                  BASE0,

        Name:                   BASE1,
        Name.Attribute:         BASE0,
        Name.Builtin:           BLUE,
        Name.Builtin.Pseudo:    BLUE,
        Name.Class:             BLUE,
        Name.Constant:          YELLOW,
        Name.Decorator:         ORANGE,
        Name.Entity:            ORANGE,
        Name.Exception:         ORANGE,
        Name.Function:          BLUE,
        Name.Property:          BLUE,
        Name.Label:             BASE0,
        Name.Namespace:         YELLOW,
        Name.Other:             BASE0,
        Name.Tag:               GREEN,
        Name.Variable:          ORANGE,
        Name.Variable.Class:    BLUE,
        Name.Variable.Global:   BLUE,
        Name.Variable.Instance: BLUE,

        String:                 CYAN,
        String.Backtick:        CYAN,
        String.Char:            CYAN,
        String.Doc:             CYAN,
        String.Double:          CYAN,
        String.Escape:          ORANGE,
        String.Heredoc:         CYAN,
        String.Interpol:        ORANGE,
        String.Other:           CYAN,
        String.Regex:           CYAN,
        String.Single:          CYAN,
        String.Symbol:          CYAN,

        Number:                 CYAN,
        Number.Float:           CYAN,
        Number.Hex:             CYAN,
        Number.Integer:         CYAN,
        Number.Integer.Long:    CYAN,
        Number.Oct:             CYAN,

        Keyword:                GREEN,
        Keyword.Constant:       GREEN,
        Keyword.Declaration:    GREEN,
        Keyword.Namespace:      ORANGE,
        Keyword.Pseudo:         ORANGE,
        Keyword.Reserved:       GREEN,
        Keyword.Type:           GREEN,

        Generic:                BASE0,
        Generic.Deleted:        BASE0,
        Generic.Emph:           BASE0,
        Generic.Error:          BASE0,
        Generic.Heading:        BASE0,
        Generic.Inserted:       BASE0,
        Generic.Output:         BASE0,
        Generic.Prompt:         BASE0,
        Generic.Strong:         BASE0,
        Generic.Subheading:     BASE0,
        Generic.Traceback:      BASE0,

        Literal:                BASE0,
        Literal.Date:           BASE0,

        Comment:                BASE01,
        Comment.Multiline:      BASE01,
        Comment.Preproc:        BASE01,
        Comment.Single:         BASE01,
        Comment.Special:        BASE01,

        Operator:               BASE0,
        Operator.Word:          GREEN,

        Punctuation:            BASE0,
    }
