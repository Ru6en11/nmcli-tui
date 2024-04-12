from ..connection import Connection
def connections_to_list_string(connections: list[Connection]) -> list[str]:
    connection_names: list[str] = []

    for connection in connections:
        connection_names.append(connection.name)

    return connection_names
