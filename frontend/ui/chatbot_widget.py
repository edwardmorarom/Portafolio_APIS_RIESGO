from __future__ import annotations

from html import escape

import streamlit as st

from services.api_client import ApiClientError, get_api_client


_MODULE_HINTS = {
    "capm": "capm",
    "garch": "garch",
    "markowitz": "markowitz",
    "var": "var",
    "cvar": "cvar",
    "perfil": "kyc",
    "dashboard riesgo": "dashboard",
    "renta fija": "nelson_siegel",
    "opciones": "black_scholes",
    "perri": "perri",
    "robo": "roboadvisor",
}


def _normalise_mode(mode: str | None) -> str:
    value = str(mode or "general").strip().lower()
    return "estadistico" if value.startswith("estad") else "general"


def _module_hint(module: str | None) -> str | None:
    value = str(module or "").strip().lower()
    if not value:
        return None

    for needle, hint in _MODULE_HINTS.items():
        if needle in value:
            return hint

    return None


def _ensure_chatbot_state() -> None:
    chatbot_version = "groq_ready_v1"
    if st.session_state.get("risk_chatbot_version") != chatbot_version:
        st.session_state.risk_chatbot_version = chatbot_version
        st.session_state.risk_chatbot_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hola. Soy el asistente IA de riesgo del proyecto. "
                    "Respondere con el proveedor IA configurado en el backend."
                ),
            }
        ]
        st.session_state.risk_chatbot_followups = [
            "Que significa VaR?",
            "Como afecta el horizonte al riesgo?",
            "Que hace este dashboard?",
        ]

    if "risk_chatbot_open" not in st.session_state:
        st.session_state.risk_chatbot_open = False

    if "risk_chatbot_messages" not in st.session_state:
        st.session_state.risk_chatbot_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hola. Soy el asistente de riesgo del proyecto. "
                    "Puedo ayudarte con VaR, CVaR, CAPM, GARCH, Markowitz, Perri, KYC, renta fija y opciones."
                ),
            }
        ]

    if "risk_chatbot_followups" not in st.session_state:
        st.session_state.risk_chatbot_followups = [
            "Que significa VaR?",
            "Como interpreto CAPM?",
            "Que hace Perri?",
        ]


def _message_html(content: str, role: str) -> str:
    clean_content = escape(str(content or "")).replace("\n", "<br>")
    role_class = "user" if role == "user" else "assistant"
    role_label = "Tu" if role == "user" else "Asistente"

    return (
        f'<div class="risk-chat-message {role_class}">'
        f'<div class="risk-chat-role">{role_label}</div>'
        f'<div class="risk-chat-copy">{clean_content}</div>'
        "</div>"
    )


def _floating_chatbot_css(is_open: bool) -> str:
    width = "390px" if is_open else "178px"
    shadow = "0 22px 52px rgba(2, 8, 23, 0.24)" if is_open else "0 14px 34px rgba(2, 8, 23, 0.22)"
    padding = "0.78rem" if is_open else "0"
    background = "rgba(255, 255, 255, 0.96)" if is_open else "transparent"
    border = "1px solid rgba(148, 163, 184, 0.28)" if is_open else "0"

    return f"""
    <style>
        .st-key-risk_chatbot_widget {{
            position: fixed !important;
            right: 1.15rem !important;
            bottom: 1.05rem !important;
            z-index: 999999 !important;
            width: min({width}, calc(100vw - 2rem)) !important;
            background: {background} !important;
            border: {border} !important;
            border-radius: 18px !important;
            box-shadow: {shadow} !important;
            padding: {padding} !important;
            backdrop-filter: blur(18px);
        }}

        .st-key-risk_chatbot_widget * {{
            letter-spacing: 0 !important;
        }}

        .st-key-risk_chatbot_widget button {{
            min-height: 2.45rem !important;
            border-radius: 999px !important;
            font-weight: 900 !important;
            line-height: 1.15 !important;
            white-space: normal !important;
        }}

        .st-key-risk_chatbot_widget textarea {{
            min-height: 5rem !important;
            border-radius: 14px !important;
            font-size: 0.88rem !important;
        }}

        .risk-chat-title-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.58rem;
        }}

        .risk-chat-title {{
            color: #0F172A;
            font-size: 0.98rem;
            font-weight: 950;
            line-height: 1.08;
        }}

        .risk-chat-subtitle {{
            color: #64748B;
            font-size: 0.74rem;
            font-weight: 750;
            line-height: 1.25;
            margin-top: 0.16rem;
        }}

        .risk-chat-status {{
            flex: 0 0 auto;
            color: #166534;
            background: #DCFCE7;
            border: 1px solid #BBF7D0;
            border-radius: 999px;
            padding: 0.24rem 0.48rem;
            font-size: 0.68rem;
            font-weight: 900;
        }}

        .risk-chat-scroll {{
            max-height: min(310px, 48vh);
            overflow-y: auto;
            padding-right: 0.2rem;
            margin: 0.25rem 0 0.62rem 0;
        }}

        .risk-chat-message {{
            border-radius: 14px;
            padding: 0.62rem 0.72rem;
            margin-bottom: 0.46rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
        }}

        .risk-chat-message.assistant {{
            background: #F8FAFC;
            color: #172033;
        }}

        .risk-chat-message.user {{
            margin-left: 2rem;
            background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%);
            border-color: rgba(37, 99, 235, 0.38);
            color: #FFFFFF;
        }}

        .risk-chat-role {{
            font-size: 0.68rem;
            font-weight: 950;
            opacity: 0.72;
            margin-bottom: 0.16rem;
        }}

        .risk-chat-copy {{
            font-size: 0.82rem;
            line-height: 1.34;
            font-weight: 650;
        }}

        .risk-chat-message.user .risk-chat-copy,
        .risk-chat-message.user .risk-chat-role {{
            color: #FFFFFF;
        }}

        .risk-chat-followups {{
            color: #475569;
            font-size: 0.72rem;
            font-weight: 850;
            margin: 0.15rem 0 0.28rem 0;
        }}

        @media (max-width: 720px) {{
            .st-key-risk_chatbot_widget {{
                right: 0.75rem !important;
                bottom: 0.75rem !important;
                width: min({width}, calc(100vw - 1.5rem)) !important;
            }}

            .risk-chat-scroll {{
                max-height: 42vh;
            }}
        }}
    </style>
    """


def _ask_chatbot(question: str, *, mode: str | None, module: str | None) -> None:
    clean_question = str(question or "").strip()
    if not clean_question:
        return

    st.session_state.risk_chatbot_messages.append(
        {"role": "user", "content": clean_question}
    )

    try:
        portfolio_config = st.session_state.get("portfolio_config", {}) or {}
        response = get_api_client().ask_chatbot(
            {
                "question": clean_question,
                "mode": _normalise_mode(mode),
                "module": _module_hint(module),
                "portfolio_context": {
                    "tickers": portfolio_config.get("tickers", []),
                    "weights_pct": portfolio_config.get("weights_pct", []),
                    "horizon": portfolio_config.get("horizon_type"),
                    "benchmark": portfolio_config.get("benchmark", {}),
                },
            }
        )
        answer = response.get("answer") or "No recibi una respuesta valida del backend."
        followups = response.get("suggested_followups", []) or []
    except ApiClientError as exc:
        answer = f"No pude consultar el chatbot del backend: {exc.message}"
        followups = []
    except Exception as exc:
        answer = f"No pude consultar el chatbot del backend: {exc}"
        followups = []

    st.session_state.risk_chatbot_messages.append(
        {"role": "assistant", "content": answer}
    )
    st.session_state.risk_chatbot_followups = [str(item) for item in followups[:3]]


def render_floating_chatbot(
    *,
    module: str | None = None,
    mode: str | None = "general",
) -> None:
    if not st.session_state.get("logged_in"):
        return

    _ensure_chatbot_state()
    is_open = bool(st.session_state.risk_chatbot_open)
    st.markdown(_floating_chatbot_css(is_open), unsafe_allow_html=True)

    with st.container(key="risk_chatbot_widget"):
        if not is_open:
            if st.button("Chatbot", key="risk_chatbot_open_button", use_container_width=True):
                st.session_state.risk_chatbot_open = True
                st.rerun()
            return

        left, right = st.columns([0.78, 0.22], vertical_alignment="center")
        with left:
            st.markdown(
                """
                <div class="risk-chat-title-row">
                    <div>
                        <div class="risk-chat-title">Asistente de riesgo</div>
                        <div class="risk-chat-subtitle">Teoria financiera y modulos del proyecto</div>
                    </div>
                    <div class="risk-chat-status">Online</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            if st.button("X", key="risk_chatbot_close_button", help="Cerrar chatbot"):
                st.session_state.risk_chatbot_open = False
                st.rerun()

        history_html = '<div class="risk-chat-scroll">'
        for message in st.session_state.risk_chatbot_messages[-8:]:
            history_html += _message_html(
                content=message.get("content", ""),
                role=message.get("role", "assistant"),
            )
        history_html += "</div>"
        st.markdown(history_html, unsafe_allow_html=True)

        followups = st.session_state.get("risk_chatbot_followups", []) or []
        if followups:
            st.markdown('<div class="risk-chat-followups">Preguntas rapidas</div>', unsafe_allow_html=True)
            for index, followup in enumerate(followups[:3]):
                if st.button(
                    str(followup),
                    key=f"risk_chatbot_followup_{index}_{abs(hash(str(followup))) % 10000}",
                    use_container_width=True,
                ):
                    _ask_chatbot(str(followup), mode=mode, module=module)
                    st.rerun()

        with st.form("risk_chatbot_form", clear_on_submit=True):
            question = st.text_area(
                "Pregunta al chatbot",
                placeholder="Ej: Como interpreto el CVaR de mi portafolio?",
                label_visibility="collapsed",
                max_chars=1000,
            )
            submitted = st.form_submit_button("Enviar", use_container_width=True)

        if submitted:
            _ask_chatbot(question, mode=mode, module=module)
            st.rerun()
