from langchain_openai import ChatOpenAI
from langchain_core.outputs import ChatGenerationChunk

class ChatDeepSeekCompatible(ChatOpenAI):
    """
    Custom ChatOpenAI subclass to handle DeepSeek/Z.ai style reasoning_content.
    LangChain's default ChatOpenAI implementation ignores unrecognized fields in the delta.
    """
    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        # DEBUG: Print raw chunk
        # print(f"[DEBUG] Raw LC Chunk: {chunk}", flush=True)

        # Let parent do the heavy lifting
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )

        if generation_chunk is None:
            return None
        
        # Manually extract reasoning_content from the raw delta
        try:
            choice = chunk["choices"][0]
            delta = choice.get("delta", {})
            reasoning = delta.get("reasoning_content")
            if reasoning:
                generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning
        except (KeyError, IndexError, AttributeError):
            pass
            
        return generation_chunk
