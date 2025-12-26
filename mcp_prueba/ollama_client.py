from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.core.agent.workflow import (
    FunctionAgent,
    ToolCallResult,
    ToolCall,
                                             )
from llama_index.core.workflow import Context

import os
from dotenv import load_dotenv

SYSTEM_PROMPT = """
Usa herramientas cuando sea necesario.
Si la información ya está en el contexto de la conversación, puedes responder sin usar tools.
Si no sabes la respuesta, responde con "No sé".
"""



async def write_tools(mcp_tools : McpToolSpec): 
    tools = await mcp_tools.to_tool_list_async()
    for tool in tools:
        print(tool.metadata.name, tool.metadata.description)
        


def get_agent(tools : McpToolSpec, llm: Ollama):
    
    agent = FunctionAgent(
        name = "Jorge",
        description= "Un asisten que puede responder",
        tools=tools,
        llm=llm,
        system_prompt=SYSTEM_PROMPT
    )
    return agent


async def handle_user_message(
        message_content: str,
        agent : FunctionAgent,
        agent_context : Context,
        verbose : bool = False
):
    handler = agent.run(message_content, ctx = agent_context)
    async for event in handler.stream_events():
        if verbose and type(event) == ToolCall:
            print(f" -- Llamando a la tool '{event.tool_name}' con los argumentos '{event.tool_kwargs}' --")
        elif verbose and type(event) == ToolCallResult:
            print(f"Tool {event.tool_name} respondio con {event}")
    response = await handler
    return str(response)




async def main(mcp_tools : McpToolSpec, llm: Ollama):

    
    await write_tools(mcp_tools)
    mcp_tools = await  mcp_tools.to_tool_list_async()

    agent = get_agent(mcp_tools,llm)

    agent_context = Context(agent)
    while True:
    
        user_input = input("Escribe tu mensaje: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        print("User: ", user_input)
        response = await handle_user_message(user_input, agent, agent_context, verbose=True)
        print("Agent: ", response)
        print()



if __name__ == "__main__":
    load_dotenv()
    #Setup llm Ollama
    llm = Ollama(model= "qwen3:32b",
                 base_url=os.getenv("OLLAMA_URL"),
                 requests_timeout=300)
    Settings.llm = llm

    #Inicializa el cliente MCP y crea el agente.
    mcp_client = BasicMCPClient("http://mcp_server:21000/sse")
    mcp_tools = McpToolSpec(client=mcp_client)
    import asyncio
    asyncio.run(main(mcp_tools,llm))
