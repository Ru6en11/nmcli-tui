from curtsies import Input, FSArray, CursorAwareWindow, fsarray
from curtsies.events import PasteEvent
from curtsies.fmtfuncs import red, bold, green, on_blue, yellow
import sys
import textwrap
import itertools
from collections import namedtuple
import enum
import re
blank = re.compile(r'^\s+')


WORD_BREAK = re.compile('[^\w]')

Cursor = namedtuple('Cursor', ['row', 'column'])


class Dir(enum.Enum):
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4

class Document:
    def __init__(self, text='', cursor=None):
        if cursor is None:
            cursor = len(text)
        self._lbuffer = text[:cursor]
        self._rbuffer = text[cursor:]

    def handle(self, key):
        if len(key) == 1:
            self.add(key)
        elif key == '<SPACE>':
            self.add(' ')
        elif key == '<BACKSPACE>':
            self.bksp()
        elif key == '<DELETE>':
            self.bksp(Dir.RIGHT)
        elif key == '<Ctrl-j>':
            self.add('\n')

    def add(self, key):
        self._lbuffer += key

    def bksp(self, direction=Dir.LEFT):
        if direction == Dir.LEFT:
            self._lbuffer = self._lbuffer[:-1]
        elif direction == Dir.RIGHT:
            self._rbuffer = self._rbuffer[1:]

    def move_cursor(self, direction=Dir.LEFT, chars=1):
        if direction == Dir.LEFT:
            if self._lbuffer:
                c = self._lbuffer[-chars:]
                self._lbuffer = self._lbuffer[:-chars]
                self._rbuffer = c + self._rbuffer
        elif direction == Dir.RIGHT:
            if self._rbuffer:
                c = self._rbuffer[:chars]
                self._lbuffer += c
                self._rbuffer = self._rbuffer[chars:]
        elif direction == Dir.UP:
            split = self._lbuffer.rsplit('\n', 2)
            if len(split) == 1:
                return
            left = '\n'.join((*split[:-2], split[-2][:len(split[-1])]))
            old_len = len(self._lbuffer)
            new_len = len(left)
            self._lbuffer, self._rbuffer = self._lbuffer[:new_len], self._lbuffer[new_len:] + self._rbuffer
        elif direction == Dir.DOWN:
            rs = self._rbuffer.split('\n', 2)
            if len(rs) == 1:
                return
            ls = self._lbuffer.rsplit('\n', 1)
            indent = len(ls[-1])
            self._lbuffer, self._rbuffer = (
                    self._lbuffer + rs[0] + '\n' + rs[1][:indent],
                    '\n'.join((rs[1][indent:], *rs[2:]))
            )

    def end_line(self, right):
        if right: # move to end of line
            line_break = self._rbuffer.find('\n')
            if line_break == -1:
                self._lbuffer, self._rbuffer = self._lbuffer + self._rbuffer, ''
                return
            self.move_cursor(Dir.RIGHT, line_break)
        else: # move to start of line
            line_break = self._lbuffer.rfind('\n')
            if line_break == -1:
                self._lbuffer, self._rbuffer = '', self._lbuffer + self._rbuffer
                return
            to_move =len(self._lbuffer) - line_break - 1
            self.move_cursor(Dir.LEFT, to_move)

    def move_word(self, direction=Dir.LEFT, delete=False):
        if direction == Dir.LEFT:
            words = WORD_BREAK.split(self._lbuffer)
            spaces = 0
            while spaces < len(words)-1 and words[-1-spaces] == '':
                spaces += 1
            last_word = words[-1-spaces]
            self._lbuffer, self._rbuffer = (
                    self._lbuffer[:-len(last_word)-spaces],
                    (self._lbuffer[-len(last_word)-spaces:] + self._rbuffer) if not delete else self._rbuffer
            )
        elif direction == Dir.RIGHT:
            words = WORD_BREAK.split(self._rbuffer)
            spaces = 0
            while spaces < len(words)-1 and words[spaces] == '':
                spaces += 1
            first_word = words[spaces]
            self._lbuffer, self._rbuffer = (
                    (self._lbuffer + self._rbuffer[:len(first_word)+spaces]) if not delete else self._lbuffer,
                    self._rbuffer[spaces+len(first_word):]
            )

    @property
    def lines(self):
        return str(self).split('\n')

    @property
    def cursor(self):
        lines = self._lbuffer.split('\n')
        return Cursor(len(lines)-1, len(lines[-1]))

    def __str__(self):
        return self._lbuffer+self._rbuffer

def prompt(message):
    """
    Request text input from the user

    Args
    ----
    message : str
        The prompt to display to the user
    Returns
    -------
    str
        The text entered by the user
    Examples
    --------
        >>> prompt('Enter some text:')
        'This text was entered'
    """
    with CursorAwareWindow(out_stream=sys.stderr, extra_bytes_callback=lambda x:x, hide_cursor=False) as window:
        left = window.width//3 -1
        prompt = textwrap.wrap(message, left) + ['']
        p_lines = len(prompt)
        right = window.width - max(len(line) for line in prompt) - 1
        left = window.width - right - 1
        document = Document()
        view = FSArray(p_lines, window.width)
        view[0:p_lines, 0:left] = [bold(line) for line in prompt]
        window.render_to_terminal(view, (0, left+1))
        with Input() as keys:
            for key in keys:
                if key == '<Ctrl-j>': # return
                    window.render_to_terminal([], (0,0))
                    return str(document)
                if key == '<Esc+Ctrl-J>': # alt-return
                    document.handle('<Ctrl-j>')
                elif key == '<LEFT>':
                    document.move_cursor(Dir.LEFT)
                elif key == '<RIGHT>':
                    document.move_cursor(Dir.RIGHT)
                elif key == '<UP>':
                    document.move_cursor(Dir.UP)
                elif key == '<DOWN>':
                    document.move_cursor(Dir.DOWN)
                elif key == '<Ctrl-LEFT>':
                    document.move_word(Dir.LEFT)
                elif key == '<Ctrl-RIGHT>':
                    document.move_word(Dir.RIGHT)
                elif key == '<Ctrl-w>':
                    document.move_word(Dir.LEFT, delete=True)
                elif key == '<Ctrl-DELETE>':
                    document.move_word(Dir.RIGHT, delete=True)
                elif key in ('<Ctrl-a>', '<HOME>'):
                    document.end_line(0)
                elif key in ('<Ctrl-e>', '<END>'):
                    document.end_line(1)
                elif isinstance(key, PasteEvent):
                    for c in key.events:
                        document.handle(c)
                else:
                    document.handle(key)

                # Add an extra blank line to force clearing of trailing text
                text = document.lines + [' ']
                lines, cursor = _wrap(text, document.cursor, right)
                rows = list(lines)
                # Replace the right column with input text
                view[0:len(rows), left+1:window.width] = rows
                window.render_to_terminal(view, (cursor.row, cursor.column+left+1))


def _wrap(text, cursor, width):
    """Convert an iterable of lines to an iterable of wrapped lines"""
    text = [textwrap.wrap(line, width - 1, drop_whitespace=False) or [''] for line in text]
    previous_lines = sum(len(line) for line in text[:cursor.row])
    current_line = text[cursor.row]
    row, column = _current_word(current_line, cursor.column)
    if column < 0:
        row = max(0, row-1)
        column = width
    text[cursor.row] = [line.lstrip() for line in current_line]
    row += previous_lines
    return itertools.chain(*text), Cursor(row, column)


def _current_word(words, column):
    count = 0
    lines = len(words)
    for i, w in enumerate(words):
        # Leading whitespace
        m = blank.match(w)
        if m:
            column -= m.span()[1]
        if column == 0:
            return 0,0
        end = count + len(w)
        if column < end:
            return (i, column-count)
        if column == end:
            if i == lines - 1: # end of last line
                return i, column - count
            return i+1, 0
        count += len(w)
    else:
        raise ValueError('column %d is not in words (%s)' %(column, words))
