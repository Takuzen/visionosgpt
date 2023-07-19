import os
import openai
import pinecone
import tiktoken
import ast
import pandas as pd
from dotenv import load_dotenv


class VisionOSChatbot:
    def __init__(self):
        # Configuration
        load_dotenv() # Load default environment variables (.env)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        assert self.OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
        openai.api_key = self.OPENAI_API_KEY
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
        assert self.PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"
        self.PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
        assert (
            self.PINECONE_ENVIRONMENT
        ), "PINECONE_ENVIRONMENT environment variable is missing from .env"

        # Models
        self.EMBEDDING_MODEL = "text-embedding-ada-002"
        self.GPT_MODEL = "gpt-3.5-turbo"

        # Initialize Pinecone
        pinecone.init(api_key=self.PINECONE_API_KEY, environment=self.PINECONE_ENVIRONMENT)

        self.table_name = "visionos-docs-2023-07-10"
        self.dimension = 1536
        self.metric = "cosine"
        self.pod_type = "p1"

        # Create Pinecone index
        if self.table_name not in pinecone.list_indexes():
            print("Creating pinecone index")
            pinecone.create_index(self.table_name, dimension=self.dimension, metric=self.metric, pod_type=self.pod_type)

        # Connect to the index
        self.index = pinecone.Index(self.table_name)

        # Load vectors into the index
        self.load_vectors()

    def load_vectors(self):
        print("loading CSV file")
        embeddings_path = "visionos_docs_2023_07_10_embedding.csv"

        df = pd.read_csv(embeddings_path)

        # Convert embeddings from CSV str type back to list type
        print("converting it to list type")
        df['embedding'] = df['embedding'].apply(ast.literal_eval)

        print("writing vectors")
        vectors = [(str(row["id"]), row["embedding"]) for i, row in df.iterrows()]
        for vector in vectors:
            self.index.upsert([vector])

    def strings_ranked_by_relatedness(self, query: str, top_n: int = 100) -> object:
        query_embedding_response = openai.Embedding.create(
            model=self.EMBEDDING_MODEL,
            input=query,
        )
        query_embedding = query_embedding_response["data"][0]["embedding"]

        results = self.index.query(query_embedding, top_k=top_n, include_metadata=True)
        return results

    def num_tokens(self, text: str, model: str = None) -> int:
        if model is None:
            model = self.GPT_MODEL
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))

    def query_message(self, query: str, model: str = None, token_budget: int = 4096 - 500) -> str:
        if model is None:
            model = self.GPT_MODEL
        results = self.strings_ranked_by_relatedness(query)
        introduction = 'Use the below articles on Apple visionOS to answer the subsequent question. If the answer cannot be found in the articles, write "I could not find an answer."'
        question = f"\n\nQuestion: {query}"
        message = introduction
        embeddings_path = "visionos_docs_2023_07_10_text.csv"
        df = pd.read_csv(embeddings_path)
        for match in results["matches"]:
            match_id = int(match['id'])
            string = df[df['id']==match_id]['text'].values[0]
            next_article = f'\n\nvisionOS document section:\n"""\n{string}\n"""'
            if (
                self.num_tokens(message + next_article + question, model=model)
                > token_budget
            ):
                break
            else:
                message += next_article
        return message + question

    def ask(self, query: str, model: str = None, token_budget: int = 4096 - 500, print_message: bool = False) -> str:
        if model is None:
            model = self.GPT_MODEL
        message = self.query_message(query, model=model, token_budget=token_budget)
        if print_message:
            print(message)
        messages = [
            {"role": "system", "content": "You answer questions about Apple VisionOS."},
            {"role": "user", "content": message},
        ]
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0
        )
        response_message = response["choices"][0]["message"]["content"]
        return response_message


if __name__ == "__main__":
    bot = VisionOSChatbot()
    query = 'How to add a button to open full immersive space using swiftUI with visionOS?'
    res = bot.ask(query, print_message=False)
    print(f"Q: {query}\nA: {res}")