#!/usr/bin/env python3
"""
Simple chat interface with the LLM
Usage: python3 chat_with_llm.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.llm_provider import LLMConfig, get_llm, LLMProvider


def chat_with_llm():
    """Interactive chat with the LLM"""
    
    # Configure LLM (reads from environment)
    config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        temperature=0.7,  # More creative responses for chat
    )
    
    print("\n" + "="*70)
    print("🤖 ESP32 LLM Assistant")
    print("="*70)
    print(f"Model: {config.model}")
    print(f"Provider: {config.provider.value}")
    print("Type 'exit' or 'quit' to end the conversation")
    print("="*70 + "\n")
    
    # Initialize LLM
    llm = get_llm(config)
    
    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            # Get response from LLM
            print("\n🤖 Assistant: ", end="", flush=True)
            response = llm.invoke(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def ask_question(question: str):
    """Ask a single question to the LLM"""
    
    config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        temperature=0.1,  # More deterministic
    )
    
    llm = get_llm(config)
    response = llm.invoke(question)
    
    print(f"\n🤖 {response}\n")
    return response


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single question mode
        question = " ".join(sys.argv[1:])
        ask_question(question)
    else:
        # Interactive chat mode
        chat_with_llm()
