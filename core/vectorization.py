from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field
from typing import Optional
import os
from tqdm import tqdm


class Vectorization(BaseModel):
    file_paths: list = Field(
        ...,
        alias="file",
        description="List of file paths to vectorize"
    )
    embeddings: Optional[Embeddings] = Field(
        default=None,
        description="Embeddings object"
    )
    embedding_api_name: Optional[str] = Field(
        default=None,
        description="API name for embeddings",
        alias="embedding_name"
    )
    embedding_api_key: Optional[str] = Field(
        default="EMPTY",
        description="API key for embeddings",
        alias="embedding_key"
    )
    embedding_api_base: Optional[str] = Field(
        default=None,
        description="API endpoint for embeddings",
        alias="embedding_url"
    )
    output_path: Optional[str] = Field(
        default="./database/faissdb",
        description="Path to save vectorized data",
        alias="output"
    )

    class Config:
        arbitrary_types_allowed = True
        extra = 'allow'

    def md_vectorize(self):
        # 1. 查找文件
        self.file_paths = self._file_loader()
        # 2. 分割文件
        documents, collection_list = self._md_split()
        # 3. 向量化
        for collection in collection_list:
            if self.embeddings is not None:
                for docs in tqdm(documents, desc=f"Vectoring documents for {collection}"):
                    FAISS.from_documents(
                        # collection_name=collection,
                        embedding=self.embeddings,
                        documents=docs
                    ).save_local(self.output_path)
            elif self.embedding_api_key is not None:
                for docs in tqdm(documents, desc=f"Vectoring documents for {collection}"):
                    self.embeddings = OpenAIEmbeddings(
                        model=self.embedding_api_name,
                        openai_api_key=self.embedding_api_key,
                        openai_api_base=self.embedding_api_base
                    )
                    FAISS.from_documents(
                        # collection_name=collection,
                        embedding=self.embeddings,
                        documents=docs
                    ).save_local(self.output_path)
            else:
                raise ValueError("No embeddings provided")
        print("Vectorization complete")
        return FAISS.load_local(
            self.output_path, self.embeddings, allow_dangerous_deserialization=True
        )

    def _md_split(self):
        # 1. 初始化 md 分割器
        md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ],
            return_each_line=True,
        )
        # 2. 执行分割，返回结果
        temp_doc_list = []
        temp_collection_list = []
        if len(self.file_paths) > 0:
            for file in tqdm(self.file_paths):
                # 打开文件，加载文件内容
                with open(file, "r", encoding="utf-8") as f:
                    markdown_text = f.read()
                # 分割/格式化文件内容
                temp_doc_list.append(md_splitter.split_text(markdown_text))
                for temp_doc in temp_doc_list[-1]:
                    # 以一级标题/文件路径名为 collection 名字
                    try:
                        temp_collection_list.append(temp_doc.metadata['Header 1'])
                    except KeyError:
                        temp_collection_list.append(file)
            return temp_doc_list, list(set(temp_collection_list))
        else:
            raise ValueError("No file paths provided")

    def _file_loader(self):
        temp_file_list = []
        for file in self.file_paths:
            if os.path.isfile(file):
                temp_file_list.append(file)
            elif os.path.isdir(file):
                temp_file_list.extend(get_file_dirs(file))
            else:
                print(f"Warning: Invalid file path: {file}")
        return temp_file_list


def get_file_dirs(dir_path: str) -> list:
    # args：dir_path，目标文件夹路径
    file_list = []
    for filepath, dir_names, filenames in os.walk(dir_path):
        # os.walk 函数将递归遍历指定文件夹
        for filename in filenames:
            # 通过后缀名判断文件类型是否满足要求
            if filename.endswith(".md"):
                # 如果满足要求，将其绝对路径加入到结果列表
                file_list.append(os.path.join(filepath, filename))
    return file_list


if __name__ == "__main__":
    Vectorization(
        file=["../database/raw"],
        embedding_name="embedding-3",
        embedding_url="https://open.bigmodel.cn/api/paas/v4",
        embedding_key="f4382b0322ae22eaeaa3f44001d0c94f.tLBA78CzNPpyNeuy"
    ).md_vectorize()
