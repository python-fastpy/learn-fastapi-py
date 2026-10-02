"""The small, boring tools every lesson in this folder reuses.

Not a lesson itself. Same idea as learn-fastmcp-server/learn-fastmcp-client's
shared greeting cast -- one set of real functions, reused everywhere, so
what changes between lessons is the AGENT mechanism, not the tools.
"""

HELLO = {"en": "Hello", "fr": "Bonjour", "de": "Hallo", "es": "Hola"}


def greet(name: str) -> str:
    """Greets someone by name, in English."""
    return f"Hello, {name}!"


def translate(text: str, language: str) -> str:
    """Translates text into another language (simulated)."""
    hello = HELLO.get(language, "Hello")
    for en in HELLO.values():
        text = text.replace(en, hello)
    return text


def lookup_weather(city: str) -> str:
    """Looks up the weather for a city (simulated, deterministic)."""
    fake_data = {"paris": "15C, light rain", "london": "12C, cloudy", "madrid": "22C, sunny"}
    return fake_data.get(city.lower(), "unknown city")


TOOLS = {"greet": greet, "translate": translate, "lookup_weather": lookup_weather}
