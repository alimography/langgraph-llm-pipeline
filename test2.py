import os
from typing_extensions import TypedDict
from typing import Annotated,Optional,Literal
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph,START,END,state
from dotenv import load_dotenv
load_dotenv()

from groq import Groq

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

client = Groq()

class State(TypedDict):
    user_query: str
    llm_output: Optional[str]
    isGood: Optional[bool]
    messages: Optional[list]
    retry_count: Optional[int]
    
graph_builder = StateGraph(State)
#create nodes
def chatbot_groq(state:State ):
     
    messages = state.get("messages", [])

    messages.append({
        "role": "user",
        "content": state["user_query"]
    })

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        messages=messages
    )

    answer = response.choices[0].message.content

    messages.append({
        "role": "assistant",
        "content": answer
    })

    state["messages"] = messages
    state["llm_output"] = answer
    state["isGood"] = True

    return state

def evaluation_response(state: State) -> Literal["chatbot_groq", "endnode"]:

    retries = state.get("retry_count", 0)

    if retries >= 2:
        return "endnode"

    if not state.get("isGood"):
        state["retry_count"] = retries + 1
        return "chatbot_groq"

    return "endnode"
        
        
def endnode(state:State):
     return state

def chatbot(state: State):

    messages = state.get("messages", [])

    messages.append({
        "role": "user",
        "content": state["user_query"]
    })

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.7,
        messages=messages
    )

    answer = response.choices[0].message.content

    messages.append({
        "role": "assistant",
        "content": answer
    })

    state["messages"] = messages
    state["llm_output"] = answer
    state["isGood"] = True

    return state

#add nodes to llm 
graph_builder.add_node("chatbot",chatbot)
graph_builder.add_node("chatbot_groq",chatbot_groq)
graph_builder.add_node("endnode",endnode)
#add edges for start to end bassically decides path of node 

# LANGGRAPH FLOW
# (START) -> chatbot node -> samplenode -> (END)
graph_builder.add_edge(START,"chatbot") # here we name of node that is in string # always srtart with START node
graph_builder.add_conditional_edges("chatbot",evaluation_response)
graph_builder.add_edge("chatbot_groq","endnode")
graph_builder.add_edge("endnode",END)


graph = graph_builder.compile()

updated_state =  graph.invoke(State(
     {"user_query": "what is 2+2 ?"}
))


print("updated_state :- ",updated_state)
