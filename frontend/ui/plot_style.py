from __future__ import annotations

import plotly.graph_objects as go


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
    font_color = "#D7E3F4"
    legend_font = "#EAF2FF"
    axis_title = "#F8FAFC"
    tick_color = "#C9D8EA"
    grid_color = "rgba(148, 163, 184, 0.22)"
    plot_bg = "rgba(8, 15, 28, 0.82)"

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
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=plot_bg,
        font=dict(color=font_color, size=13),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=height,
        margin=dict(l=58, r=28, t=70, b=52),
        legend=dict(
            orientation=legend_orientation,
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(8, 15, 28, 0.42)",
            bordercolor="rgba(148, 163, 184, 0.18)",
            borderwidth=0,
            font=dict(size=11, color=legend_font),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0B1220",
            bordercolor="rgba(125, 211, 252, 0.32)",
            font=dict(color="#F8FAFC", size=12),
        ),
    )

    fig.update_xaxes(
        showgrid=show_xgrid,
        gridcolor=grid_color,
        zeroline=False,
        showline=True,
        linecolor="rgba(203, 213, 225, 0.52)",
        tickfont=dict(color=tick_color, size=12),
        title_font=dict(color=axis_title, size=13, family="Inter, sans-serif"),
    )

    fig.update_yaxes(
        showgrid=show_ygrid,
        gridcolor=grid_color,
        zeroline=False,
        showline=True,
        linecolor="rgba(203, 213, 225, 0.52)",
        tickfont=dict(color=tick_color, size=12),
        title_font=dict(color=axis_title, size=13, family="Inter, sans-serif"),
    )

    try:
        fig.update_coloraxes(
            colorbar=dict(
                tickfont=dict(color=tick_color, size=11),
                title=dict(font=dict(color=axis_title, size=12)),
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
