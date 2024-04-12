import sys
import warnings

from curtsies import Input, FSArray , CursorAwareWindow, fsarray
from curtsies.fmtfuncs import red, bold, green, on_blue, yellow

from .error import SelectionAborted

import random

CHECKED = '\u25c9 '
UNCHECKED = '\u25cc '

def _no_fmt(s):
    return s

def choose(prompt, choices, multi=False, preselected=()):
    """
    Offer a range of options to the user and return their selection

    Args
    ----
    prompt : str
        The prompt to display to the users above the options
    choices : iterable
        The range of choices to offer to the user.

        * If this is a ``dict`` type, the ``__str__`` representation of the keys
          are displayed to the user and the corresponding values are returned.
        * Otherwise, the ``__str__`` representation of each option is
          displayed and the original objects are returned.

    Keyword Args
    ------------
    multi : bool
        Whether the user can choose multiple options
        Defaults to False
    preselected : iterable
        Optional argument when choosing multiple options
        set a preselection of values using a list
        * for ``dict`` type choices use a list of keys
        * for ``list`` type choices use a list of indices
        Defaults to tuple() (No preselection)
    Returns
    -------
        object
            If multi is ``False``, return the selected option.
            The returned object is the same instance as that passed in.
        list
            If multi is ``True``, return a list of the users choices. This
            may be an empty list if no choices are made.
            The instances are the same as those passed in.

    Raises
    ------
        ValueError
            If the list of options is ``None`` or empty
    Examples
    --------
    Using a list of options and picking one:

        >>> options = ['Option %d' %i for i in range(10)]
        >>> choose('Choose an option', options)
        'Option 3'

    Using a dict of options and picking several

        >>> options = {'One': 1, 'Two': 2, 'Three': 3}
        >>> choose('Choose multiple options', options, multi=True)
        [1, 2]
    """

    choice_list = ChoiceList(choices, prompt=prompt, multi=multi, preselected=preselected)
    with CursorAwareWindow(out_stream=sys.stderr, extra_bytes_callback=lambda x: x) as window:
        options = choice_list.run(window)

    return options

class Choice:
    def __init__(self, obj, display=None):
        self._obj = obj
        self._disp = display

    def __str__(self):
        if self._disp is None:
            self._disp = str(self._obj)
        return self._disp

    def render(self, fmt, width):
        lines = str(self).split('\n')
        arr = fsarray(fmt(line) for line in lines)
        return arr


class ChoiceList:
    def __init__(self, choices, prompt=None, multi=False, preselected=(), sel_fmt=bold, des_fmt=_no_fmt, selected=CHECKED, deselected=UNCHECKED):
        if prompt:
            self._prompt = fsarray([bold(line) for line in prompt.split('\n')])
        else:
            self._prompt = prompt
        if multi is True:
            multi = (0, len(choices))
        self._multi = multi
        if not choices:
            raise ValueError('No choices given')
        if not self._multi:
            if preselected:
                warnings.warn("Preselection is only available for multiple choices", category=RuntimeWarning)
            preselected = []

        if isinstance(choices, dict):
            self._choices = [[k in preselected, Choice(v, k)] for k, v in choices.items()]
        else:
            self._choices = [[i in preselected, Choice(c)] for i, c in enumerate(choices)]
        self._sel_fmt = sel_fmt
        self._des_fmt = des_fmt
        self._sel = selected
        self._des = deselected
        self._idx = 0

    def run(self, window):
        opt_arr = self.render(window.width)
        window.render_to_terminal(opt_arr)
        try:
            with Input() as keyGen:
                for key in keyGen:
                    if key == '<UP>':
                        self.prev()
                    elif key == '<DOWN>':
                        self.next()
                    elif key == '<SPACE>':
                        if self._multi:
                            self.toggle()
                    elif key == '<Ctrl-j>':
                        break
                    elif key == '<ESC>':
                        raise SelectionAborted(self.get_selection())
                    else:
                        continue
                    window.render_to_terminal(self.render(window.width))
        except KeyboardInterrupt as ke:
            raise SelectionAborted(self.get_selection()) from ke

        return self.get_selection()

    def toggle(self):
        state = self._choices[self._idx]
        state[0] = not state[0]

    def select(self, index):
        self._idx = index

    def render(self, width):
        arr = fsarray('', width=width)
        if self._prompt:
            arr.rows = self._prompt.rows + arr.rows
        l = len(arr)
        for checked, option in self._choices:
            current = self._choices[self._idx][1] == option
            fmt = self._sel_fmt if current else self._des_fmt
            opt_arr = option.render(fmt, width-3)
            arr[l:l+len(opt_arr), 2:width] = opt_arr
            if self._multi:
                state = self._sel if checked else self._des
            else:
                state = '> ' if current else '  '
            arr[l:l+1, 0:2] = fsarray([state])
            l += len(opt_arr)
        return arr

    def get_selection(self):
        options = [item[1]._obj for item in self._choices if item[0]]
        if self._multi:
            return options
        elif options:
            return options[0]
        return self._choices[self._idx][1]._obj

    def next(self):
        self._idx = min(len(self)-1, self._idx+1)

    def prev(self):
        self._idx = max(0, self._idx-1)

    def __len__(self):
        return len(self._choices)

    def __getitem__(self, key):
        item = self._choices[key]
        return item[1]._obj

    def __setitem__(self, key, value):
        self._choices[key] = [False, Choice(value)]

    def __delitem__(self, key):
        del self._choices[key]

    def __contains__(self, item):
        return item in [i[1]._obj for i in self._choices]


if __name__ == "__main__":
    c = choose('Prompt \n line 2: ', ['abc', 'def', 'ghi', 'jkl', 'mno'])
