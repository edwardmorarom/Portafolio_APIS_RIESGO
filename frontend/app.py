from __future__ import annotations

from ui.page_setup import setup_dashboard_page
from ui.dashboard_ui import header_dashboard, nota


modo, _ = setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    filtros_label="Parámetros Generales",
)

header_dashboard(
    "Dashboard de Riesgo de Portafolio",
    "Proyecto integrador de Teoría del Riesgo y APIs",
    modo=modo,
)

if modo == "General":
    nota("Usa el menú lateral para navegar entre módulos del dashboard.")
else:
    nota("Modo estadístico activo. La interfaz prioriza lectura técnica e interpretación cuantitativa.")