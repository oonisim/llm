import langchain_google_genai
import langchain_core.prompts
import langchain.agents
import mcp
import langchain_mcp_adapters.tools
import asyncio


async def main():

    # モデルを準備
    model = langchain_google_genai.ChatGoogleGenerativeAI(
        model="gemini-2.0-flash"
    )

    # プロンプトを準備
    prompt = langchain_core.prompts.chat.ChatPromptTemplate.from_template(
        """Question: {input}
        Thought: Let's think step by step.
        Use one of registered tools to answer the question.
        Answer: {agent_scratchpad}"""
    )

    # MCP サーバ呼出の設定
    params = mcp.StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    # MCP サーバを実行
    async with mcp.client.stdio.stdio_client(params) as (read, write):
        async with mcp.ClientSession(read, write) as session:
            await session.initialize()
            tools = await langchain_mcp_adapters.tools.load_mcp_tools(session)

            # エージェントを用意
            agent = langchain.agents.create_tool_calling_agent(model, tools, prompt)
            executor = langchain.agents.AgentExecutor(agent=agent, tools=tools)

            query = "なごや個人開発者の集いとは何ですか？"

            # 推論を実行
            output = await executor.ainvoke({"input": query})
            print(output)

asyncio.run(main())
