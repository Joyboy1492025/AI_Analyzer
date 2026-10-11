"""Prompt + RAG chain."""

from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama

from tool.guardrails import check_banned_content
from tool.web_search import web_search

PROMPT = ChatPromptTemplate.from_template("""
# Role

You are an expert analyst, researcher, career advisor,
software architect, code reviewer, and technology consultant.

Analyze the provided content using:

1. Retrieved Context
2. Latest Web Information
3. Current Industry Trends
4. Best Practices
5. Emerging Technologies

<Context>
{context}
</Context>

## Focus

- Analysis type: {analysis_type} (if "Auto-detect", infer whether the content is a resume or code)
- Target job role: {job_role}

## User Query

{input}

## Instructions

- Answer the user's question accurately.
- Compare the content with current industry standards and trends.
- Identify strengths and weaknesses.
- Suggest missing skills, technologies, concepts, or improvements.
- Recommend relevant tutorials, learning resources, certifications, projects, or research papers.
- Compare against current and emerging trends whenever relevant.
- Provide practical and actionable recommendations.
- Be concise but informative.
- Always return valid Markdown.

---

## Content Specific Analysis

### If Resume

Include:

- ATS Analysis
- Missing Skills
- Industry Readiness
- Certification Suggestions
- Project Suggestions
- Job Role Fit
- Trend Comparison
- Career Roadmap

### If Code

Include:

- Code Review
- Architecture Review
- Security Issues
- Performance Optimizations
- Scalability Suggestions
- Best Practices
- Refactoring Recommendations

#### Format

- IN MARKDOWN
""")


def _validate(inputs: dict) -> dict:
    check_banned_content(inputs["query"])
    check_banned_content(inputs.get("job_role", ""))
    return inputs


def _web_query(inputs: dict) -> str:
    role = inputs.get("job_role", "").strip()
    base = f"{role} {inputs['query']}".strip() if role else inputs["query"]
    return f"{base} latest industry trends"[:200]


def build_chain(retriever, model: str, temperature: float, use_web: bool):
    llm = ChatOllama(model=model, temperature=temperature)

    def hybrid_context(inputs: dict) -> str:
        docs = retriever.invoke(inputs["query"])
        pdf_context = "\n\n".join(d.page_content for d in docs)

        web_context = "Web search disabled."
        if use_web:
            try:
                web_context = web_search.invoke(_web_query(inputs))
            except Exception:
                web_context = "No web results"

        return f"PDF Context:\n{pdf_context}\n\nWeb Context:\n{web_context}"

    return (
        RunnableLambda(_validate)
        | {
            "context": RunnableLambda(hybrid_context),
            "input": itemgetter("query"),
            "analysis_type": itemgetter("analysis_type"),
            "job_role": itemgetter("job_role"),
        }
        | PROMPT
        | llm
        | StrOutputParser()
    )