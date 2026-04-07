# 📂 BizScribe (商录)
**Enterprise Contract Collapse Engine | 企业级商务会议“契约坍缩”引擎**

> **"Talk is cheap. Show me the Schema."** 
> 废话少说，给我看结构。

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-red.svg)](https://www.gnu.org/licenses/agpl-3.0) 
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Bimodal IT](https://img.shields.io/badge/Architecture-Bimodal_IT-black.svg)]()

BizScribe (商录) is an engineering pipeline designed to force high-entropy, evasive human meeting conversations to collapse into a **100% deterministic JSON contract** with strict deadlines and risk audits.
商录（BizScribe）并非市面上常见的“AI 录音总结玩具”，而是一个专为企业级多语言商务谈判与产研会议设计的工程化管道。它的核心使命是将高熵、推诿、发散的人类会议语音，强制坍缩为**100% 确定性、带死线的 JSON 结构化契约**。

---

## ⚡ Core Architecture | 核心架构

- **L0 Zero-RAM Slicing (无感极速切片)**
  Hijacks FFmpeg for fast, lossless audio slicing. Paired with offline ASR (e.g., SenseVoice) for absolute data privacy. 
  底层接管 FFmpeg 探针实现大体积音频极速切片，配合离线 ASR 模型完成物理级断网语音识别，杜绝企业机密音频外泄。

- **L1 Dual-Track Routing (双轨算力解耦)**
  Decouples local hardware (GPU/CPU) from cloud APIs (DeepSeek V3 / Gemini). Switch compute sources seamlessly.
  本地算力与云端 API 双轨并行。代码即基建，随时切换算力源。

- **L2 Pydantic Iron Wall (结构防抖铁墙)**
  Strips all LLM "hallucinations", forcing the output into a strict JSON schema. Schema mutations trigger a Dead Letter Queue retry.
  物理剥离 LLM 产生的自然语言废话，强制输出严格包含四大维度的 JSON 结构。格式一旦变异即触发死信重试。

- **L2 SOW Airgap (前置风控气闸)**
  Cross-references meeting content against pre-injected contracts (SOW) to audit and flag commercial risks in real-time.
  支持前置注入历史合同或 SOW 红线。实时比对会议决议是否越权、违背常识或突破预算，并输出 `risks` 预警。

---

## 🛠 Workflow Topology | 工作流拓扑

`[Audio 混沌语音] -> [FFmpeg] -> [Offline ASR] -> [LLM Schema Collapse] -> [Pydantic Iron Wall] -> [Markdown Report 高管战报]`

**Forced JSON Ontology | 引擎强制输出的四维本体结构：**
```json
{
  "summary": "Executive summary under 100 words. (100字以内的冷酷高管摘要)",
  "decisions": ["Confirmed business decision 1 (已拍板的商业决议)"],
  "action_items": [
    {"owner": "John (张三)", "task": "Deploy node (部署节点)", "deadline": "Friday (周五)"}
  ],
  "risks": [
    "🔴 Overstepped budget constraints defined in pre-SOW (决议突破了前置SOW的预算红线)"
  ]
}