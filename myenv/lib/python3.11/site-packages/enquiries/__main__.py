#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys

from enquiries import choose
from enquiries import freetext
from enquiries import yesno


def free(args):
    user_input = freetext(args.prompt or '')
    # If we're not being quiet and stdout is not being redirected, write the prompt
    if args.prompt and not args.quiet and sys.stdout.isatty():
        print(args.prompt or '', file=sys.stderr)
    # always print the output
    print(user_input)


def select(args):
    choice = choose(args.prompt, args.OPTIONS, multi=args.multi)
    # if not quiet, print everything
    if not args.quiet and args.prompt:
        print(args.prompt + ' ', file=sys.stderr, end='\n' if args.multi else '')
    # if we're being piped to somewhere else, always print choice
    if not args.quiet or not sys.stdout.isatty():
        print('\n'.join(choice))


def confirm(args):
    """Prompt user for a yes/no response"""
    exit(not yesno.confirm(args.prompt or 'Continue? ', single_key=True, default=args.default_true, clear=args.quiet))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Take useful user input')
    parser.add_argument('-p', '--prompt', help='Prompt to display')
    parser.add_argument('-q', '--quiet',  action='store_true', help='Hide prompt after closing')

    subparsers = parser.add_subparsers(dest='option')
    select_parser = subparsers.add_parser('select', help='Select from multiple options')
    select_parser.add_argument('-m', '--multi', action='store_true', help='Choose multiple options')
    select_parser.add_argument('OPTIONS', nargs="+", help='Options to choose from')
    select_parser.set_defaults(func=select)

    free_parser = subparsers.add_parser('free', help="Get a roughly readline-ish prompt")
    free_parser.set_defaults(func=free)

    confirm_parser = subparsers.add_parser('confirm', help='Get a yes/no answer')
    confirm_parser.add_argument('-t', '--default-true', action='store_true', help='Default to true instead of false')
    confirm_parser.set_defaults(func=confirm)

    args = parser.parse_args()
    args.func(args)
