"""
ESP-IDF AI Agent with MCP integration.

This agent uses the MCP Server to interact with the ESP-IDF toolchain
in a decoupled and scalable way.
"""

import os
import sys
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI

# Add MCP server to path
sys.path.insert(0, '/mcp-server/src')

from mcp_idf.client import MCPClient


def create_agent():

import os
import sys
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

# Add MCP server to path
sys.path.insert(0, '/mcp-server/src')

from mcp_idf.client import MCPClient


def create_agent():
    """Create agent with MCP tools."""
    
    # Initialize MCP client
    mcp_client = MCPClient()
    
    # Get tools from MCP server
    tools = mcp_client.get_langchain_tools()
    
    # Create LLM model
    llm = ChatOpenAI(


def main():
    """Main entry point for the agent."""
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is not configured")
        print("Please configure your API key in the .env file")
        return
    
    print("=" * 80)
    print("ESP-IDF AI Agent with MCP")
    print("=" * 80)
    print()
    
    # Create agent
    agent = create_agent()
    
    # Interactive mode or single command
    if len(sys.argv) > 1:
        # Execute command from arguments
        query = " ".join(sys.argv[1:])
        print(f"Query: {query}\n")
        result = agent.run(query)
        print(f"\nResult:\n{result}")
    else:
        # Interactive mode
        print("Interactive mode - Type 'exit' or 'quit' to exit\n")
        
        while True:
            try:
                query = input("\n🤖 Query: ").strip()
                
                if query.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                print()
                result = agent.run(query)
                print(f"\n✅ Result:\n{result}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
