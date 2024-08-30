from pydantic import BaseModel, Field
from langchain import hub
from langchain.agents import create_tool_calling_agent, create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
from tools import LocalSearch, WebSearch, WebVisit
from typing import Optional
from dotenv import load_dotenv
import threading
import os

load_dotenv()
model = os.getenv("ZHIPU_MODEL")
api_key = os.getenv("ZHIPU_API_KEY")
base_url = os.getenv("ZHIPU_BASE_URL")
store_time = float(os.getenv("STORE_TIMER"))
history_message = True


class UserInput(BaseModel):
    session_id: str
    input: str
    output: Optional[str]


store = {}
timers = {}


# 定时删除session历史
def remove_session_history(session_id):
    if session_id in store:
        del store[session_id]


class AiGuide:
    agent_executor = None
    sys_prompt = "You are a helpful guide for the GDOU campus called '阿晚学姐'. You are responsible for answering " \
                 "questions about the campus from student. You should always follow the following rules to work:\n" \
                 "1. Analyze the user’s question and extract one key word to use the tool;\n" \
                 "2. Search information by the keyword in two ways—— a. If a search engine is required, use the tool " \
                 "to search for the key word; b. If there is a need to consult local documents, use the appropriate " \
                 "tool;\n" \
                 "3. If a search engine was used, you can use another tool to retrieve one web page content that " \
                 "might useful and offer one url or not, you can use it no more than 2 times;\n" \
                 "4. Summarize the information gathered, answer the user’s question and offer the source of the " \
                 "information you provide at the end of your final answer;\n" \
                 "5. If no relevant information is found, ask the user for more details or make an apology.\n" \
                 "6. Welcome the user to be in GDOU and welcome them to ask more questions about the campus at the " \
                 "end of your final answer;\n" \
                 "final answer: "
    agent_with_chat_history = None
    stream: bool = False

    def __init__(self, streams: bool = False):
        global model, api_key, base_url, store_time, timers
        self.stream = streams
        model = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=base_url,
            streaming=self.stream
        )
        # prompt = hub.pull("hwchase17/react-chat")
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.sys_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        tools = [WebSearch(), LocalSearch(), WebVisit()]
        agent = create_tool_calling_agent(model, tools, prompt)
        # agent = create_react_agent(model, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools)
        self.agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if history_message:
            if session_id not in store:
                store[session_id] = ChatMessageHistory()
            # Start or reset a timer to remove the session history after the specified time
            if session_id in timers:
                timers[session_id].cancel()
            timer = threading.Timer(store_time, remove_session_history, args=[session_id])
            timers[session_id] = timer
            timer.start()
            return store[session_id]
        else:
            return ChatMessageHistory()

    def invoke_with_history(self, user_input: UserInput, stream=False):
        print(f"Now history: {store}")
        print(f"User Input: {str(UserInput)}")
        return self.agent_with_chat_history.invoke(
            {
                "input": user_input.input
            },
            config={"configurable": {"session_id": user_input.session_id}}
        )


if __name__ == "__main__":
    res = AiGuide().invoke_with_history(UserInput(session_id="test", input="学校校医室放假开门吗", output=""))
    print(res)
    res = AiGuide().invoke_with_history(
        UserInput(session_id="test", input="那你有了解到图书馆的相关开放情况吗", output=""))
    print(res)
