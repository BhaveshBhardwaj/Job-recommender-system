# llm_parser.py
import os
from langchain_groq import ChatGroq
# CORRECTED IMPORTS:
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models import JobQueryStructured

def get_llm_chain():
    """
    Initializes and returns the LangChain runnable for parsing job queries.
    """
    
    # 1. Initialize Groq LLM
    # Make sure GROQ_API_KEY is set in your .env file
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.1
    )

    # 2. Setup the Pydantic parser
    parser = PydanticOutputParser(pydantic_object=JobQueryStructured)

    # 3. Create the Prompt Template
    # This prompt is engineered to handle vague and rural/urban Indian context
    prompt_template = """
    You are an expert recruitment assistant for the Indian job market. 
    A user will provide a query in natural language. This user might be from a rural village or a large urban city. 
    They might use local terms, misspellings, or be very vague (e.g., "I need a computer job" or "10th pass, need work").

    Your task is to parse this query and extract structured information.
    
    GUIDELINES:
    1.  **Skills**: Extract any skill. For "computer job", infer skills like 'MS Office', 'Data Entry', 'Basic Computer'. For "driving", infer 'Driver'.
    2.  **Locations**: Extract locations. If they mention a village, use the village and its nearest major city or district. e.g., "village near Agra" -> ['Agra'].
    3.  **Experience**: Infer 'entry-level' for queries mentioning "10th pass", "12th pass", "fresher", or no experience.
    4.  **Job Titles**: Generate 1-3 likely job titles. e.g., "12th pass data entry" -> "Data Entry Operator", "Back Office Executive".
    5.  **Search Keywords**: This is most important. Generate 3-5 diverse, practical search queries that will be fed into job portals like Naukri, Apna, and Indeed. 
        -   Combine skills and locations.
        -   Include queries for freshers/specific qualifications.
        -   e.g., "data entry jobs near Agra", "12th pass jobs Agra", "fresher computer operator jobs Agra"

    {format_instructions}
    
    USER QUERY:
    "{query}"
    """

    prompt = ChatPromptTemplate.from_template(
        template=prompt_template,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    # 4. Create the chain
    chain = prompt | llm | parser
    
    return chain

# Example of how to run this chain (for testing)
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    chain = get_llm_chain()
    
    # Test with a vague, rural query
    test_query = "Sir, main Rampur gaon se hu, Bareilly ke paas. 12th pass kiya hai aur computer thoda bahut aata hai. Koi kaam dilwa do."
    # Translation: "Sir, I am from Rampur village, near Bareilly. I have passed 12th and know a little bit of computers. Please get me some work."
    
    try:
        result = chain.invoke({"query": test_query})
        print(result)
    except Exception as e:
        print(f"Error: {e}")