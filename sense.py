import os
import asyncio
from langchain.memory import ConversationSummaryMemory
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from prompts import prompt1, prompt2, prompt3, prompt4, prompt5, prompt6, prompt7
from dotenv import load_dotenv

load_dotenv()

llm1 = ChatGroq(model="Llama-3.1-8b-instant")
llm2 = ChatGroq(model="gemma2-9b-it")
llm3 = ChatGroq(model="llama3-8b-8192")

chain1 = prompt1 | llm1 | StrOutputParser()
chain2 = prompt2 | llm2 | StrOutputParser()
chain3 = prompt3 | llm2 | StrOutputParser()
chain4 = prompt4 | llm3 | StrOutputParser()
chain5 = prompt5 | llm1 | StrOutputParser()
chain6 = prompt6 | llm1 | StrOutputParser()  # search
chain7 = prompt7 | llm1 | StrOutputParser()  # nav

memory = ConversationSummaryMemory(llm=llm3)

# Asynchronous function to open an application
async def open_application(app_command):
    try:
        process = await asyncio.create_subprocess_shell(app_command)
        await process.communicate()

        if process.returncode != 0:
            webapp_command = (await chain3.ainvoke({"command": app_command})).strip()
            if webapp_command != '404':
                process = await asyncio.create_subprocess_shell(webapp_command)
                await process.communicate()
                return webapp_command
            return 'Application not found'
        return app_command
    except Exception as e:
        return f"Error opening application: {str(e)}"

# Asynchronous function to search content
async def search_content(command):
    try:
        process = await asyncio.create_subprocess_shell(command)
        await process.communicate()

        if process.returncode != 0:
            return 'Please input a valid query'
        return command
    except Exception as e:
        return f"Error searching content: {str(e)}"

# Asynchronous function to navigate files and folders
async def navigate_system(command):
    if command == "Application not found":
        return "Sorry, I can't open this file or folder."
    try:
        process = await asyncio.create_subprocess_shell(command)
        await process.communicate()

        if process.returncode != 0:
            return "Failed to open file/folder."
        return command
    except Exception as e:
        return f"Error navigating system: {str(e)}"

# Asynchronous main function
async def main():
    while True:
        query = input("\nEnter a prompt: ")
        chat_history = memory.load_memory_variables({}).get('history', '')

        result = (await chain1.ainvoke({"query": query})).strip()
        print(result)

        if result == "app":
            command = (await chain2.ainvoke({"query": query})).strip()
            if command == '404':
                response = await chain4.ainvoke({"query": query, "command": 'None'})
            else:
                print(command)
                exe = await open_application(command)
                response = await chain4.ainvoke({"query": query, "command": exe})
            print("\nResponse:", response)
            memory.save_context({"input": query}, {"outputs": response})

        elif result == "search":
            command = (await chain6.ainvoke({"query": query})).strip()
            if command == '404':
                response = await chain4.ainvoke({"query": query, "command": 'None'})
            else:
                print(command)
                exe = await search_content(command)
                response = await chain4.ainvoke({"query": query, "command": exe})
            print("\nResponse:", response)
            memory.save_context({"input": query}, {"outputs": response})

        elif result == "nav":
            command = (await chain7.ainvoke({"query": query})).strip()
            print(command)
            response = await navigate_system(command)
            print("\nResponse:", response)

        elif result == "convo":
            ans = await chain5.ainvoke({"query": query, "history": chat_history})
            print("\nResponse:", ans)
            memory.save_context({"input": query}, {"outputs": ans})

        else:
            print("Invalid response. Please try again.")

# Run the asynchronous main function
asyncio.run(main())
