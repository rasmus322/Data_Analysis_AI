import httpx
import json


OLLAMA_BASE_URL = "http://localhost:11434"


async def check_ollama_available() -> tuple[bool, list[str]]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return True, models
            return False, []
    except Exception:
        return False, []


async def generate_analysis(prompt: str, model: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


def build_analysis_prompt(games_data: dict) -> str:
    return f"""Ты — AI-аналитик для продакт-менеджеров в геймдеве.
Проанализируй следующие данные из Steam и дай краткие инсайты и рекомендации.

Данные:
{json.dumps(games_data, ensure_ascii=False, indent=2)}

Предоставь:
1. Ключевые тренды (какие жанры доминируют, какие игры растут)
2. Инсайты для PM (что можно извлечь для разработки нового продукта)
3. Рекомендации (на что обратить внимание при планировании)
4. Риски и возможности

Ответ должен быть структурированным и кратким.
"""
