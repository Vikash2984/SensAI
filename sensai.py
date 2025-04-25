from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from prompts import prompt1, prompt2, prompt3, prompt4, prompt5, prompt6, prompt7
from dotenv import load_dotenv
import asyncio

load_dotenv()

llm1 = ChatGroq(model="Llama-3.1-8b-instant")
llm2 = ChatGroq(model="gemma2-9b-it")
llm3 = ChatGroq(model="llama3-8b-8192")

chain1 = prompt1 | llm1 | StrOutputParser()
chain2 = prompt2 | llm2 | StrOutputParser()
chain3 = prompt3 | llm2 | StrOutputParser()
chain4 = prompt4 | llm3 | StrOutputParser()
chain5 = prompt5 | llm1 | StrOutputParser()
chain6 = prompt6 | llm1 | StrOutputParser()
chain7 = prompt7 | llm1 | StrOutputParser()  

messages = []

async def open_application(app_command):
    exe = await asyncio.create_subprocess_shell(app_command, shell=True)
    await exe.communicate()
    result = exe.returncode
    if result != 0:
        webapp_command = chain3.invoke({"command": app_command}) or '404'
        if webapp_command != '404':
            await asyncio.create_subprocess_shell(webapp_command, shell=True)
            return webapp_command
        return 'Application not found'
    return app_command

async def search_content(command):
    exe = await asyncio.create_subprocess_shell(command, shell=True)
    await exe.communicate()
    result = exe.returncode
    return command if result == 0 else 'Please input a valid query'

async def navigate_system(command):
    if command == "Application not found":
        return "Sorry, I can't open this file or folder."
    exe = await asyncio.create_subprocess_shell(command, shell=True)
    await exe.communicate()
    result = exe.returncode
    return command if result == 0 else "Failed to open file/folder."

async def sens(query):
    messages.append(HumanMessage(content=query))

    result = chain1.invoke({"query": query}).strip()

    if result == "app":
        command = chain2.invoke({"query": query}).strip()
        if command == '404':
            response = chain4.invoke({"query": query, "command": 'None'})
        else:
            exe = await open_application(command)
            response = chain4.invoke({"query": query, "command": exe})
        messages.append(AIMessage(content=response))
        return response

    elif result == "search":
        command = chain6.invoke({"query": query}).strip()
        if command == '404':
            response = chain4.invoke({"query": query, "command": 'None'})
        else:
            exe = await search_content(command)
            response = chain4.invoke({"query": query, "command": exe})
        messages.append(AIMessage(content=response))
        return response

    elif result == "nav":
        command = chain7.invoke({"query": query}).strip()
        exe = await navigate_system(command)
        response = chain4.invoke({"query": query, "command": exe})
        messages.append(AIMessage(content=response))
        return response

    elif result == "convo":
        chat_history = "\n".join(
            f"Human: {m.content}" if isinstance(m, HumanMessage) else f"AI: {m.content}"
            for m in messages
        )
        ans = chain5.invoke({"query": query, "history": chat_history})
        messages.append(AIMessage(content=ans))
        return ans

    else:
        return "Invalid response. Please try again."
