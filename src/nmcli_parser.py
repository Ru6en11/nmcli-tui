import subprocess as sp
from .connection import Connection

class NmcliParser:
    
    def connection_show_output_to_connections(self, output: str) -> list[Connection]:
        connections: list[Connection] = []

        rows: list[str] = output.split('\n')
        header: str = rows[0]
        connection_name_end_index: int = header.find('UUID')
        connection_uuid_end_index: int = header.find('TYPE')
        connection_interface_end_index: int = header.find('DEVICE')

        if (connection_name_end_index == -1 or
            connection_uuid_end_index == -1 or
            connection_interface_end_index == -1): raise Exception(f'Failed to parse output data\n{output}')

        rows.remove(header)
        
        for row in rows:
            name: str = row[:connection_name_end_index].strip()
            uuid: str = row[connection_name_end_index:connection_uuid_end_index].strip()
            interface: str = row[connection_uuid_end_index:connection_interface_end_index].strip()
            device: str = row[connection_interface_end_index:].strip()

            completed_process: sp.CompletedProcess = sp.run(f'nmcli connection show --active | grep "{name}"', shell=True, capture_output=True)
            if len(completed_process.stdout.decode()) != 0: name = "\u001b[32m" + name
 
            if len(name) == 0: continue
            connection: Connection = Connection(name=name, uuid=uuid, interface=interface, device=device)

            connections.append(connection) 
        
        return connections
