from __future__ import annotations

from collections.abc import Iterable

import altair as alt
import pandas as pd

from ui.theme import get_theme_tokens


PROFESSIONAL_PALETTE = [
    "#2563EB",
    "#8A1538",
    "#059669",
    "#D97706",
    "#7C3AED",
    "#0F766E",
    "#DC2626",
]


def _series_domain(series_names: Iterable[str]) -> list[str]:
    return [str(name) for name in series_names if str(name)]


def _axis(title: str, theme: dict[str, str], grid: bool = True) -> alt.Axis:
    return alt.Axis(
        title=title,
        titleColor=theme["TEXT_MAIN"],
        titleFontSize=12,
        titleFontWeight=700,
        labelColor=theme["TEXT_SOFT"],
        labelFontSize=11,
        grid=grid,
        gridColor=theme["PLOT_GRID"],
        domain=False,
        tickColor=theme["BORDER_SOFT"],
    )


def _base_chart(data: pd.DataFrame, modo: str, height: int) -> alt.Chart:
    return alt.Chart(data).properties(height=height)


def line_chart(
    data: pd.DataFrame,
    *,
    modo: str,
    x: str,
    y: str,
    color: str,
    series_names: list[str],
    y_title: str,
    height: int = 390,
    y_scale: alt.Scale | None = None,
    stroke_width: int = 2,
) -> alt.Chart:
    theme = get_theme_tokens(modo)
    domain = _series_domain(series_names)

    return _base_chart(data, modo=modo, height=height).mark_line(
        interpolate="monotone",
        strokeWidth=stroke_width,
        point=False,
    ).encode(
        x=alt.X(f"{x}:T", axis=_axis("Fecha", theme, grid=False)),
        y=alt.Y(f"{y}:Q", axis=_axis(y_title, theme, grid=True), scale=y_scale),
        color=alt.Color(
            f"{color}:N",
            scale=alt.Scale(domain=domain, range=PROFESSIONAL_PALETTE[: len(domain)]),
            legend=alt.Legend(
                orient="top",
                direction="horizontal",
                title=None,
                labelLimit=260,
                labelColor=theme["TEXT_MAIN"],
                labelFontSize=11,
                symbolSize=90,
                symbolStrokeWidth=3,
            ),
        ),
        tooltip=[
            alt.Tooltip(f"{x}:T", title="Fecha", format="%Y-%m-%d"),
            alt.Tooltip(f"{color}:N", title="Serie"),
            alt.Tooltip(f"{y}:Q", title=y_title, format=",.4f"),
        ],
    ).interactive(bind_y=False)


def bar_chart(
    data: pd.DataFrame,
    *,
    modo: str,
    x: str,
    y: str,
    color_condition: alt.condition,
    y_title: str,
    height: int = 320,
) -> alt.Chart:
    theme = get_theme_tokens(modo)

    return _base_chart(data, modo=modo, height=height).mark_bar(
        opacity=0.78,
        cornerRadiusTopLeft=2,
        cornerRadiusTopRight=2,
    ).encode(
        x=alt.X(f"{x}:T", axis=_axis("Fecha", theme, grid=False)),
        y=alt.Y(f"{y}:Q", axis=_axis(y_title, theme, grid=True)),
        color=color_condition,
        tooltip=[
            alt.Tooltip(f"{x}:T", title="Fecha", format="%Y-%m-%d"),
            alt.Tooltip(f"{y}:Q", title=y_title, format=",.4f"),
        ],
    ).interactive(bind_y=False)


def horizontal_rule(
    y: float,
    *,
    modo: str,
    label: str | None = None,
    color: str = "#64748B",
) -> alt.Chart:
    data = pd.DataFrame({"y": [float(y)], "label": [label or str(y)]})

    return alt.Chart(data).mark_rule(
        color=color,
        strokeDash=[6, 5],
        opacity=0.75,
    ).encode(
        y=alt.Y("y:Q", axis=None),
        tooltip=[alt.Tooltip("label:N", title="Referencia"), alt.Tooltip("y:Q", title="Valor")],
    )
