from typing import Optional, Type
from langchain_core.tools import BaseTool, BaseModel, Field
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from zhipuai import ZhipuAI
from dotenv import load_dotenv
import os

load_dotenv()


class LocalSearchInput(BaseModel):
    query: str = Field(description="Query to search for")


class LocalSearch(BaseTool):
    name = "Local Information Search"
    description = "Useful for when you need to search for information about campus in local documents."
    args_schema: Type[BaseModel] = LocalSearchInput
    return_direct: bool = False

    def _run(
            self,
            query: str,
            run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        knowledge_id = os.getenv("KNOWLEDGE_ID")
        api_key = os.getenv("ZHIPU_API_KEY")
        tools = [
            {
                "type": "retrieval",
                "retrieval": {
                    "knowledge_id": knowledge_id
                }
            }
        ]
        client = ZhipuAI(api_key=api_key)  # 填写您自己的APIKey
        response = client.chat.completions.create(
            model="glm-4",
            tools=tools,
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        return response

    async def _arun(
            self,
            query: str,
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        # 开销小，直接同步调用
        return self._run(query, run_manager=run_manager.get_sync())


if __name__ == "__main__":
    tool = LocalSearch()
    print(tool._run("校园公交怎么样？"))
