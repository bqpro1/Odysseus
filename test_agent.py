from agents import Agent, FileSearchTool, Runner, WebSearchTool
from rich.console import Console
import asyncio

console = Console()

agent = Agent(
    name="Assistant",
    tools=[WebSearchTool()])


async def main():
    result = await Runner.run(agent, "Serch the web for info about the Deontic Logic")
    console.print(result.raw_responses)

if __name__ == "__main__":
    asyncio.run(main())

