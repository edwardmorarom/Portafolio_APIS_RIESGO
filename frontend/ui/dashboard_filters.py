from __future__ import annotations

import streamlit as st


def render_filter_help(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div style="
            border:1px solid rgba(96,165,250,0.28);
            background:rgba(30,64,175,0.16);
            border-radius:12px;
            padding:0.70rem 0.82rem;
            margin:0.15rem 0 0.75rem 0;
            color:#D8E6FF;
            font-size:0.84rem;
            line-height:1.35;">
            <strong>{title}</strong><br>{body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def chip_toggles(
    options: list[tuple[str, str, bool]],
    *,
    key_prefix: str,
) -> dict[str, bool]:
    """
    Renderiza controles tipo chip para capas de gráficos.

    options: lista de (key, label, default_active).
    """
    states: dict[str, bool] = {}
    if not options:
        return states

    if len(options) == 1:
        key, label, default_active = options[0]
        state_key = f"{key_prefix}_{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = bool(default_active)

        active = bool(st.session_state[state_key])
        clicked = st.button(
            label,
            key=f"{state_key}_button",
            type="primary" if active else "secondary",
            use_container_width=True,
        )
        if clicked:
            st.session_state[state_key] = not active
            st.rerun()

        states[key] = bool(st.session_state[state_key])
        return states

    cols = st.columns(len(options), gap="small")
    for col, (key, label, default_active) in zip(cols, options):
        state_key = f"{key_prefix}_{key}"
        if state_key not in st.session_state:
            st.session_state[state_key] = bool(default_active)

        active = bool(st.session_state[state_key])
        with col:
            clicked = st.button(
                label,
                key=f"{state_key}_button",
                type="primary" if active else "secondary",
                use_container_width=True,
            )
            if clicked:
                st.session_state[state_key] = not active
                st.rerun()

        states[key] = bool(st.session_state[state_key])

    return states
