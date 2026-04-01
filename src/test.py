import src.util.ToolSelecrot.SQLToolSelector as sqlTool


tool_selector = sqlTool.DefaultToolSelector()
tools:list[int] = tool_selector.query("查询天气")
print(tools)

