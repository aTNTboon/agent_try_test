from dataclasses import dataclass


@dataclass
class ToolMeta:
    id: int
    code: str
    name: str
    description: str
    category: str
    handler: str
    enabled: bool = True
