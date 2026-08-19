"""
LLM通用调用客户端，兼容OpenAI格式接口
后续可以无缝切换本地Qwen、llama.cpp兼容服务
"""
import requests
from typing import List, Dict
from config.settings import settings


class LLMClient:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.model_name = settings.LLM_MODEL_NAME

    def chat(self, prompt: str, history: List[Dict] = None, temperature: float = 0.1):
        """
        同步对话调用
        :param prompt: 用户当前提问
        :param history: 历史对话列表 [{"role":"user","content":"xxx"},{"role":"assistant","content":"xxx"}]
        :param temperature: 温度，越低答案越稳定、减少幻觉，RAG场景推荐0.0~0.3
        :return: 大模型文本回答
        """
        if history is None:
            history = []
        messages = history.copy()
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature
        }
        resp = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# 全局单例客户端
llm_client = LLMClient()