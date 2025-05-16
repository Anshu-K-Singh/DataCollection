import os
import pandas as pd
import json
import spacy
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini API
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "your-api-key-here")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.3)

# Initialize spaCy for NLP
nlp = spacy.load("en_core_web_sm")

# DataFrame column descriptions for LLM
COLUMN_DESCRIPTIONS = """
The data is stored in a pandas DataFrame with the following columns, representing projects and their associated engineers:

Project-level columns:
- _id: Unique project identifier (string).
- client_name: Name of the client company (string).
- client_id: Unique client identifier (string).
- role: Job role for the project (string).
- experience_range: Required experience range (string, e.g., '5-6' years).
- client_price: Price quoted to the client (integer).
- ss_price: Supersourcing price (integer).
- month_of_engagement: Duration of engagement (string, e.g., '12 Months').
- engagement_type: Type of engagement (string, e.g., 'Full-Time Contract').
- no_requirements: Number of required engineers (integer).
- tentative_start: Expected start time (string, e.g., '2 Week').
- expectations: Description of job expectations (string).
- primary_skills: Primary skills required, comma-separated (string).
- secondary_skills: Secondary skills, comma-separated (string).
- working_time_zone: Work time zone (string).
- travel_preference: Work location preference (string, e.g., 'Remote').
- job_city, job_state, job_country: Job location (strings).
- location: Full location string (string).
- no_of_rounds: Number of interview rounds (integer).
- job_responsibility: Detailed job responsibilities (HTML-formatted string).
- interested_count, interviewing_count, hired_count, rejected_count, shortlisted_count: Counts of engineers in each status (integers).
- createdAt, updatedAt: Timestamps for project creation and update (strings).
- project_id: Unique project identifier (string).
- type: Project type (string).
- job_status_date: Date of last job status update (string).
- platform_type: Platform type (string).
- hiring_type: Hiring type (string).
- job_status: Current job status (string).
- client_point_of_contact_email, client_point_of_contact_mobile, client_point_of_contact_name, client_point_of_contact_designation: Client contact details (strings).

Engineer-level columns (prefixed with 'engineer_'):
- engineer_id: Unique engineer identifier (integer).
- engineer_name: Engineer's name (string).
- engineer_status: Current status (string, e.g., 'interested', 'interviewing', 'hired', 'not_interested').
- engineer_quoted_price: Quoted price for the engineer (string or integer).
- engineer_engineer_role: Engineer's role (string).
- engineer_contract_type: Contract type (string).
- engineer_engineer_experience_years: Years of experience (string).
- engineer_total_interview_rounds: Number of interview rounds (integer).
- engineer_project_duration: Project duration (string).
- engineer_engineer_primary_skill: Engineer's primary skills, comma-separated (string).
- engineer_contract_start_date, engineer_contract_end_date: Contract dates (strings, often null).
- engineer_engineer_email: Engineer's email (string).
- engineer_account_manager_name: Account manager's name (string, often null).
- engineer_resume: URL to engineer's resume (string).
- engineer_lead_type: Lead type (string).
- engineer_company: Company name (string, often null).
- engineer_developer_type: Developer type (string, often null).
- engineer_client_city, engineer_client_state, engineer_client_country: Client location for the engineer (strings).
- engineer_client_industry_type: Client industry (string, often empty).
- engineer_onboarding_date: Onboarding date (string, often null).
- engineer_engineer_mobile: Engineer's mobile number (string).
- engineer_web_app_platform: Platform (string).
- engineer_billing_date, engineer_am_assign_poc, engineer_developer_cost: Billing and cost details (strings, often null).

Job actions:
- job_actions: List of actions for each engineer, with fields: job_interaction_id (string), action_by_name (string), action_type (string, e.g., 'interested'), created_at (string), department_name (string, often null).
"""

# Load and preprocess combined_data.json
def load_data(file_path="combined_data.json"):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Flatten the nested structure
        flat_data = []
        for project in data:
            project_base = {k: v for k, v in project.items() if k != "engineers"}
            engineers = project.get("engineers", [])
            if not engineers:
                flat_data.append(project_base)
            for eng in engineers:
                eng_data = project_base.copy()
                eng_data.update({f"engineer_{k}": v for k, v in eng.items() if k != "job_actions"})
                job_actions = eng.get("job_actions", [])
                eng_data["job_actions"] = job_actions
                flat_data.append(eng_data)
        
        df = pd.DataFrame(flat_data)
        # Convert lists to strings for easier querying
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, list)).any():
                df[col] = df[col].apply(lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x)
        # Ensure numeric columns are properly typed
        numeric_cols = ["client_price", "ss_price", "no_requirements", "no_of_rounds", 
                        "interested_count", "interviewing_count", "hired_count", 
                        "rejected_count", "shortlisted_count", "engineer_total_interview_rounds"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # Handle quoted_price as numeric
        if "engineer_quoted_price" in df.columns:
            df["engineer_quoted_price"] = pd.to_numeric(df["engineer_quoted_price"], errors="coerce")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

# Dynamic query parser using spaCy
def parse_query_to_pandas(query, df):
    query = query.lower()
    doc = nlp(query)
    filters = []
    result_limit = 10
    aggregation = None
    
    # Extract entities and intents
    entities = {
        "role": None,
        "skill": None,
        "location": None,
        "client": None,
        "status": None,
        "experience": None,
        "price": None,
        "action": None
    }
    intent = "filter"  # Default intent
    
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PERSON"]:
            entities["client"] = ent.text
        elif ent.label_ in ["GPE", "LOC"]:
            entities["location"] = ent.text
        elif ent.label_ == "CARDINAL" and "experience" in query:
            entities["experience"] = float(ent.text)
        elif ent.label_ == "MONEY" or (ent.label_ == "CARDINAL" and "price" in query):
            entities["price"] = float(ent.text)
    
    # Extract keywords
    tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
    if "count" in tokens:
        intent = "aggregation"
    elif "average" in tokens or "mean" in tokens:
        intent = "aggregation"
    
    # Map keywords to columns
    for token in tokens:
        if token in ["role", "job"]:
            entities["role"] = next((t.text for t in doc if t.pos_ == "NOUN" and t.text != token), None)
        elif token in ["skill", "skills"]:
            entities["skill"] = next((t.text for t in doc if t.pos_ == "NOUN" and t.text != token), None)
        elif token in ["status"]:
            entities["status"] = next((t.text for t in doc if t.pos_ == "NOUN" and t.text != token), None)
        elif token in ["action", "actions"]:
            entities["action"] = next((t.text for t in doc if t.pos_ == "NOUN" and t.text != token), None)
    
    # Build filters
    if entities["role"]:
        filters.append(f"role.str.contains('{entities['role']}', case=False, na=False) | engineer_engineer_role.str.contains('{entities['role']}', case=False, na=False)")
    if entities["skill"]:
        filters.append(f"primary_skills.str.contains('{entities['skill']}', case=False, na=False) | secondary_skills.str.contains('{entities['skill']}', case=False, na=False) | engineer_engineer_primary_skill.str.contains('{entities['skill']}', case=False, na=False)")
    if entities["location"]:
        filters.append(f"job_city.str.contains('{entities['location']}', case=False, na=False) | job_state.str.contains('{entities['location']}', case=False, na=False) | job_country.str.contains('{entities['location']}', case=False, na=False) | engineer_client_city.str.contains('{entities['location']}', case=False, na=False)")
    if entities["client"]:
        filters.append(f"client_name.str.contains('{entities['client']}', case=False, na=False)")
    if entities["status"]:
        filters.append(f"engineer_status.str.contains('{entities['status']}', case=False, na=False)")
    if entities["experience"]:
        filters.append(f"engineer_engineer_experience_years >= {entities['experience']}")
    if entities["price"]:
        if "above" in query or "more" in query:
            filters.append(f"engineer_quoted_price >= {entities['price']}")
        elif "below" in query or "less" in query:
            filters.append(f"engineer_quoted_price <= {entities['price']}")
    if entities["action"]:
        filters.append(f"job_actions.str.contains('{entities['action']}', case=False, na=False)")
    
    # Handle aggregations
    if intent == "aggregation":
        if "count" in tokens:
            group_by = "engineer_status"
            if "role" in tokens:
                group_by = "engineer_engineer_role"
            elif "client" in tokens:
                group_by = "client_name"
            aggregation = df.groupby(group_by).size().to_dict()
            return aggregation, "aggregation"
        if "average" in tokens or "mean" in tokens:
            group_by = "engineer_engineer_role"
            if "client" in tokens:
                group_by = "client_name"
            aggregation = df.groupby(group_by)["engineer_quoted_price"].mean().dropna().to_dict()
            return aggregation, "aggregation"
    
    # Handle result limit
    for token in doc:
        if token.text == "limit" and token.nbor(1).like_num:
            result_limit = int(token.nbor(1).text)
    
    # Combine filters
    if filters:
        query_str = " & ".join(filters)
        try:
            filtered_df = df.query(query_str, engine="python")
            return filtered_df.head(result_limit), "filter"
        except Exception as e:
            print(f"Query error: {e}")
            return df.head(result_limit), "filter"
    return df.head(result_limit), "filter"

# Generate response using LangChain
def generate_response(query, data, query_type):
    if query_type == "aggregation":
        prompt_template = PromptTemplate(
            input_variables=["query", "data", "column_descriptions"],
            template="""{column_descriptions}

User asked: {query}
Aggregation result: {data}
Provide a clear and concise answer based on the aggregation, using the column descriptions to ensure accuracy."""
        )
        chain = LLMChain(llm=llm, prompt=prompt_template)
        response = chain.run(query=query, data=json.dumps(data, indent=2), column_descriptions=COLUMN_DESCRIPTIONS)
        return response
    
    # Convert DataFrame to JSON-like string
    data_str = data.to_dict(orient="records")
    data_str = json.dumps(data_str, indent=2)
    
    prompt_template = PromptTemplate(
        input_variables=["query", "data", "column_descriptions"],
        template="""{column_descriptions}

You are a chatbot answering questions about project and engineer data. Answer the user's query accurately based on the provided data. Use the column descriptions to understand the data structure and ensure precise responses. Be concise and professional. If no relevant data is found, indicate that clearly.

User query: {query}

Data:
{data}

Answer:"""
    )
    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run(query=query, data=data_str, column_descriptions=COLUMN_DESCRIPTIONS)
    return response

# Main chatbot loop
def chatbot():
    df = load_data()
    if df.empty:
        print("No data loaded. Exiting.")
        return
    
    print("Chatbot started. Type 'exit' to quit.")
    while True:
        query = input("Enter your query: ")
        if query.lower() == "exit":
            break
        
        # Parse query and get filtered data
        filtered_data, query_type = parse_query_to_pandas(query, df)
        
        # Generate response
        response = generate_response(query, filtered_data, query_type)
        print("\nResponse:")
        print(response)
        print()

if __name__ == "__main__":
    chatbot()