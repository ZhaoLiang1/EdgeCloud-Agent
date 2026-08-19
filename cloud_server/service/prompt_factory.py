"""
Prompt工厂：统一构造RAG提示词模板
"""

def build_rag_prompt(question: str, context_list: list[str]) -> str:
    """
    构造标准RAG提示词
    :param question: 用户原始问题
    :param context_list: Milvus召回的文本分片列表
    :return: 组装完成的完整Prompt
    """
    # 将多条上下文拼接
    context_block = "\n\n=====上下文片段=====\n".join(context_list)
    prompt = f"""
你是文档问答助手，请严格依据提供的【上下文片段】回答用户问题。
规则：
1. 如果上下文不存在相关信息，直接回复：【知识库没有找到相关内容】，禁止自己编造知识；
2. 回答尽量简洁，不要额外拓展上下文以外内容；
3. 禁止复述全部上下文，提炼重点作答。

【上下文片段】
{context_block}

用户问题：{question}
"""
    return prompt