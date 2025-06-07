# app/services/doc_generator.py
from typing import Dict, Any

class DocGenerator:
    def __init__(self, template_dir: str = "app/templates"):
        self.template_dir = template_dir
        print(f"DocGenerator инициализирован. Директория шаблонов: {self.template_dir}")

    def render_readme(self, template_name: str, context_data: Dict[str, Any]) -> str:
        """
        Заглушка: Рендерит README с использованием шаблона Jinja2.
        В реальной реализации будет загружать шаблон и рендерить его.
        """
        print(f"[DocGenerator ЗАГЛУШКА] Рендеринг шаблона: {template_name}")
        print(f"[DocGenerator ЗАГЛУШКА] Контекстные данные: {str(context_data)[:200]}...")

        # Простая симуляция, если LLM уже вернул Markdown
        # В вашем ui.py вы делаете final_readme = llm_output, если LLM отдает Markdown
        # Если LLM отдает структурированные данные, то здесь будет логика Jinja.
        # Для этой заглушки, если context_data - это строка, просто вернем ее.
        if isinstance(context_data, str):
            return context_data
        
        # Иначе, симулируем, что context_data - это словарь для шаблона
        output = f"# README из шаблона {template_name}\n\n"
        output += f"Заголовок из контекста: {context_data.get('title', 'Нет заголовка')}\n\n"
        output += f"Описание из контекста: {context_data.get('description', 'Нет описания')}\n\n"
        output += "*Сгенерировано DocGenerator (Заглушка)*"
        
        print("[DocGenerator ЗАГЛУШКА] Шаблон отрендерен (симуляция).")
        return output
