from .context import Context
from .llm import LLM, ConversationHistory


class Dependencies:
    llm: LLM

    def __init__(self, ctx: Context) -> None:
        self.conversation_history = ConversationHistory(ctx)
        self.llm = LLM(ctx)
        ctx.add_dependencies(self)

def make_context() -> Context:
    ctx = Context()
    ctx.add_dependencies(Dependencies(ctx))
    return ctx
