import os
import subprocess as sp

from .connection import Connection
from .nmcli_parser import NmcliParser

class ConnectionManager:

    __nmcli_parser: NmcliParser = NmcliParser()
    
    def active_connection_by_name(self, connection: Connection) -> None:
        os.system(f'nmcli connection up id "{connection.name}"')

    def deactivate_connecion_by_name(self, connection: Connection) -> None:
        os.system(f'nmcli connection down id "{connection.name}"')

    def get_active_connections(self) -> list[Connection]:
        completed_process: sp.CompletedProcess = sp.run(['nmcli', 'connection', 'show', '--active'], capture_output=True)
        output: str = completed_process.stdout.decode()

        try: 
            connections: list[Connection] = self.__nmcli_parser.connection_show_output_to_connections(output)

            return connections
        except:
            return []

    def is_active_connection(self, connection) -> bool:
        completed_process = sp.run(f'nmcli connection show --active | grep "{connection}"', shell=True, capture_output=True)
        if len(completed_process.stdout.decode()) == 0: return False
        
        return True

    def get_connections(self) -> list[Connection]:

        completed_process: sp.CompletedProcess = sp.run(['nmcli', 'connection'], capture_output=True)
        output = completed_process.stdout.decode()
        
        try:
            connections: list[Connection] = self.__nmcli_parser.connection_show_output_to_connections(output)

            return connections
        except: 
            return []

