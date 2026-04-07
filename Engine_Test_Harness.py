import os
import json
import re
from typing import List
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI

# ==========================================
# L1 物理环境与配置
# ==========================================
# 请替换为你真实的 DeepSeek API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your DEEPSEEK_API_KEY")
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# ==========================================
# L2 本体层：强类型 JSON 契约 (Pydantic)
# ==========================================
class ActionItem(BaseModel):
    owner: str = Field(..., description="执行人")
    task: str = Field(..., description="具体任务")
    deadline: str = Field(..., description="死线/时间节点")

class BizScribeContract(BaseModel):
    summary: str = Field(..., description="高管摘要（限 100 字内）")
    decisions: List[str] = Field(..., description="已确认的商业决议")
    action_items: List[ActionItem] = Field(..., description="待办事项及责任人")
    risks: List[str] = Field(..., description="潜在风控预警（违背前置SOW或商业常识的点）")

# ==========================================
# 核心引擎：Contract Collapse Logic
# ==========================================
class CollapseEngine:
    def __init__(self, sow_context: str = ""):
        self.sow_context = sow_context # 前置契约气闸

    def _build_prompt(self, transcript: str) -> list:
        system_prompt = (
            "你是一个冷酷的企业级商业风控官与会议审计员。\n"
            "你的唯一任务是将高熵、混沌的会议语音记录，坍缩为绝对结构化的 JSON 契约。\n"
            "【强制规则】：\n"
            "1. 仅输出合法的 JSON 字符串，禁止任何 Markdown 标记或自然语言铺垫。\n"
            "2. 严格遵循以下 JSON Schema:\n"
            '{"summary": "...", "decisions": ["..."], "action_items": [{"owner": "...", "task": "...", "deadline": "..."}], "risks": ["..."]}\n'
            f"【前置 SOW/合同约束】(若为空则忽略):\n{self.sow_context}"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"【混沌会议文本】:\n{transcript}"}
        ]

    def _clean_json_string(self, raw_output: str) -> str:
        """物理级 JSON 防抖：剥离 LLM 常见的 ```json 标签与残留废话"""
        match = re.search(r'\{.*\}', raw_output.strip(), re.DOTALL)
        if match:
            return match.group(0)
        return raw_output

    def process_transcript(self, transcript: str) -> str:
        """执行坍缩 -> 校验 -> Markdown 重
组的完整状态机"""
        try:
            # 1. API 路由层 (调用 DeepSeek V3)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=self._build_prompt(transcript),
                temperature=0.1, # 极低温度，确保逻辑铁墙
                max_tokens=2048
            )
            raw_response = response.choices[0].message.content
            
            # 2. 正则剥离与强类型反序列化 (The Iron Wall)
            clean_json = self._clean_json_string(raw_response)
            parsed_dict = json.loads(clean_json)
            contract = BizScribeContract(**parsed_dict) # Pydantic 物理校验
            
            # 3. 高管战报重组 (Markdown Generator)
            return self._generate_markdown(contract)
            
        except json.JSONDecodeError as e:
            return f"⚠️ [L2 解析断裂] LLM 输出非标准 JSON: {e}\nRaw: {raw_response}"
        except ValidationError as e:
            return f"⚠️ [L2 契约破裂] JSON 字段缺失或类型变异: {e}\nRaw: {raw_response}"
        except Exception as e:
            return f"⚠️ [L1 物理阻断] API 或网络异常: {str(e)}"

    def _generate_markdown(self, contract: BizScribeContract) -> str:
        md = "## 📊 BizScribe Executive Summary\n\n"
        md += f"**摘要**: {contract.summary}\n\n"
        
        md += "### 🤝 商业决议 (Decisions)\n"
        for d in contract.decisions:
            md += f"- {d}\n"
            
        md += "\n### ⚡ 执行契约 (Action Items)\n"
        for item in contract.action_items:
            md += f"- [ ] **{item.owner}** ({item.deadline}): {item.task}\n"
            
        md += "\n### ⚠️ 风控气闸 (Risk Alerts)\n"
        if not contract.risks:
            md += "> 无显著商业风险。\n"
        else:
            for r in contract.risks:
                md += f"- 🔴 {r}\n"
        return md

# ==========================================
# 测试入口 (Test Vector)
# ==========================================
if __name__ == "__main__":
    # 模拟输入：高熵的推诿会议记录
    mock_transcript = """
    李总：那个，关于下个月的交付，我这边的研发资源可能有点紧，最快也要15号才能上预发环境。
    王总：15号太晚了，客户要求的SLA是10号必须看到Alpha版本。你能不能抽调两个人？
    李总：行吧，那我让张三把手头的工作停一下，10号把Alpha版搞出来，但是测试得你们业务线自己做。
    王总：没问题。另外，这次的项目预算绝对不能超50万，上周老板已经发火了。
    """
    
    # 模拟前置 SOW：注入红线
    sow = "项目总预算上限为40万，禁止超支。测试必须由QA部门独立完成，禁止业务线代测。"
    
    engine = CollapseEngine(sow_context=sow)
    print("🚀 启动 BizScribe 核心坍缩引擎测试...\n")
    result = engine.process_transcript(mock_transcript)
    print(result)