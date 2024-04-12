class SelectionAborted(Exception):
    def __init__(self, current_selection):
        self.current = current_selection
