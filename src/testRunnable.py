from typing import Any

from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig

class test(Runnable):
    def __init__(self):
        super().__init__()

    def run(self):
        pass

    def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        print('test')
        print(input)
        print("__________________")
        print("__________________")
        print("__________________")
        return super().invoke(input, config, **kwargs)
    
class test2(Runnable):
    def __init__(self):
        super().__init__()

    def run(self):
        pass

    def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        print('test2')
        print(input)
        print("__________________")
        print("__________________")
        print("__________________")
        return input


if __name__ == "__main__":
    t = test()
    t2 = test2()
    chain= t|t2
    chain.invoke(input="hello")