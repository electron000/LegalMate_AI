# FILE: legalchatbot.py (MODIFIED FOR ENHANCED LOGGING AND SAFETY)
import datetime
import re
from typing import Dict, Any, List, Optional

from app.core.llm import get_gemini, get_gemini_for_routing, get_gemini_for_conversation
from app.schemas.chatbot_schemas import AdaptiveResponse, LegalResponse, ApiKeyChatQuery
from app.services.chatbot_prompt import ROUTER_PROMPT, GENERAL_PROMPT
from app.services.planner_prompt import PLANNER_PROMPT_TEMPLATE
from app.core.config import settings

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import Runnable, RunnableBranch, RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from langchain_tavily import TavilySearch


class AdaptiveLegalChatbot:
    def __init__(self, history_store: Optional[Dict] = None):
        """
        Initializes the AdaptiveLegalChatbot service with a history store.
        """
        self.store = history_store if history_store is not None else {}

        # Pydantic schema for the planner chain output
        class ActionPlan(BaseModel):
            justification: str = Field(description="A brief justification for the research strategy.")
            direct_answer_possible: bool = Field(description="True if the query is general and does not require RAG or Web Search.")
            rag_query: Optional[str] = Field(default=None, description="A single, highly specific query for local document search (RAG).")
            web_query: Optional[str] = Field(default=None, description="A single, precise query for web search (Tavily).")
        
        self.action_plan_parser = JsonOutputParser(pydantic_object=ActionPlan)
        self.planner_prompt = PromptTemplate(
            template=PLANNER_PROMPT_TEMPLATE,
            input_variables=["input", "chat_history", "current_date"],
            partial_variables={"format_instructions": self.action_plan_parser.get_format_instructions()},
        )
        self.router_prompt = ROUTER_PROMPT
        self.general_prompt = GENERAL_PROMPT
        
        # This new prompt guides the AI to reason like a senior legal analyst
        self.synthesizer_prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert Indian Legal Analyst. Your task is to synthesize research results (from RAG and Web Search) and your internal knowledge into a comprehensive, multi-layered answer."
                "You must follow a strict analytical framework for all queries involving a person's rights or criminal procedure."
                
                "**ANALYTICAL FRAMEWORK:**"
                "1.  **Constitutional Validity (The 'Puttaswamy' & 'Selvi' Tests):**"
                "    -   Always start with Fundamental Rights (Art. 14, 19, 20, 21)."
                "    -   Is there a privacy violation? Apply the 3-fold test from **K.S. Puttaswamy v. UoI** (legality, legitimate aim, proportionality)."
                "    -   Is there a 'testimonial compulsion' or 'mental privacy' violation (e.g., forcing passwords, narco-analysis, intrusive AI profiling)? Apply principles from **Selvi v. State of Karnataka** and **Art. 20(3)**."

                "2.  **Statutory & Procedural Legality (The 'Letter of the Law'):**"
                "    -   Did the actions follow the correct procedure? Check the **Code of Criminal Procedure, 1973 (CrPC)**."
                "    -   For any **digital** data, decryption, or surveillance, you **MUST** check for compliance with the **Information Technology Act, 2000** (especially **Section 69**)."
                "    -   Consider any other specific statutes (e.g., UAPA, PMLA, etc. if mentioned)."

                "3.  **Data-Specific Laws (The 'DPDP Act' Check):**"
                "    -   If personal data is being processed, how does this comply with the **Digital Personal Data Protection (DPDP) Act, 2023**?"
                "    -   Pay attention to state exemptions (like **Section 17**) but analyze if they are still subject to the `Puttaswamy` proportionality test."

                "4.  **Evidentiary Value & Fair Trial (The 'Evidence Act' Test):**"
                "    -   Is the evidence (especially digital) admissible? Check the **Indian Evidence Act, 1872** (e.g., **Section 65B** for electronic records, **Section 45A** for expert opinion)."
                "    -   **Crucial Connection:** If evidence is opaque (like a 'black box' AI report), does this violate the **Right to a Fair Trial** (part of Art. 21) because the accused cannot mount a defense against it?"
                
                "**RESPONSE INSTRUCTIONS:**"
                "1.  **Start with Empathy and a Direct Answer:** First, respond directly to the user's main concern in simple, clear language. (e.g., 'Yes, you are right to be concerned. This raises significant legal red flags.')"
                "2.  **Present Your Analysis:** After the direct answer, introduce your detailed breakdown. (e.g., 'To explain why, here is a breakdown of the legal principles involved:')"
                "3.  **Synthesize Using the Framework:** Synthesize all gathered context (`rag_results`, `web_results`) using the 4-point framework. Be comprehensive and precise."
                "4.  **Conclude Clearly:** After the analysis, provide a short summary conclusion."
                "-   Always cite the full case names and sections you use in your analysis."
                
                # --- MODIFICATION START ---
                "**CRITICAL SAFETY RULE (NON-NEGOTIABLE):**"
                "1.  You **MUST NOT** provide legal advice. Legal advice includes:"
                "    -   Telling a user what to do in their specific case (e.g., 'You should sue...')."
                "    -   Predicting a legal outcome (e.g., 'You will win your case.')."
                "    -   **CRITICAL:** Recommending or naming specific legal actions, motions, petitions, or documents to file (e.g., 'Your lawyer should file a Section 482 petition' or 'You need to send a legal notice.')."
                
                "2.  **HOW TO HANDLE QUESTIONS ABOUT LEGAL ACTIONS (e.g., 'What can I do?', 'What motion can be filed?'):**"
                "    -   You **MUST** reframe the answer to be descriptive and general, not prescriptive."
                "    -   **Safe (Descriptive):** 'A lawyer can challenge such evidence in court, arguing that it was obtained illegally and violates fundamental rights. They can also petition a higher court to review the charges.'"
                "    -   **Unsafe (Prescriptive):** 'Your lawyer can file an Application to Exclude Evidence or a Quashing Petition under Section 482 of the CrPC.'"
                "    -   Always describe *what* a lawyer can do in general terms, without naming the *specific* legal instrument. Redirect the user to a qualified legal professional for the specific strategy."
                
                "3.  **MANDATORY DISCLAIMER:** You **MUST** end *every* legal analysis with this exact disclaimer:"
                "'I cannot provide legal advice. My purpose is to provide legal information for educational purposes. For advice on your specific situation, please consult with a qualified legal professional.'\n\n"
                # --- MODIFICATION END ---
                
                "--- GATHERED CONTEXT ---"
                "Local Document (RAG) Results: {rag_results}\n"
                "Web Search Results: {web_results}\n"
                "-------------------------"
            )),
            ("human", "Based on that context, please answer my question: {input}"),
        ])

    def _build_full_chain(self, google_api_key: str, cohere_api_key: str, tavily_api_key: str) -> Runnable:
        """
        Factory method to construct the full conversational chain
        using user-provided API keys.
        """
        try:
            # LLM Initialization
            planner_model = get_gemini_for_routing(google_api_key=google_api_key, temperature=0.0)
            synthesizer_model = get_gemini(google_api_key=google_api_key, temperature=0.3)
            router_model = get_gemini_for_routing(google_api_key=google_api_key, temperature=0.0)
            general_model = get_gemini_for_conversation(google_api_key=google_api_key, temperature=0.5)

            # Tool Initialization
            embeddings = None
            if cohere_api_key and cohere_api_key.strip():
                embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=cohere_api_key)
            
            web_search_tool = None
            if tavily_api_key and tavily_api_key.strip():
                web_search_tool = TavilySearch(max_results=3, tavily_api_key=tavily_api_key)
            
        except Exception as e:
            if "ValueError: A Google API Key must be provided" in str(e):
                    raise ValueError(f"Failed to initialize core LLM. Please check your Google API Key. Error: {e}")
            raise ValueError(f"Failed to initialize AI models or tools. Please check your API keys. Error: {e}")
        
        if not embeddings:
            raise ValueError("Cohere API key is mandatory for RAG functionality. Please provide the Cohere API Key.")

        retriever = Chroma(persist_directory=settings.CHROMA_DB_PATH, embedding_function=embeddings).as_retriever(search_kwargs={"k": 5})

        # --- NEW LOGGING HELPERS ---
        def retrieve_from_local_docs(query: str) -> str:
            try:
                docs = retriever.invoke(query)
                return "\n\n---\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                return "Error: Could not retrieve local documents."

        def invoke_web_search(query: str) -> str:
            if not web_search_tool:
                return "Not used. (Tavily Key Missing)"
            try:
                results = web_search_tool.invoke(query)
                return results
            except Exception as e:
                return "Error: Could not retrieve web search results."

        def log_synthesis_start(data):
            return data
        # --- END NEW LOGGING HELPERS ---

        planner_chain = self.planner_prompt | planner_model | self.action_plan_parser
        
        synthesizer_chain = self.synthesizer_prompt | synthesizer_model | StrOutputParser()

        def route_research(plan: dict) -> Runnable:
            # This is now STEP 4
            research_steps = {}
            if plan.get("rag_query"):
                research_steps["rag_results"] = RunnableLambda(lambda x: retrieve_from_local_docs(plan["rag_query"]))
            else:
                research_steps["rag_results"] = RunnableLambda(lambda x: "Not used.")

            if plan.get("web_query"):
                research_steps["web_results"] = RunnableLambda(lambda x: invoke_web_search(plan["web_query"]))
            else:
                research_steps["web_results"] = RunnableLambda(lambda x: "Not used.")
            
            return RunnableParallel(**research_steps)

        research_and_synthesis_chain = (
        RunnablePassthrough.assign(research=RunnableLambda(lambda x: route_research(x['plan'])))
    |   (lambda x: {"input": x["input"], **x["research"]})
            | RunnableLambda(log_synthesis_start) # Added log step before synthesis
            | synthesizer_chain
        )
        
        def route_final_answer(plan_and_input):
            # This is now STEP 3
            plan = plan_and_input["plan"]
            
            if plan.get("direct_answer_possible"):
                return (
                    RunnableLambda(lambda x: synthesizer_chain.invoke({
                        "input": x["input"], 
                        "rag_results": "Not used. (Answered from general knowledge)", 
                        "web_results": "Not used. (Answered from general knowledge)"
                    }))
                )
            else:
                # Add descriptive path logging
                rag_planned = bool(plan.get('rag_query'))
                web_planned = bool(plan.get('web_query'))
                
                path_desc = "Research & Synthesis Path"
                if rag_planned and web_planned:
                    path_desc += " (RAG + Web Search + LLM)"
                elif rag_planned:
                    path_desc += " (RAG + LLM)"
                elif web_planned:
                    path_desc += " (Web Search + LLM)"
                
                return research_and_synthesis_chain

        legal_chain = (
            RunnablePassthrough.assign(plan=planner_chain)
            | RunnableLambda(self._log_action_plan_func) # Step 2
            | RunnableLambda(route_final_answer) # Step 3
        )

        general_chain = self.general_prompt | general_model | StrOutputParser()
        router_chain = self.router_prompt | router_model | StrOutputParser()

        branch = RunnableBranch(
            (lambda x: "legal_query" in x["topic"], legal_chain),
            general_chain
        )

        full_chain = {
            "topic": router_chain,
            "input": lambda x: x["input"],
            "chat_history": lambda x: x["chat_history"],
            "current_date": lambda x: datetime.date.today().isoformat()
        } | RunnableLambda(self._log_router_decision_func) | branch # Step 1
        
        return full_chain

    async def ask(self, query: str, session_id: str, google_api_key: str, cohere_api_key: str, tavily_api_key: str) -> str:
        """
        Internal method to invoke the chain.
        Requires API keys to build and run the chain.
        """
        try:
            chain = self._build_full_chain(google_api_key, cohere_api_key, tavily_api_key)
            
            conversational_chain = RunnableWithMessageHistory(
                chain,
                self.get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            return await conversational_chain.ainvoke({"input": query}, config={"configurable": {"session_id": session_id}})
        except Exception as e:
            if isinstance(e, ValueError) or "API Key" in str(e): 
                    return f"I apologize, but I encountered an issue with the provided API keys: {e}"
            return "I apologize, but I encountered an issue processing your request. Please try again later."
    
    async def ask_structured(self, query: str, session_id: str, google_api_key: str, cohere_api_key: str, tavily_api_key: str) -> AdaptiveResponse:
        """
        Primary public method.
        Accepts query, session, and API keys, then returns a structured response.
        """
        try:
            response_text = await self.ask(query, session_id, google_api_key, cohere_api_key, tavily_api_key)
            
            if "I apologize, but I encountered an issue" in response_text:
                raise Exception(response_text)
                
            metadata = self.get_response_metadata(query, response_text, session_id)
            return AdaptiveResponse(response=response_text, session_id=session_id, response_type="adaptive", metadata=metadata)
        except Exception as e:
            return AdaptiveResponse(response=str(e), session_id=session_id, response_type="error", metadata={"error": str(e)})

    # --- MODIFIED LOGGING FUNCTIONS ---

    def _log_action_plan_func(self, data):
        # This is now STEP 2
        plan = data.get('plan', {})
        return data

    def _log_router_decision_func(self, x):
        # This is now STEP 1
        
        # Log for general conversation
        if "general_conversation" in x.get('topic'):
            pass
        return x

    # --- UNMODIFIED HELPER FUNCTIONS ---

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.store: self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def analyze_query_type(self, query: str) -> str:
        query_lower = query.lower()
        if any(word in query_lower for word in ["how to", "procedure", "steps"]): return "procedural"
        if any(word in query_lower for word in ["what is", "define", "explain"]): return "explanatory"
        if any(word in query_lower for word in ["compare", "vs", "versus"]): return "comparative"
        if any(word in query_lower for word in ["example", "case", "scenario"]): return "example-based"
        if any(word in query_lower for word in ["brief", "quick","summary"]): return "concise"
        return "comprehensive"

    def get_response_metadata(self, query: str, response: str, session_id: str) -> Dict[str, Any]:
        word_count = len(response.split())
        return {"query_type": self.analyze_query_type(query), "has_legal_sections": bool(re.search(r'Section \d+|Article \d+', response)), "complexity": "simple" if word_count < 100 else "moderate" if word_count < 300 else "detailed", "word_count": word_count}

    def get_all_sessions(self) -> List[str]: 
        return list(self.store.keys())

    def get_sessions_with_titles(self) -> List[Dict[str, str]]:
        session_list = []
        for session_id, history in self.store.items():
            title = f"Chat {session_id[:8]}..."
            for message in history.messages:
                if message.__class__.__name__ == "HumanMessage" and message.content:
                    title = message.content[:40] + "..." if len(message.content) > 40 else message.content
                    break
            session_list.append({"id": session_id, "title": title})
        return session_list

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        if session_id not in self.store: return []
        formatted_messages = []
        for message in self.store[session_id].messages: formatted_messages.append({"type": "user" if message.__class__.__name__ == "HumanMessage" else "ai", "content": message.content})
        return formatted_messages

    def clear_session_history(self, session_id: str) -> bool:
        if session_id in self.store:
            self.store[session_id].clear()
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.store:
            del self.store[session_id]
            return True
        return False

    def clear_all_histories(self):
        try:
            self.store.clear()
        except Exception as e: pass


class LegalChatbot(AdaptiveLegalChatbot):
    """Legacy class name for backward compatibility."""

    def __init__(self, history_store: Optional[Dict] = None):
        super().__init__(history_store=history_store)
    
    async def ask(self, query: str, session_id: str, google_api_key: str, cohere_api_key: str, tavily_api_key: str) -> LegalResponse:
        """
        Overrides the base 'ask' to return the legacy format,
        but must now also accept and pass on API keys.
        """
        try:
            adaptive_response = await super().ask(query, session_id, google_api_key, cohere_api_key, tavily_api_key)
            
            if "I apologize, but I encountered an issue" in adaptive_response:
                raise Exception(adaptive_response)
            
            # This part remains the same, just formatting the output
            lines = adaptive_response.split('\n')
            explanation = '\n'.join([line for line in lines if not line.strip().startswith('## ')]).strip()
            # Remove the mandatory disclaimer from the main explanation if it's there
            explanation = explanation.replace("I cannot provide legal advice. My purpose is to provide legal information for educational purposes. For advice on your specific situation, please consult with a qualified legal professional.", "").strip()
            
            sections = re.findall(r'Section \d+[^.\n]*|Article \d+[^.\n]*', adaptive_response)
            summary_sentences = re.split(r'(?<=[.!?])\s+', explanation)
            summary = ' '.join(summary_sentences[:2]).strip() or "Legal information provided."
            
            return LegalResponse(
                explanation=explanation, 
                relevant_sections=list(set(sections)), # Use set to avoid duplicates
                summary=summary, 
                disclaimer="This is not legal advice. Consult a qualified legal professional.", 
                sources=[] # Note: RAG sources are not piped to this legacy format
            )
        except Exception as e:
            return LegalResponse(explanation=str(e), relevant_sections=[], summary="Error processing request.", disclaimer="This is not legal advice. Consult a qualified legal professional.", sources=[])