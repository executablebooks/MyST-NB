from pygments.token import Text, Token
import pytest

from myst_nb.core import lexers


@pytest.mark.parametrize(
    ("bold", "faint", "fg_color", "bg_color", "expected"),
    (
        (False, False, False, False, Text),
        (True, False, False, False, Token.Color.Bold),
        (True, False, "Red", False, Token.Color.Bold.Red),
        (True, False, "Red", "Blue", Token.Color.Bold.Red.BGBlue),
        (True, True, "Red", "Blue", Token.Color.Bold.Faint.Red.BGBlue),
    ),
)
def test_token_from_lexer_state(bold, faint, fg_color, bg_color, expected):
    ret = lexers._token_from_lexer_state(bold, faint, fg_color, bg_color)
    assert ret == expected


def _highlight(text):
    return tuple(lexers.AnsiColorLexer().get_tokens(text))


def test_plain_text():
    assert _highlight("hello world\n") == ((Text, "hello world\n"),)


def test_simple_colors():
    assert _highlight(
        "plain text\n"
        "\x1b[31mred text\n"
        "\x1b[1;32mbold green text\n"
        "\x1b[39mfg color turned off\n"
        "\x1b[0mplain text after reset\n"
        "\x1b[1mbold text\n"
        "\x1b[43mbold from previous line with yellow bg\n"
        "\x1b[49mbg color turned off\n"
        "\x1b[2mfaint turned on\n"
        "\x1b[22mbold turned off\n"
    ) == (
        (Text, "plain text\n"),
        (Token.Color.Red, "red text\n"),
        (Token.Color.Bold.Green, "bold green text\n"),
        (Token.Color.Bold, "fg color turned off\n"),
        (Text, "plain text after reset\n"),
        (Token.Color.Bold, "bold text\n"),
        (Token.Color.Bold.BGYellow, "bold from previous line with yellow bg\n"),
        (Token.Color.Bold, "bg color turned off\n"),
        (Token.Color.Bold.Faint, "faint turned on\n"),
        (Text, "bold turned off\n"),
    )


def test_highlight_empty_end_specifier():
    ret = _highlight("plain\x1b[31mred\x1b[mplain\n")
    assert ret == ((Text, "plain"), (Token.Color.Red, "red"), (Text, "plain\n"))


def test_ignores_unrecognized_ansi_color_codes():
    """It should just strip and ignore any unrecognized color ANSI codes."""
    assert _highlight(
        # unknown int code
        "\x1b[99m"
        "plain text\n"
        # invalid non-int code
        "\x1b[=m"
        "plain text\n"
    ) == (
        (Text, "plain text\n"),
        (Text, "plain text\n"),
    )


def test_ignores_valid_ansi_non_color_codes():
    """It should just strip and ignore any non-color ANSI codes.

    These include things like moving the cursor position, erasing lines, etc.
    """
    assert _highlight(
        # restore cursor position
        "\x1b[u"
        "plain "
        # move cursor backwards 55 steps
        "\x1b[55C"
        "text\n"
    ) == (
        # Ideally these would be just one token, but our regex isn't smart
        # enough yet.
        (Text, "plain "),
        (Text, "text\n"),
    )


def test_ignores_completely_invalid_escapes():
    """It should strip and ignore invalid escapes.

    This shouldn't happen in valid ANSI text, but we could have an escape
    followed by garbage.
    """
    assert _highlight("plain \x1b[%text\n") == (
        (Text, "plain "),
        (Text, "%text\n"),
    )
