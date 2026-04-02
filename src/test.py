import src.util.ToolSelecrot.CatagorySelector as category_selector_module
import src.util.ToolSelecrot.MeetingToolSelector as tool_selector_module


category_selector = category_selector_module.CatagoryToolSelector()
selected_categories = category_selector.query(
    {
        "question": "我昨天有没有没参加的会议",
    }
)
print("selected_categories:", selected_categories)


tool_selector = tool_selector_module.DefaultToolSelector()
selected_tools: list[int] = tool_selector.query(
    {
        "question": "我昨天有没有没参加的会议",
        "category": selected_categories,
    }
)
print("selected_tools:", selected_tools)
