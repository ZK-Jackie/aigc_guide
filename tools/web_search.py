from typing import Optional, Type
from duckduckgo_search import DDGS
from langchain_core.tools import BaseTool, BaseModel, Field
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

hot_words = {}


class WebSearchInput(BaseModel):
    keyword: str = Field(description="One word to search for")


class WebSearch(BaseTool):
    name = "Web Information Search"
    description = "Useful for when you need to search for information about campus in GDOU's official website."
    args_schema: Type[BaseModel] = WebSearchInput
    return_direct: bool = False
    query_header: str = "site:gdou.edu.cn"

    def _run(
            self, keyword: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> list:
        """Use the tool."""
        if not keyword.startswith(self.query_header):
            keyword = self.query_header + ' ' + keyword
        with DDGS() as duck:
            web_query = [r for r in duck.text(keyword, region='cn-zh', max_results=4)]
            print(f"web query result: {web_query}")
            return web_query

    async def _arun(
            self,
            keyword: str,
            run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> list:
        """Use the tool asynchronously."""
        # 开销小，直接同步调用
        return self._run(keyword, run_manager=run_manager.get_sync())
