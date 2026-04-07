#!/usr/bin/env python3
"""
Interactive CLI chat with Srečko Kosovel.

Usage:
    python chat_srecko.py

Commands:
    - Type your question and press Enter
    - 'exit' / 'quit' / 'q' to end the session
    - 'help' for usage tips
    - 'sources' to toggle tool-call display
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

root_path = str(Path(__file__).parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from langchain_rag.agent import create_agent


class Colors:
    BLUE   = '\033[94m'
    CYAN   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    BOLD   = '\033[1m'
    END    = '\033[0m'


TOOL_LABELS = {
    "get_poem":           "recited poem",
    "search_by_keyword":  "keyword search",
    "search_by_meaning":  "semantic search",
}


def print_header():
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.CYAN}Srečko Kosovel AI Chat{Colors.END}")
    print("=" * 70)
    print(f"\n{Colors.YELLOW}Welcome! I am Srečko Kosovel (1904-1926), Slovenian poet.{Colors.END}")
    print("\nAsk me about my poetry, the Karst region, my themes, or request")
    print("that I recite specific poems. I will answer based on my actual works.")
    print(f"\n{Colors.CYAN}Commands:{Colors.END}  exit · help · sources (toggle tool display)")
    print("=" * 70 + "\n")


def print_help():
    print(f"\n{Colors.CYAN}How to use:{Colors.END}")
    print("  'Recitiraj pesem Bori'          → recites the poem")
    print("  'V katerih pesmih omenjam Kras?' → keyword search in content")
    print("  'Pesmi o samoti in naravi'       → thematic search")
    print("  'Kdo si?'                        → general question")
    print(f"\n{Colors.CYAN}Tips:{Colors.END}")
    print("  - Works in Slovenian and English")
    print("  - Type 'sources' to see which database queries were run")
    print()


def print_sources(sources: list):
    """Show which tools were called — more informative than a relevance score."""
    if not sources:
        return
    print(f"\n{Colors.CYAN}🔍 Database queries:{Colors.END}")
    for s in sources:
        label = TOOL_LABELS.get(s["tool"], s["tool"])
        print(f"  {Colors.YELLOW}{label}{Colors.END}({s['query']!r})")


def main():
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "ollama")
    llm_config = {
        "provider": provider,
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model":    os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b"),
        "timeout":  int(os.getenv("OLLAMA_CHAT_TIMEOUT", "600")),
    }

    if provider == "openrouter":
        llm_config["model"]      = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")
        llm_config["api_key"]    = os.getenv("OPENROUTER_API_KEY")
        llm_config["max_tokens"] = int(os.getenv("OPENROUTER_MAX_TOKENS", "2000"))
    elif provider == "anthropic":
        llm_config["model"]   = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        llm_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
    elif provider == "github-copilot":
        llm_config["model"]   = os.getenv("GITHUB_COPILOT_MODEL", "Claude Sonnet 4.5")
        llm_config["api_key"] = os.getenv("GITHUB_COPILOT_TOKEN") or os.getenv("GITHUB_TOKEN")
    elif provider == "github":
        llm_config["model"]   = os.getenv("GITHUB_MODEL", "gpt-4o")
        llm_config["api_key"] = os.getenv("GITHUB_TOKEN")

    print_header()
    print(f"{Colors.CYAN}Initializing...{Colors.END}", end=" ", flush=True)
    try:
        agent = create_agent(llm_config)
        print(f"{Colors.GREEN}✓ Ready!{Colors.END}")
        print(f"{Colors.CYAN}Using {provider}: {llm_config['model']}{Colors.END}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ {e}{Colors.END}")
        sys.exit(1)

    show_sources = True

    try:
        while True:
            try:
                user_input = input(f"{Colors.BOLD}{Colors.BLUE}You:{Colors.END} ").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print(f"\n{Colors.YELLOW}Farewell! May my poems stay with you.{Colors.END}\n")
                break
            if user_input.lower() == "help":
                print_help()
                continue
            if user_input.lower() == "sources":
                show_sources = not show_sources
                print(f"\n{Colors.CYAN}Tool display {'enabled' if show_sources else 'disabled'}.{Colors.END}\n")
                continue

            print(f"{Colors.CYAN}Thinking...{Colors.END}", end=" ", flush=True)
            try:
                result = agent.invoke(user_input, return_sources=show_sources)
                print(f"\r{' ' * 20}\r", end="")

                print(f"\n{Colors.BOLD}{Colors.GREEN}💬 Srečko Kosovel:{Colors.END}\n")
                print(result["answer"])
                print()

                if show_sources:
                    print_sources(result.get("sources", []))
                    print()

            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}Interrupted. Type 'exit' to quit.{Colors.END}\n")
            except Exception as e:
                print(f"\r{Colors.RED}✗ Error: {e}{Colors.END}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Farewell! May my poems stay with you.{Colors.END}\n")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
