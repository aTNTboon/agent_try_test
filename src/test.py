import src.util.ToolSelecrot.MeetingToolSelector as sqlTool


tool_selector = sqlTool.DefaultToolSelector()
tools: list[int] = tool_selector.query(
    {
        "question": "meeting search: 我昨天有没有没参加的会议",
    }
)
print(tools)
