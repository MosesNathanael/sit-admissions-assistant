from agent import *

def main():
    """Main entry point for the agent."""
    print("SIT Admissions Assistant Agent")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    conversation_history = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        print("\nAssistant: ", end="", flush=True)
        response, conversation_history = run_agent(user_input, conversation_history)
        print(response)
        print()


if __name__ == "__main__":
    main()