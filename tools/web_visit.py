from typing import Optional, Type, Sequence
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import BeautifulSoupTransformer
from langchain_core.documents import Document
from langchain_core.tools import BaseTool, BaseModel, Field
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)


class WebVisitInput(BaseModel):
    url: str = Field(description="Url that you want to visit to see.")


class WebVisit(BaseTool):
    name = "Web Visit"
    description = "Useful for when you need detailed information from a specific web page by its url."
    args_schema: Type[BaseModel] = WebVisitInput
    return_direct: bool = False

    def _run(
            self, url: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Sequence[Document]:
        """Use the tool."""
        # Load HTML
        html_content = AsyncChromiumLoader([url]).load()
        # Transform
        docs_transformed = BeautifulSoupTransformer().transform_documents(html_content, tags_to_extract=["span", "p"])
        print(f"web visit result: {docs_transformed}")
        return docs_transformed

    async def _arun(
            self, url: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> Sequence[Document]:
        """Use the tool asynchronously."""
        # 开销小，直接同步调用
        return self._run(url, run_manager=run_manager.get_sync())


if __name__ == "__main__":
    urls = ['https://www.gdou.edu.cn/yjxq/info/1056/8742.htm']
    for url in urls:
        print(WebVisit()._run(url))
