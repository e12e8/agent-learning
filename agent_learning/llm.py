# llm.py
def call_llm(prompt: str)-> str:
    """
    调用语言模型的模拟函数
    
    参数:
        prompt (str): 输入的提示文本，用于发送给语言模型
    
    返回:
        str: 模拟的语言模型回复，格式为"【模拟模型回复】"加上原始提示
    """
    return f"【模拟模型回复】{prompt}"