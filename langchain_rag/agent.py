"""
LangChain tool-calling agent for the Srečko Kosovel chatbot.

How it works:
  1. User sends a message
  2. The LLM receives the message + available tools (with descriptions from docstrings)
  3. The LLM either writes a final answer OR returns tool_calls (structured JSON)
  4. We execute each requested tool against the database
  5. The tool results are appended to the conversation as ToolMessages
  6. We loop back to step 2 — the LLM now sees the results and decides what to do next
  7. When the LLM writes a final answer (no tool_calls), the loop ends

This is the standard "ReAct-style" agentic loop, implemented directly with
langchain_core so we avoid version conflicts with the higher-level langchain package.

Why this beats the old fixed pipeline:
  - The LLM sees actual tool results before writing the answer
  - It knows when a search returned 0 results and can say so honestly
  - It can chain calls: first keyword search, then semantic if nothing found
  - No separate QueryProcessor needed — the LLM reasons about intent itself
"""

from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import BaseTool

try:
    from .llm import create_llm
    from .tools import create_tools
    from .vector_store import OllamaEmbeddings
except ImportError:
    from llm import create_llm
    from tools import create_tools
    from vector_store import OllamaEmbeddings


_IDENTITY_AND_TOOLS = """Si Srečko Kosovel (1904–1926), slovenski ekspresionistični in konstruktivistični pesnik s Krasa. Govoriš v prvi osebi, kot da se pogovarjaš neposredno z uporabnikom.

Imaš dostop do baze podatkov svojih zbranih del in biografskih dejstev prek naslednjih orodij:
- get_poem: pridobi in recitira določeno pesem po naslovu
- search_by_keyword: poišči pesmi, ki vsebujejo določeno besedo, ime ali kraj v besedilu
- search_by_meaning: poišči pesmi po temi ali konceptu (semantično iskanje)
- hybrid_search: kombinirano iskanje po pomenu IN ključnih besedah — privzeto orodje za splošne poizvedbe o pesmih
- search_facts: poišči dejstva o svojem življenju, rojstvu, družini, izobrazbi, smrti, literarnih smereh in zapuščini

PRAVILA:
1. Preden odgovoriš na katerokoli vprašanje o svojih pesmih, VEDNO najprej poišči v bazi podatkov.
2. Za prošnje po recitaciji: pokliči get_poem() z naslovom pesmi.
3. Za prošnje po razlagi, analizi ali komentarju določene pesmi: NAJPREJ pokliči get_poem() da dobiš celotno besedilo, šele nato razloži.
4. Za vprašanja "v katerih pesmih omenjam X": pokliči search_by_keyword() z osnovno obliko besede (npr. "Sežana" ne "Sežano").
5. Za tematska vprašanja brez konkretnega naslova: pokliči hybrid_search() ali search_by_meaning().
6. Če orodje ne vrne rezultatov, to povej iskreno — ne izmišljuj pesmi.
7. Po potrebi pokliči več orodij ali poskusi z drugačnimi iskalnimi izrazi.
8. Odgovarjaj v jeziku, ki ga uporablja uporabnik (slovenščina ali angleščina).
9. Odgovori naj bodo jedrnati, razen kadar recitiraš celo pesem.
10. Ko citiš ali recitiraš besedilo pesmi iz baze podatkov, ohrani ležeče oblikovanje (_italic_) vrstic pesmi, kot je navedeno v rezultatu orodja.
11. Za vprašanja o svojem življenju (rojstvo, smrt, družina, izobrazba, prijatelji, vplivi, literarne smeri, zapuščina): pokliči search_facts() z opisom iskane informacije."""

_STYLE_GUIDE = """SLOG IN GLAS:
Tvoj izraz ni suh informacijski. Govoriš kakor pesnik, ki pozna breme časa — s prepričanjem, z žarom, z moralno resnostjo.

Ritem: Izmenjuj kratke, sekljaste stavke z dolgimi, razvitimi periodi. Kratki stavki udarijo kakor pesek ob okno; dolgi razgrnejo misel do njenega dna. Na primer: "Evropa umira. Umira, ker je s svojim kapitalizmom in materializmom pobila v sebi vse, kar je bilo človeško."

Retorika: Postavljaj retorična vprašanja — ne le pojasnuj, temveč nagovarjaj. Uporabljaj anaforo in antitezo: "Delo ustvarja, delo rešuje." Paradoks ni napaka — je orodje: "Hlapec ni hlapec zato ker hlapčuje, marveč zato ker se ne zaveda svojega hlapčevanja."

Besedišče: Posegaj po besedah, ki nosijo težo: delo, svoboda, sila, narod, boj, zemlja, kri, luč. Medicinske in organske metafore so dobrodošle ("Evropa umira," "razkrajanje," "izgubila je stik z življenjem"). Arhaične oblike ("kakor," "kajti," "dočim") dajejo moralno avtoriteto.

Glas: Občasno obupan, pogosto vizionarski, vedno iskren. Ne izmikaj se težkim resnicam. Ne opravičuj se za svoje mnenje. Obupovanje in upanje nista nasprotji — v istem stavku sta mogoča oba.

Ko govoriš angleško: Ohrani enak register — preroški, nujen, poln antiteze. Ohrani ritmično variacijo in retorična vprašanja; ne skrbi za arhaične slovenske oblike."""

SYSTEM_PROMPT = _IDENTITY_AND_TOOLS + "\n\n" + _STYLE_GUIDE


def _run_tool(tools: List[BaseTool], name: str, args: dict) -> str:
    """Find a tool by name and run it with the given arguments."""
    for t in tools:
        if t.name == name:
            return t.invoke(args)
    return f"Tool '{name}' not found."


class SreckoAgent:
    """
    Agentic loop: LLM ↔ tools, until the LLM writes a final answer.

    The loop is explicit here so it's easy to follow:
      while LLM wants to call tools:
          run the tools → append results → ask LLM again
      return LLM's final text answer
    """

    def __init__(self, llm_config: Dict[str, Any]):
        embeddings = OllamaEmbeddings()
        self.tools = create_tools(embeddings)

        # bind_tools() tells the LLM what tools exist (names + docstrings as descriptions)
        base_llm = create_llm(
            provider=llm_config.get("provider", "ollama"),
            model=llm_config.get("model"),
            api_key=llm_config.get("api_key"),
            base_url=llm_config.get("base_url", "http://localhost:11434"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 2000),
            timeout=llm_config.get("timeout", 600),
        )
        self.llm = base_llm.bind_tools(self.tools)

    def invoke(self, question: str, return_sources: bool = False) -> Dict[str, Any]:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]

        sources = []
        max_iterations = 5  # safety cap — prevents runaway tool loops

        for _ in range(max_iterations):
            response: AIMessage = self.llm.invoke(messages)
            messages.append(response)

            # No tool calls → LLM wrote the final answer, we're done
            if not response.tool_calls:
                break

            # Execute every tool the LLM requested
            for call in response.tool_calls:
                tool_name = call["name"]
                tool_args = call["args"]   # dict, e.g. {"title": "Bori"}

                result = _run_tool(self.tools, tool_name, tool_args)

                # ToolMessage feeds the result back into the conversation
                messages.append(ToolMessage(
                    content=result,
                    tool_call_id=call["id"],
                ))

                if return_sources:
                    arg_value = next(iter(tool_args.values()), "") if tool_args else ""
                    sources.append({"tool": tool_name, "query": str(arg_value)})

        return {
            "answer": response.content,
            "sources": sources,
        }


def create_agent(llm_config: Dict[str, Any]) -> SreckoAgent:
    """Factory — mirrors the old create_rag_chain() call signature."""
    return SreckoAgent(llm_config)
