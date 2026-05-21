from __future__ import annotations

import streamlit as st


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
