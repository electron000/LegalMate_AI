 .\venv\Scripts\Activate.ps1
uvicorn main:app --reload


---------------------------------------------------------------------------
1. The "LLM-Only" Path (Philosophical)
This tests the direct_answer_possible: true path. It must be a broad, conceptual question with no specific laws, cases, or recent dates.

Test Query: "What is the core jurisprudential difference between 'law' and 'justice' from an Indian legal philosophy perspective?"

Purpose: To validate that the planner correctly identifies this as a purely abstract, philosophical query that does not require RAG (no specific sections) or Web Search (no time-sensitive keywords).

Why It Works: Your PRIORITY 3 in the planner_prompt is specifically designed to catch this. It looks for "broad, philosophical, or general questions" like "What is the purpose of law?" This query fits that category perfectly.

Expected Log Output:

[STEP 1] ROUTER: legal_query

[STEP 2] PLANNER: ... Direct Answer (LLM-Only) Possible: true

[STEP 3] EXECUTION: ... PATH: LLM-Only Path

[STEP 4] SYNTHESIS: Synthesizing direct answer (LLM-Only)...

Expected Final Answer Type: A well-reasoned, academic essay from the LLM's base knowledge, which is then structured and made safe by the synthesizer_prompt.

2. The "RAG + LLM" Path (Foundational & Technical)
This tests the PRIORITY 2 (RAG) path. It must be about a specific, foundational, and non-recent legal doctrine tied to a specific statute.

Test Query: "Explain the 'Doctrine of Lis Pendens' as defined under Section 52 of the Transfer of Property Act, 1882."

Purpose: To validate that the planner correctly identifies a query for a specific, unchanging, foundational legal doctrine and its corresponding statute section.

Why It Works: This query is a classic law school question. It's not new (1882), it's not time-sensitive, but it's highly specific. It will fail PRIORITY 1 (Web) and be immediately caught by PRIORITY 2 (RAG) which looks for "Section numbers" and "established legal doctrines."

Expected Log Output:

[STEP 1] ROUTER: legal_query

[STEP 2] PLANNER: ... Direct Answer (LLM-Only) Possible: false

[STEP 2] PLANNER: ... RAG Query Planned: 'Doctrine of Lis Pendens Section 52 Transfer of Property Act 1882'

[STEP 3] EXECUTION: ... PATH: Research & Synthesis Path (RAG + LLM)

[STEP 4] DATA GATHERING: ... EXECUTING RAG...

[STEP 5] SYNTHESIS: ... RAG Context: Present, Web Context: N/A

Expected Final Answer Type: A precise, technical explanation of the doctrine, clearly drawing from the RAG context retrieved from your vector store.

3. The "Web + LLM" Path (Time-Sensitive & New)
This tests the PRIORITY 1 (Web) path. It must be only about a recent event, a new regulation, or a future implementation date.

Test Query: "What is the current implementation status of the 'Bharatiya Nagarik Suraksha Sanhita' (BNSS)? When is it scheduled to fully replace the CrPC as of late 2025?"

Purpose: To validate that the planner correctly identifies time-sensitive keywords ("current status," "scheduled," "late 2025") and prioritizes web search above all else.

Why It Works: This query is entirely time-sensitive. The answer from a RAG store (trained on data from 2023) would be hopelessly out of date. The planner's PRIORITY 1 logic, which looks for "latest," "new," "ongoing," "current," "upcoming," and specific recent dates, will be immediately triggered.

Expected Log Output:

[STEP 1] ROUTER: legal_query

[STEP 2] PLANNER: ... Direct Answer (LLM-Only) Possible: false

[STEP 2] PLANNER: ... Web Query Planned: 'Bharatiya Nagarik Suraksha Sanhita BNSS implementation status 2025'

[STEP 3] EXECUTION: ... PATH: Research & Synthesis Path (Web Search + LLM)

[STEP 4] DATA GATHERING: ... EXECUTING WEB SEARCH...

[STEP 5] SYNTHESIS: ... RAG Context: N/A, Web Context: Present

Expected Final Answer Type: A very factual, up-to-the-minute summary of the law's implementation status, based only on the web search results.

4. The "RAG + Web + LLM" Path (Combo: Foundational + Recent)
This tests the "Combination Rule." It must clearly ask for two things: one foundational (for RAG) and one recent (for Web).

Test Query: "What are the main duties and powers of a 'Resolution Professional' under the Insolvency and Bankruptcy Code (IBC), 2016, and what did the Supreme Court say in its most recent 2024 or 2025 rulings regarding their ability to avoid antecedent transactions?"

Purpose: To validate the planner's most complex path: identifying and separating a query into its foundational and time-sensitive components.

Why It Works: This query is a perfect split:

RAG: "duties and powers of a 'Resolution Professional' under the InsolVency and Bankruptcy Code (IBC), 2016" (Foundational, statutory).

Web: "Supreme Court... most recent 2024 or 2025 rulings... antecedent transactions" (Time-sensitive, recent case law).

Expected Log Output:

[STEP 1] ROUTER: legal_query

[STEP 2] PLANNER: ... Direct Answer (LLM-Only) Possible: false

[STEP 2] PLANNER: ... RAG Query Planned: 'duties and powers of Resolution Professional under IBC 2016'

[STEP 2] PLANNER: ... Web Query Planned: 'Supreme Court recent rulings 2024 2025 on IBC antecedent transactions'

[STEP 3] EXECUTION: ... PATH: Research & Synthesis Path (RAG + Web Search + LLM)

[STEP 4] DATA GATHERING: ... EXECUTING RAG... EXECUTING WEB SEARCH...

[STEP 5] SYNTHESIS: ... RAG Context: Present, Web Context: Present

Expected Final Answer Type: A comprehensive, two-part answer. The first part will explain the RP's powers (from RAG), and the second part will summarize the latest court rulings (from Web).

    ---------------------------

 