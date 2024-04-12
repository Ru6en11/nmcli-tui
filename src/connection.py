from dataclasses import dataclass

@dataclass(frozen=True)
class Connection:

    name: str
    uuid: str
    interface: str
    device: str
    
    def __str__(self) -> str:
        return self.name
    
