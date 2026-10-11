"""Gradio UI for the AI Resume & Code Analyzer.

Run:  python app.py
"""

import html

import gradio as gr

from config import ANALYSIS_TYPES, DEFAULT_LLM, LLM_CHOICES
from tool.emailer import is_valid_email, send_email_with_pdf
from tool.guardrails import GuardrailError
from tool.pipeline import run_analysis

# --------------------------------------------------------------------------- #
# Theme & CSS
# --------------------------------------------------------------------------- #

theme = gr.themes.Base(
    primary_hue="violet",
    secondary_hue="indigo",
    neutral_hue="slate",
    radius_size=gr.themes.sizes.radius_lg,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
).set(
    body_background_fill_dark="#07070f",
    block_background_fill_dark="rgba(255,255,255,0.03)",
    block_border_color_dark="rgba(255,255,255,0.08)",
    input_background_fill_dark="rgba(255,255,255,0.04)",
    input_border_color_dark="rgba(255,255,255,0.10)",
    button_primary_background_fill="linear-gradient(135deg,#7c3aed 0%,#4f46e5 50%,#06b6d4 100%)",
    button_primary_background_fill_hover="linear-gradient(135deg,#8b5cf6 0%,#6366f1 50%,#22d3ee 100%)",
    button_primary_text_color="white",
    button_primary_shadow="0 8px 30px rgba(99,102,241,0.45)",
)

CSS = """
.gradio-container {
    max-width: 1280px !important;
    margin: auto;
    background:
        radial-gradient(900px 500px at 10% -10%, rgba(124,58,237,0.25), transparent 60%),
        radial-gradient(800px 500px at 100% 0%, rgba(6,182,212,0.18), transparent 55%),
        #07070f !important;
}
footer { display: none !important; }

/* Hero */
.hero { text-align: center; padding: 34px 10px 18px; }
.hero .pill {
    display: inline-block; padding: 6px 14px; border-radius: 999px; font-size: 12px;
    letter-spacing: .08em; text-transform: uppercase; color: #c4b5fd;
    background: rgba(124,58,237,.14); border: 1px solid rgba(167,139,250,.35);
}
.hero h1 {
    font-size: 46px; line-height: 1.1; margin: 16px 0 10px; font-weight: 800;
    background: linear-gradient(90deg,#fff 0%,#c4b5fd 40%,#67e8f9 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { color: #94a3b8; font-size: 16px; max-width: 700px; margin: 0 auto; }
.chips { margin-top: 18px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.chips span {
    font-size: 12px; color: #cbd5e1; padding: 6px 12px; border-radius: 10px;
    background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08);
}

/* Glass cards */
.glass {
    background: rgba(255,255,255,0.035) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(18px);
    padding: 22px !important;
    box-shadow: 0 20px 60px rgba(0,0,0,.45);
}
.section-title {
    font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
    color: #a78bfa; margin: 4px 0 2px;
}
.section-title b {
    display: inline-flex; width: 22px; height: 22px; align-items: center; justify-content: center;
    border-radius: 7px; margin-right: 8px; color: #fff; font-size: 12px;
    background: linear-gradient(135deg,#7c3aed,#06b6d4);
}

/* Buttons */
button.primary { font-weight: 700 !important; letter-spacing: .02em; transition: transform .15s ease; }
button.primary:hover { transform: translateY(-2px); }

/* Stat cards */
.stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; }
.stat {
    padding: 14px 16px; border-radius: 14px;
    background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08);
}
.stat .v { font-size: 22px; font-weight: 800; color: #fff; }
.stat .l { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: .08em; }
.banner { padding: 14px 16px; border-radius: 14px; font-size: 14px; }
.banner.idle { background: rgba(99,102,241,.10); border: 1px dashed rgba(129,140,248,.4); color: #c7d2fe; }
.banner.err  { background: rgba(239,68,68,.10);  border: 1px solid rgba(239,68,68,.45); color: #fecaca; }
.banner.warn { background: rgba(245,158,11,.10); border: 1px solid rgba(245,158,11,.45); color: #fde68a; margin-top: 10px; }
.banner.ok   { background: rgba(16,185,129,.10); border: 1px solid rgba(16,185,129,.45); color: #a7f3d0; margin-top: 10px; }

.report-md { min-height: 420px; max-height: 720px; overflow-y: auto; padding: 6px 10px; }
@media (max-width: 800px) { .stats { grid-template-columns: repeat(2,1fr); } .hero h1 { font-size: 32px; } }
"""

FORCE_DARK = "() => { document.body.classList.add('dark'); }"

HERO = """
<div class="hero">
  <span class="pill">&#10024; Hybrid RAG &middot; Local LLM &middot; Live Web</span>
  <h1>AI Resume &amp; Code Analyzer</h1>
  <p>Upload a resume or code PDF, ask anything, and get an ATS-aware, trend-aligned analysis
     with a downloadable PDF report &mdash; optionally emailed to you.</p>
  <div class="chips">
    <span>&#128274; Guardrails</span><span>&#129504; Ollama</span>
    <span>&#128269; ChromaDB</span><span>&#127760; DuckDuckGo</span><span>&#128231; Email report</span>
  </div>
</div>
"""

IDLE = (
    '<div class="banner idle">Upload a PDF, write your question and press '
    "<b>Analyze</b>. Results will appear here.</div>"
)

EXAMPLES = [
    "Suggest missing AI skills in this resume",
    "Give me a full ATS analysis and improvement plan",
    "Which job roles am I the best fit for right now?",
    "Review this code for security issues and refactoring opportunities",
    "Build a 6-month career roadmap based on current industry trends",
]


def _section(num: int, title: str) -> str:
    return f'<div class="section-title"><b>{num}</b>{title}</div>'


def _banner(kind: str, text: str) -> str:
    return f'<div class="banner {kind}">{text}</div>'


def _stats(result, model: str) -> str:
    cards = [
        (str(result.chunks), "Chunks indexed"),
        (f"{result.words:,}", "Words generated"),
        (f"{result.seconds:.1f}s", "Total time"),
        (html.escape(model), "Model"),
    ]
    inner = "".join(f'<div class="stat"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in cards)
    return f'<div class="stats">{inner}</div>'


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #

def analyze(
    pdf_path,
    query,
    analysis_type,
    job_role,
    model,
    temperature,
    k,
    use_web,
    block_sensitive,
    send_mail,
    receiver,
    sender,
    app_password,
    subject,
    mail_body,
    progress=gr.Progress(),
):
    if not pdf_path:
        return "", None, _banner("err", "Please upload a PDF first.")
    if not (query or "").strip():
        return "", None, _banner("err", "Please enter a question or instruction.")
    if send_mail and not is_valid_email(receiver):
        return "", None, _banner("err", "Enter a valid receiver email, or turn off 'Email the report'.")

    try:
        result = run_analysis(
            pdf_path=pdf_path,
            query=query,
            analysis_type=analysis_type,
            job_role=job_role or "",
            model=model,
            temperature=temperature,
            k=int(k),
            use_web=use_web,
            block_sensitive=block_sensitive,
            on_progress=lambda frac, desc: progress(frac, desc=desc),
        )
    except GuardrailError as e:
        return "", None, _banner("warn", f"&#128737; Blocked by guardrail: {html.escape(str(e))}")
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "connect" in msg.lower() or "refused" in msg.lower():
            msg = (
                "Could not reach Ollama. Start it with <code>ollama serve</code> and make sure the "
                f"model is pulled: <code>ollama pull {html.escape(model)}</code>."
            )
        else:
            msg = html.escape(msg)
        return "", None, _banner("err", f"Something went wrong: {msg}")

    status = _stats(result, model)

    if send_mail:
        progress(0.95, desc="Sending email...")
        try:
            send_email_with_pdf(
                receiver_email=receiver,
                pdf_file=result.pdf_path,
                sender_email=sender or "",
                app_password=app_password or "",
                subject=subject or "AI Analysis Report",
                body=mail_body or "Hi,\n\nPlease find attached the AI-generated analysis report.\n\nRegards,\nAI Assistant",
            )
            status += _banner("ok", f"&#9989; Report emailed to <b>{html.escape(receiver)}</b>")
        except Exception as e:  # noqa: BLE001
            status += _banner("warn", f"Analysis finished, but email failed: {html.escape(str(e))}")

    return result.markdown, result.pdf_path, status


def clear_all():
    return (
        None, "", ANALYSIS_TYPES[0], "", DEFAULT_LLM, 0.3, 6, True, True,
        False, "", "", "", "AI Analysis Report", "", "", None, IDLE,
    )


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #

with gr.Blocks(theme=theme, css=CSS, js=FORCE_DARK, title="AI Resume & Code Analyzer") as demo:
    gr.HTML(HERO)

    with gr.Row(equal_height=False):
        # ---------------- Left: inputs ---------------- #
        with gr.Column(scale=5, elem_classes="glass"):
            gr.HTML(_section(1, "Document"))
            pdf_in = gr.File(
                label="Resume / Code PDF",
                file_types=[".pdf"],
                type="filepath",
                height=140,
            )

            gr.HTML(_section(2, "Your request"))
            with gr.Row():
                analysis_type = gr.Dropdown(ANALYSIS_TYPES, value=ANALYSIS_TYPES[0], label="Analysis type")
                job_role = gr.Textbox(label="Target job role", placeholder="e.g. AI/ML Engineer")
            query = gr.Textbox(
                label="Question / instruction",
                placeholder="What would you like to know about this document?",
                lines=3,
            )
            gr.Examples(EXAMPLES, inputs=query, label="Quick prompts")

            with gr.Accordion("Model & retrieval settings", open=False):
                model = gr.Dropdown(LLM_CHOICES, value=DEFAULT_LLM, allow_custom_value=True, label="Ollama model")
                with gr.Row():
                    temperature = gr.Slider(0, 1, value=0.3, step=0.05, label="Temperature")
                    k = gr.Slider(2, 12, value=6, step=1, label="Chunks to retrieve (k)")
                with gr.Row():
                    use_web = gr.Checkbox(value=True, label="Use live web search")
                    block_sensitive = gr.Checkbox(value=True, label="Block PDFs with sensitive data")

            with gr.Accordion("Email the report", open=False):
                send_mail = gr.Checkbox(value=False, label="Email the PDF report when finished")
                receiver = gr.Textbox(label="Receiver email", placeholder="name@example.com")
                with gr.Row():
                    sender = gr.Textbox(label="Sender Gmail", placeholder="you@gmail.com (or set in .env)")
                    app_password = gr.Textbox(
                        label="Gmail app password", type="password", placeholder="16-character app password"
                    )
                subject = gr.Textbox(label="Subject", value="AI Analysis Report")
                mail_body = gr.Textbox(label="Message (optional)", lines=3, placeholder="Leave empty for the default message")

            with gr.Row():
                run_btn = gr.Button("Analyze  \u2192", variant="primary", size="lg", scale=3)
                clear_btn = gr.Button("Reset", variant="secondary", size="lg", scale=1)

        # ---------------- Right: outputs ---------------- #
        with gr.Column(scale=7, elem_classes="glass"):
            gr.HTML(_section(3, "Results"))
            status = gr.HTML(IDLE)
            with gr.Tabs():
                with gr.Tab("Analysis"):
                    output_md = gr.Markdown(
                        value="",
                        elem_classes="report-md",
                        show_copy_button=True,
                    )
                with gr.Tab("PDF report"):
                    pdf_out = gr.File(label="Download your report", interactive=False)

    gr.HTML(
        '<p style="text-align:center;color:#64748b;font-size:12px;margin-top:18px;">'
        "Runs locally with Ollama &middot; Your PDFs never leave your machine except web-search queries.</p>"
    )

    inputs = [
        pdf_in, query, analysis_type, job_role, model, temperature, k, use_web,
        block_sensitive, send_mail, receiver, sender, app_password, subject, mail_body,
    ]
    run_btn.click(analyze, inputs=inputs, outputs=[output_md, pdf_out, status])
    clear_btn.click(
        clear_all,
        outputs=[
            pdf_in, query, analysis_type, job_role, model, temperature, k, use_web,
            block_sensitive, send_mail, receiver, sender, app_password, subject, mail_body,
            output_md, pdf_out, status,
        ],
    )


if __name__ == "__main__":
    demo.queue().launch()