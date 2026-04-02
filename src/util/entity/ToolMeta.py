from openai import BaseModel


class ToolMeta(BaseModel):
    id: int
    code: str
    name: str
    description: str
    category: str
    enabled: bool = True
    handler: str