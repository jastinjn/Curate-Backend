import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import TokenTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_community.vectorstores import Neo4jVector
from langchain.output_parsers.openai_tools import JsonOutputKeyToolsParser
from flask import current_app

os.environ["OPENAI_API_KEY"] = "sk-proj-7ZAIGQr5EFpi51zNM2JtT3BlbkFJ3gVlKlQsRLwAGoFNsUjS"
os.environ["NEO4J_URI"] = "neo4j+s://4d155963.databases.neo4j.io"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "MBK5P8SQMeotDeLiNjxqyxpLAw5QC-evAY7iOhEeRv0"

template = """You are a physician assistant responsible for communicating patient medical information to the doctor.
Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Knowledge Graph: {context1}
Documents: {context2}

Question: {question}

Helpful Answer:"""
hybrid_prompt = PromptTemplate.from_template(template)

def save_text_to_pdf(text, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Split the text into paragraphs
    paragraphs = text.split('\n')

    for para in paragraphs:
        # Create a paragraph object
        p = Paragraph(para, styles["Normal"])
        # Add the paragraph to the story
        story.append(p)

    # Build the PDF document
    doc.build(story)

def split_pdf_sections(pdf_file, save_path, splitting_character):
    # Open the PDF file
    pdf_document = fitz.open(pdf_file)
    combined_text = ''

    # Iterate through each page and combine text
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        combined_text += page.get_text()

    # Split combined text into sections based on splitting character
    sections = combined_text.split(splitting_character)

    # Print sections
    for i, section in enumerate(sections):
        # print(f"Section {i + 1}:\n{section.strip()}\n")
        section_text = section.strip()
        output_file = save_path + "/" + section_text.split('\n', 1)[0] + ".pdf"
        save_text_to_pdf(section_text, output_file)

    # Close the PDF document
    pdf_document.close()

def initialize_databases(path: str):
    
    docs = []
    for file in os.listdir(path):
        loader = PyMuPDFLoader(path + "/" + file)
        docs.extend(loader.load())

    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100, add_start_index=True)
    text_splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
    splits = text_splitter.split_documents(docs)

    llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-0125") # gpt-4-0125-preview occasionally has issues
    llm_transformer = LLMGraphTransformer(llm=llm)

    graph_documents = llm_transformer.convert_to_graph_documents(splits)
    graph = Neo4jGraph()
    graph.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True
    )

    graph.query(
        "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")

    vectorNeo4j = Neo4jVector.from_existing_graph(
        OpenAIEmbeddings(),
        search_type="hybrid",
        node_label="Document",
        text_node_properties=["text"],
        embedding_node_property="embedding"
    )
    
    return graph, vectorNeo4j

def get_graph_chain():
    llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-0125") 
    # Extract entities from text
    class Entities(BaseModel):
        """Identifying information about entities."""

        names: List[str] = Field(
            ...,
            description="All the person, health condition, medical procedure or medication entities that appear in the text",
        )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are extracting person, health condition, medical procedure and medication entities from the text.",
            ),
            (
                "human",
                "Use the given format to extract information from the following "
                "input: {question}",
            ),
        ]
    )

    graph_chain = prompt | llm.with_structured_output(Entities)

    return graph_chain

def generate_full_text_query(input: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2 changed characters) to each word, then combines
    them using the AND operator. Useful for mapping entities from user questions
    to database values, and allows for some misspelings.
    """
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()

# Fulltext index query
def structured_retriever(question: str) -> str:
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    result = ""
    graph = current_app.graph
    graph_chain = get_graph_chain()
    entities = graph_chain.invoke({"question": question})
    for entity in entities.names:
        response = graph.query(
            """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
            YIELD node,score
            CALL {
              MATCH (node)-[r:!MENTIONS]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
              UNION
              MATCH (node)<-[r:!MENTIONS]-(neighbor)
              RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            }
            RETURN output LIMIT 50
            """,
            {"query": generate_full_text_query(entity)},
        )
        result += "\n".join([el['output'] for el in response])
    return result

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def format_docs_num(docs):
    return "\n\n".join("Source " + str(i) + ":\n" + doc.page_content for i, doc in enumerate(docs))

def get_particulars():
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

    class particulars(BaseModel):
        """Answer the user question based only on the given sources and knowledge graph."""

        name: str = Field(
            ...,
            description="The name of the patient queried by the user.",
        )
        age: str = Field(
            ...,
            description="The age of the patient queried by the user.",
        )
        gender: str = Field(
            ...,
            description="The gender of the patient queried by the user.",
        )
        dob: str = Field(
            ...,
            description="The date of birth of the patient queried by the user.",
        )

    unstructured_retriever = current_app.vector.as_retriever()

    chain = (
    {"context1": structured_retriever, "context2": unstructured_retriever | format_docs, "question": RunnablePassthrough()}
    | hybrid_prompt
    | llm.bind_tools([particulars],tool_choice="particulars")
    | JsonOutputKeyToolsParser(key_name="particulars", first_tool_only=True)
    )

    return chain.invoke("What is the name, age, gender and date of birth of the patient?")

def get_overview(name: str, llm = ChatOpenAI(model="gpt-3.5-turbo-0125")):

    unstructured_retriever = current_app.vector.as_retriever()

    chain = (
    {"context1": structured_retriever, "context2": unstructured_retriever | format_docs, "question": RunnablePassthrough()}
    | hybrid_prompt
    | llm
    | StrOutputParser()
    )

    return chain.invoke(f"Summarize the most important medical information of {name}. Keep the response to one paragraph.")

def get_medications(name: str, llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)):

    class Medication(BaseModel):
        name: str = Field(
            ...,
            description="The name of the medication taken by the patient.",
        )
        dosage: str = Field(
            ...,
            description="The dosage of the medication taken by the patient.",
        )
        active: bool = Field(
            ...,
            description="True if the patient is still taking the medication.",
        )
        source_id: int = Field(
        ...,
        description="The integer ID of a SPECIFIC source which best justifies the answer.",
        )
        quote: str = Field(
            ...,
            description="The VERBATIM quote from the specified source that best justifies the answer.",
        )

    class medication_answer(BaseModel):
        """Answer the user question based only on the given sources and knowledge graph, and cite the sources used."""

        medications: List[Medication] = Field(
            ..., description="List of medications taken by the patient with citations from the given sources."
        )

    unstructured_retriever = current_app.vector.as_retriever()
        
    output_parser = JsonOutputKeyToolsParser(key_name="medication_answer", first_tool_only=True)

    chain = (
        RunnablePassthrough.assign(context1=(lambda x: x["context1"]), context2=(lambda x: format_docs_num(x["context2"])))
        # {"context1": structured_retriever, "context2": unstructured_retriever | format_docs, "question": RunnablePassthrough()}
        | hybrid_prompt
        | llm.bind_tools([medication_answer],tool_choice="medication_answer")
        | output_parser
    )

    chain_with_citations = RunnableParallel(
        {"context1": structured_retriever, "context2": unstructured_retriever, "question": RunnablePassthrough()}
    ).assign(answer=chain).pick(["context2","answer"])

    response = chain_with_citations.invoke(f"List all medications {name} has taken or is currently taking. There should be no repeated answers.")

    source_indices = [med["source_id"] for med in response["answer"]["medications"]]

    for idx, source_index in enumerate(source_indices):
        path = response["context2"][source_index].metadata['file_path']
        response["answer"]["medications"][idx]["source_path"] = path

    return response["answer"]["medications"]

def get_problems(name: str, llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)):

    class Problem(BaseModel):
        name: str = Field(
            ...,
            description="The name of the medical problem suffered by the patient.",
        )
        active: bool = Field(
            ...,
            description="True if the patient is still suffering from the medical problem.",
        )
        source_id: int = Field(
        ...,
        description="The integer ID of a SPECIFIC source which best justifies the answer.",
        )
        quote: str = Field(
            ...,
            description="The VERBATIM quote from the specified source that best justifies the answer.",
        )

    class problem_answer(BaseModel):
        """Answer the user question based only on the given sources and knowledge graph, and cite the sources used."""

        problems: List[Problem] = Field(
            ..., description="List of medical problems suffered by the patient with citations from the given sources."
        )

    unstructured_retriever = current_app.vector.as_retriever()
    output_parser = JsonOutputKeyToolsParser(key_name="problem_answer", first_tool_only=True)

    chain = (
        RunnablePassthrough.assign(context1=(lambda x: x["context1"])).assign(context2=(lambda x: format_docs_num(x["context2"])))
        | hybrid_prompt
        | llm.bind_tools([problem_answer],tool_choice="problem_answer")
        | output_parser
    )

    chain_with_context = RunnableParallel(
        {"context1": structured_retriever, "context2": unstructured_retriever, "question": RunnablePassthrough()}
    ).assign(answer=chain).pick(["answer", "context2"])

    response = chain_with_context.invoke(f"List all the major medical problems {name} currently has or has had. There should be no repeated answers.")

    source_indices = [problem["source_id"] for problem in response["answer"]["problems"]]

    for idx, source_index in enumerate(source_indices):
        path = response["context2"][source_index].metadata['file_path']
        response["answer"]["problems"][idx]["source_path"] = path

    return response["answer"]["problems"]

def query_database(question: str, llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)):

    class Citation(BaseModel):
        source_id: int = Field(
            ...,
            description="The integer ID of a SPECIFIC source which justifies the answer.",
        )
        quote: str = Field(
            ...,
            description="The VERBATIM quote from the specified source that justifies the answer.",
        )

    class quoted_answer(BaseModel):
        """Answer the user question based only on the given sources and knowledge graph, and cite the sources used."""

        answer: str = Field(
            ...,
            description="The answer to the user question.",
        )
        citations: List[Citation] = Field(
            ..., description="Citations from the given sources that justify the answer."
        )

    unstructured_retriever = current_app.vector.as_retriever()
    output_parser = JsonOutputKeyToolsParser(key_name="quoted_answer", first_tool_only=True)

    chain = (
        RunnablePassthrough.assign(context1=(lambda x: x["context1"]), context2=(lambda x: format_docs_num(x["context2"])))
        | hybrid_prompt
        | llm.bind_tools([quoted_answer],tool_choice="quoted_answer")
        | output_parser
    )

    chain_with_citations = RunnableParallel(
        {"context1": structured_retriever, "context2": unstructured_retriever, "question": RunnablePassthrough()}
    ).assign(answer=chain).pick(["context2","answer"])

    response = chain_with_citations.invoke(question)

    source_indices = [cite["source_id"] for cite in response["answer"]["citations"]]

    for idx, source_index in enumerate(source_indices):
        path = response["context2"][source_index].metadata['file_path']
        response["answer"]["citations"][idx]["source_path"] = path

    return response["answer"]

def summarize_document(path: str, llm = ChatOpenAI(model="gpt-3.5-turbo-0125")):


    loader = PyMuPDFLoader(path)
    text = loader.load()

    class Summary(BaseModel):

        summary: str = Field(
            ...,
            description="The summary of the text provided by the user.",
        )
        author: str = Field(
            ..., description="Name and title of the author or signer of the original text."
        )

    template = """You are a physician assistant responsible for communicating patient medical information to the doctor.
    Summarize the following medical document into one paragraph, being as concise as possible. Report the name of the author who has signed off the document.

    {text}

    Summarized Text:"""
    prompt = PromptTemplate.from_template(template)

    output_parser = JsonOutputKeyToolsParser(key_name="Summary", first_tool_only=True)

    chain = (
        {"text": RunnablePassthrough()}
        | prompt
        | llm.bind_tools([Summary])
        | output_parser
    )

    return chain.invoke(text)

def organize_documents(problems, llm = ChatOpenAI(model="gpt-3.5-turbo-0125")):

    def format_docs_number(docs):
        return "\n\n".join("Document " + str(i) + ":\n" + doc.page_content for i, doc in enumerate(docs))

    def format_problems(problems):
        return " ".join(str(i) + ": " + prob + "\n" for i, prob in enumerate(problems))

    class ProblemWithDocs(BaseModel):
        problem: str = Field(
            ...,
            description="The medical problem suffered by the patient.",
        )
        summary: str = Field(
            ...,
            description="A brief summary of the patient's medical problem based only on the related documents.",
        )
        documents: List[int] = Field(
            ..., description="The integer IDs of the SPECIFIC documents related to the medical problem."
        )

    class documents_answer(BaseModel):
        """Categorize the included documents using only the medical problems provided."""
        problems: List[ProblemWithDocs] = Field(
            ..., description="The list of medical problems, summaries and integer IDs of their related documents"
        )

    docs = []
    for file in os.listdir('patient'):
        loader = PyMuPDFLoader("patient/" + file)
        docs.extend(loader.load())
    
    template = f"""You are a physician assistant responsible for communicating patient medical information to the doctor.
    For the given list of medical problems experienced by the patient, categorize each document below by the medical problem the document is most related to.
    In addition, write a concise summary (no more than 3 sentences) for each medical problem based only on the documents related to it.

    Problems: {format_problems(problems)}

    Documents:
    {format_docs_number(docs)}

    Answer:"""
    prompt = PromptTemplate.from_template(template)

    output_parser = JsonOutputKeyToolsParser(key_name="documents_answer", first_tool_only=True)

    chain = (
        {"problems": RunnablePassthrough() | format_problems}
        | prompt
        | llm.bind_tools([documents_answer])
        | output_parser
    )
    # The argument actually is ignored
    response = chain.invoke("Categorize each document below.")

    for idx, problem in enumerate(response['problems']):
        source_indices = problem['documents']

        paths = []
        for source_index in source_indices:
            new_path = docs[source_index].metadata['file_path']
            if new_path not in paths:
                paths.append(new_path)
        
        response["problems"][idx]["source_path"] = paths
        del response["problems"][idx]["documents"]
    
    return response["problems"]