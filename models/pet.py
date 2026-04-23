from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    notes: str = ""
