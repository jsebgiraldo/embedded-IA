import os
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
from tools.compile import run_build
from tools.edit_file import read_file, write_file
from tools.diagnose import idf_doctor

def tool_compile(_):
    """Tool to compile ESP-IDF project"""
    return run_build()

def tool_read_main(_):
    """Tool to read main.c file"""
    return read_file("main/main.c")

def tool_write_main(instruction: str):
    """Tool to write to main.c
    
    Note: In production, the LLM must deliver the complete file
    with changes between ```c ... ```
    """
    return write_file("main/main.c", instruction)

def tool_doctor(_):
    """Tool to run environment diagnostics"""
    return idf_doctor()

def make_agent():
    """Create and configure agent with available tools"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    tools = [
        Tool(
            name="compile",
            func=tool_compile,
            description="Compile the project with idf.py"
        ),
        Tool(
            name="read_main",
            func=tool_read_main,
            description="Read main/main.c"
        ),
        Tool(
            name="write_main",
            func=tool_write_main,
            description="Overwrite main.c with given content"
        ),
        Tool(
            name="idf_doctor",
            func=tool_doctor,
            description="Run idf.py doctor to diagnose environment"
        )
    ]
    
    return initialize_agent(
        tools,
        llm,
        agent_type="zero-shot-react-description",
        verbose=True
    )

if __name__ == "__main__":
    agent = make_agent()
    print(agent.run(
        "Compile the project and tell me exactly what errors appear. "
        "Propose a correction."
    ))
