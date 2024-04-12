import sys
import textwrap
from curtsies import Input, FSArray , CursorAwareWindow, fsarray
from curtsies.fmtfuncs import red, bold, green, on_blue, yellow
import curtsies

from .error import SelectionAborted


def _keys(true, false, default):
    """
    Format keys used for yes/no with the default in upper case

    eg with default=False and y/n for the keys, this should return '[y/N]'
    """
    true = default and true.upper() or true.lower()
    false = (not default) and false.upper() or false.lower()
    return ' [{}/{}]'.format(true, false)


def confirm(prompt, *, true='yes', false='no', default=False, single_key=False, true_key='y', false_key='n', clear=True):
    """
    Get a True/False value from your users

    This removes the need for all validation and repetitive loops to get yes/no
    values from your users.

    Args
    ----
        prompt : str
            A string to display to the user to show what you're asking
    Keyword Args
    ------------
        true : str
            The text to display when choosing the true option
        false : str
            The text to display when choosing the false option
        default : bool
            The default return value if no explicit selection is made
        single_key : bool
            If True, don't require return key to confirm selection
        true_key : str
            The key to select true value - defaults to 'y'.
            Should be a single character.
        false_key : str
            The key to select false value - defaults to 'n'.
            Should be a single character.
        clear : bool
            Clear the prompt after getting the response - defaults to ``True``
    Returns
    -------
        bool
            True or False as selected by the user
    Examples
    --------

        >>> if not confirm('Do you want to continue?'):
        ...     print('Exiting early')
        ...     sys.exit()


    """
    with CursorAwareWindow(out_stream=sys.stderr, extra_bytes_callback=lambda x: x, keep_last_line=not clear) as window:
        prompt = prompt + _keys(true_key, false_key, default)
        width = min(min(window.width, 80) - len(true+false) - 5, len(prompt))
        prompt_arr = fsarray((bold(line) for line in textwrap.wrap(prompt, width=width)), width=window.width)
        choice = fsarray(['  '.join((true, false))])
        window.render_to_terminal(prompt_arr)
        selected = None
        try:
            with Input() as keyGen:
                for i in keyGen:
                    try:
                        if i == true_key:
                            selected = True
                            if single_key:
                                break
                        elif i == false_key:
                            selected = False
                            if single_key:
                                break
                        elif i in ('<LEFT>', '<UP>', '<DOWN>', '<RIGHT>'):
                            selected = not selected
                        elif i == '<Ctrl-j>':
                            if selected is None:
                                selected = default
                            break
                        elif i == '<ESC>':
                            raise SelectionAborted(selected)
                    finally:
                        if (selected is not None):
                            choice = fsarray([true if selected else false])
                            prompt_arr[0:1, width+1:width+len(true+false)+5] = choice
                            window.render_to_terminal(prompt_arr)
        except KeyboardInterrupt as ke:
            raise SelectionAborted(selected) from ke
    return selected

