"""End-to-end orchestration: PDF -> RAG -> LLM -> guardrail -> PDF report."""

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from tool.chain import build_chain
from tool.guardrails import output_guardrail
from tool.rag import build_retriever
from tool.report import create_pdf

ProgressFn = Callable[[float, str], None]


@dataclass
class AnalysisResult:
    markdown: str
    pdf_path: str
    chunks: int
    words: int
    seconds: float


def run_analysis(
    pdf_path: str,
    query: str,
    analysis_type: str,
    job_role: str,
    model: str,
    temperature: float,
    k: int,
    use_web: bool,
    block_sensitive: bool,
    on_progress: Optional[ProgressFn] = None,
) -> AnalysisResult:
    step = on_progress or (lambda frac, desc: None)
    start = time.time()

    step(0.10, "Reading & indexing PDF...")
    retriever, n_chunks = build_retriever(pdf_path, k=k, block_sensitive=block_sensitive)

    step(0.35, "Retrieving context & searching the web...")
    chain = build_chain(retriever, model=model, temperature=temperature, use_web=use_web)

    step(0.55, f"Generating analysis with {model}...")
    answer = chain.invoke(
        {
            "query": query.strip(),
            "analysis_type": analysis_type,
            "job_role": job_role.strip() or "Not specified",
        }
    )
    answer = output_guardrail(answer)

    step(0.90, "Building PDF report...")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    subtitle = f"{Path(pdf_path).name} | {analysis_type}"
    report_path = create_pdf(answer, f"analysis_{stamp}.pdf", subtitle=subtitle)

    return AnalysisResult(
        markdown=answer,
        pdf_path=report_path,
        chunks=n_chunks,
        words=len(answer.split()),
        seconds=time.time() - start,
    )