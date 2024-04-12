import os
import enquiries as tui
import subprocess as sp

from .connection_manager import Connection, ConnectionManager
from .tools.connections_to_list_string import connections_to_list_string 


def main():

    connection_manager: ConnectionManager = ConnectionManager()
    connections: list[Connection] = connection_manager.get_connections()

    connection_names = connections_to_list_string(connections)

    if len(connections) == 0:
        print('Connections not found')
        return

    choise = tui.choose("Choose one of connections: ", connections)

    print(type(choise))

