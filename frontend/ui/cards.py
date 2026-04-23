from __future__ import annotations

import streamlit as st

from ui.theme import safe_text


def render_chip(text: str):
    st.markdown(
        f'<span class="ui-chip">{safe_text(text)}</span>',
        unsafe_allow_html=True,
    )


def render_chip_row(items: list[str]):
    if not items:
        return

    html = "".join([f'<span class="ui-chip">{safe_text(item)}</span>' for item in items])
    st.markdown(html, unsafe_allow_html=True)


def render_info_card(title: str, body: str):
    st.markdown(
        f"""
        <div class="ui-note">
            <strong>{safe_text(title)}</strong><br>
            {safe_text(body)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_meta_row(items: list[tuple[str, str]]):
    if not items:
        return

    html_parts = []
    for label, value in items:
        html_parts.append(
            f'<span class="ui-chip"><strong>{safe_text(label)}:</strong>&nbsp;{safe_text(value)}</span>'
        )

    st.markdown("".join(html_parts), unsafe_allow_html=True)