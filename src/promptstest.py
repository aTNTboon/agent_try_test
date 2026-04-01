import json
import requests
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate

# ========== 配置硬编码 ==========
API_URL = "https://spark-api-open.xf-yun.com/v2/chat/completions"
API_KEY = "Bearer ZXSdpSgEJXFhygMYiiaA"   # 已包含 Bearer
MODEL = "x1"
TEMPERATURE = 0.7
ApiSecret = "jDalRRbmMsQBXJeiCUAa"
# ========== 定义 few-shot 模板 ==========
example_data = [
    {"word": "cat", "antonym": "dog"},
    {"word": "house", "antonym": "tree"},
    {"word": "car", "antonym": "bus"},
]
prompt_template = PromptTemplate.from_template("单词：{word},反义词{antonym}")
few_shot_prompt = FewShotPromptTemplate(
    example_prompt=prompt_template,
    examples=example_data,
    prefix="告知单词反义词，以下是例子",
    suffix="基于前面的例子，告诉我接下来词语的反义词 {input_word}",
    input_variables=['input_word'],
)
