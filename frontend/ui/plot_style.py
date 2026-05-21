from __future__ import annotations

import plotly.graph_objects as go

from ui.theme import get_theme_tokens


def style_plotly_figure(
    fig: go.Figure,
    modo: str = "General",
    title: str | None = None,
    xaxis_title: str = "",
    yaxis_title: str = "",
    height: int = 470,
    show_xgrid: bool = True,
    show_ygrid: bool = True,
    legend_orientation: str = "h",
) -> go.Figure:
    theme = get_theme_tokens(modo)
    font_color = "#6B7280" if modo == "Estadístico" else "#334155"
    legend_font = "#334155" if modo == "General" else "#5B2132"
    axis_title = "#0F172A"
    tick_color = "#475569"
    grid_color = "rgba(148, 163, 184, 0.16)"

    if title:
        fig.update_layout(
            title=dict(
                text=title,
                x=0.02,
                xanchor="left",
                font=dict(size=18, color=axis_title),
            )
        )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=font_color, size=13),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=height,
        margin=dict(l=42, r=24, t=56, b=38),
        legend=dict(
            orientation=legend_orientation,
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(255,255,255,0)",
            bordercolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=11, color=legend_font),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="rgba(148, 163, 184, 0.28)",
            font=dict(color="#0F172A", size=12),
        ),
    )

    fig.update_xaxes(
        showgrid=show_xgrid,
        gridcolor=grid_color,
        zeroline=False,
        showline=True,
        linecolor="rgba(100, 116, 139, 0.38)",
        tickfont=dict(color=tick_color, size=12),
        title_font=dict(color=axis_title, size=13, family="Inter, sans-serif"),
    )

    fig.update_yaxes(
        showgrid=show_ygrid,
        gridcolor=grid_color,
        zeroline=False,
        showline=True,
        linecolor="rgba(100, 116, 139, 0.38)",
        tickfont=dict(color=tick_color, size=12),
        title_font=dict(color=axis_title, size=13, family="Inter, sans-serif"),
    )

    try:
        fig.update_coloraxes(
            colorbar=dict(
                tickfont=dict(color=theme["TEXT_SOFT"], size=11),
                title=dict(font=dict(color=theme["TEXT_MAIN"], size=12)),
            )
        )
    except Exception:
        pass

    return fig


def add_reference_line(
    fig: go.Figure,
    y: float,
    color: str = "rgba(100, 116, 139, 0.65)",
    dash: str = "dash",
):
    fig.add_hline(y=y, line_dash=dash, line_color=color)
    return fig
