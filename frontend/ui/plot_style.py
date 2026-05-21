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
    horizontal_legend = legend_orientation == "h"
    margin = dict(
        l=66 if yaxis_title else 44,
        r=34 if horizontal_legend else 140,
        t=112 if horizontal_legend else 78,
        b=62 if xaxis_title else 44,
    )
    legend = (
        dict(
            orientation="h",
            yanchor="bottom",
            y=1.18,
            xanchor="left",
            x=0.0,
            bgcolor=theme["PANEL_BG"],
            bordercolor=theme["BORDER_SOFT"],
            borderwidth=1,
            font=dict(size=11, color=theme["TEXT_MAIN"]),
            itemwidth=30,
        )
        if horizontal_legend
        else dict(
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.02,
            bgcolor=theme["PANEL_BG"],
            bordercolor=theme["BORDER_SOFT"],
            borderwidth=1,
            font=dict(size=11, color=theme["TEXT_MAIN"]),
        )
    )

    if title:
        fig.update_layout(
            title=dict(
                text=title,
                x=0.02,
                xanchor="left",
                font=dict(size=24, color=theme["TEXT_MAIN"]),
            )
        )

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=theme["PANEL_BG_2"],
        font=dict(color=theme["TEXT_MAIN"], size=13),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=height,
        margin=margin,
        legend=legend,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=theme["TEXT_MAIN"],
            bordercolor=theme["ACCENT_MAIN"],
            font=dict(color=theme["TEXT_INVERSE"], size=12),
        ),
    )

    fig.update_xaxes(
        showgrid=show_xgrid,
        gridcolor=theme["PLOT_GRID"],
        zeroline=False,
        showline=True,
        linecolor=theme["TEXT_MUTED"],
        linewidth=1,
        ticks="outside",
        tickcolor=theme["TEXT_MUTED"],
        ticklen=5,
        automargin=True,
        tickfont=dict(color=theme["TEXT_SOFT"], size=12),
        title_font=dict(color=theme["TEXT_MAIN"], size=14, family="Inter, sans-serif"),
    )

    fig.update_yaxes(
        showgrid=show_ygrid,
        gridcolor=theme["PLOT_GRID"],
        zeroline=False,
        showline=True,
        linecolor=theme["TEXT_MUTED"],
        linewidth=1,
        ticks="outside",
        tickcolor=theme["TEXT_MUTED"],
        ticklen=5,
        automargin=True,
        tickfont=dict(color=theme["TEXT_SOFT"], size=12),
        title_font=dict(color=theme["TEXT_MAIN"], size=14, family="Inter, sans-serif"),
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
