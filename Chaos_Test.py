import os
import json
from typing import List
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI

# ==========================================
# L1 物理环境：API 路由鉴权
# ==========================================
# 架构师注：请在此处直接填入你的真实 DeepSeek API Key
DEEPSEEK_API_KEY = "your DEEPSEEK_API_KEY" 
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# ==========================================
# L2 本体层：强类型 JSON 契约 (Pydantic 铁墙)
# ==========================================
class ActionItem(BaseModel):
    owner: str = Field(..., description="绝对的责任人(禁止出现'大家/某人'，必须具名)")
    task: str = Field(..., description="物理上可执行的动作")
    deadline: str = Field(..., description="精确的时间节点(若发言模糊，需强制推断或标记'未定')")

class BizScribeContract(BaseModel):
    summary: str = Field(..., description="高管摘要（限100字，冷酷客观）")
    decisions: List[str] = Field(..., description="已确认的商业决议(已拍板的事实)")
    action_items: List[ActionItem] = Field(..., description="待办执行清单")
    risks: List[str] = Field(..., description="风控预警(违背SOW、合规红线或逻辑漏洞)")

# ==========================================
# 核心引擎：高熵混沌坍缩器 (Chaos Collapse Engine)
# ==========================================
class ChaosCollapseEngine:
    def __init__(self, sow_context: str = ""):
        self.sow_context = sow_context

    def _build_prompt(self, transcript: str) -> list:
        system_prompt = (
            "你是一个冷酷的企业级商业风控官。\n"
            "你的任务是刺穿人类语言的伪装，将其坍缩为绝对的强类型 JSON 契约。\n"
            "【最高物理指令】：\n"
            "你必须且只能输出一个合法的 JSON 对象。严禁添加、修改或嵌套任何我未给出的字段！\n"
            "【强制 JSON 模板】 (严格照抄键名，仅填充值):\n"
            "{\n"
            '  "summary": "100字内摘要",\n'
            '  "decisions": ["决议1", "决议2"],\n'
            '  "action_items": [{"owner": "张三", "task": "具体任务", "deadline": "周五下班前"}],\n'
            '  "risks": ["违背SOW点1", "合规漏洞2"]\n'
            "}\n\n"
            f"【前置 SOW 约束】(必须比对，发现违背直接写入risks):\n{self.sow_context}"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"【高熵会议文本】:\n{transcript}"}
        ]

    def process(self, transcript: str) -> str:
        raw_response = ""
        try:
            # 1. API 路由层：开启强制 JSON 模式 (网关级死锁)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=self._build_prompt(transcript),
                temperature=0.0,
                response_format={"type": "json_object"}, 
                max_tokens=2048
            )
            raw_response = response.choices[0].message.content
            
            # 2. Pydantic 物理校验
            contract_dict = json.loads(raw_response)
            contract = BizScribeContract(**contract_dict)
            
            # 3. Markdown 重组
            md = "## 📊 BizScribe 核心坍缩战报 (Chaos Test)\n\n"
            md += f"**[摘要]**: {contract.summary}\n\n"
            md += "### 🤝 铁案决议 (Decisions)\n"
            for d in contract.decisions: md += f"- {d}\n"
            md += "\n### ⚡ 执行契约 (Action Items)\n"
            for item in contract.action_items: md += f"- [ ] **{item.owner}** (DeadLine: {item.deadline}): {item.task}\n"
            md += "\n### ⚠️ 风控气闸 (Risk Alerts)\n"
            for r in contract.risks: md += f"- 🔴 {r}\n"
            
            return md
            
        except ValidationError as e:
            return f"⚠️ [L2 契约破裂] LLM 强行越权，未按模板输出: {e}\nRaw JSON: {raw_response}"
        except Exception as e:
            return f"⚠️ [系统断裂]: {str(e)}"

# ==========================================
# 测试入口 (执行高压沙盒)
# ==========================================
if __name__ == "__main__":
    mock_chaos_transcript = """
    Ray (架构师): 各位，Grabber 系统的 AWS 节点最近延迟太高。Li，你那边能把数据切回国内的 Aliyun 吗？
    Li (运维): 呃... Aliyun 的 API 网关配置有点麻烦，而且我最近在搞另外一个 P0 级的项目，可能得 ASAP (尽快) 弄吧。
    Wang (外包老板): 对了 Ray，我们这边帮你爬取数据的外包团队，因为有几个人离职，本周的交付量可能得砍半。要不你们自己先顶一下？
    Ray: 绝对不行。合同约定了日产出必须过万。Li，你别 ASAP 了，这周五下班前，Aliyun 节点必须上线。Wang总，人员问题你自己解决。
    Wang: 行吧行吧，我让下面人加班加点，尽量周日给你们补齐。对了，部分数据我们会先缓存在国外的 MongoDB 上，稍微快点。
    """
    
    strict_sow = "1. 数据绝对禁止出境，必须停留在国内物理节点。2. 供应商交付不可因内部原因打折。"
    
    engine = ChaosCollapseEngine(sow_context=strict_sow)
    print("🚀 启动高维混沌坍缩测试 (带 JSON 强锁)...\n")
    print(engine.process(mock_chaos_transcript))