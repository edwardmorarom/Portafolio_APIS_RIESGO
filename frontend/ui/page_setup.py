from __future__ import annotations

from ui.dashboard_ui import (
    aplicar_estilos_globales,
    render_sidebar_brand,
    render_sidebar_panel,
)


def setup_dashboard_page(
    title: str = "Dashboard Riesgo",
    subtitle: str = "Universidad Santo Tomás",
    logo_path: str = "frontend/assets/escudo_santo_tomas.png",
    modo_default: str = "General",
    filtros_label: str = "Parámetros Del Módulo",
    filtros_expanded: bool = False,
):
    aplicar_estilos_globales(modo="General")

    render_sidebar_brand(
        title=title,
        subtitle=subtitle,
        logo_path=logo_path,
    )

    modo, filtros_sidebar = render_sidebar_panel(
        modo_default=modo_default,
        filtros_label=filtros_label,
        filtros_expanded=filtros_expanded,
    )

    aplicar_estilos_globales(modo=modo)

    return modo, filtros_sidebar