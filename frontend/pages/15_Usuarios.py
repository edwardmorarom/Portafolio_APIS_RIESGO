from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.cards import render_info_card
from ui.dashboard_ui import header_dashboard, seccion, tarjeta_kpi
from ui.page_setup import setup_dashboard_page


USERS_PATH = Path("backend/data/users.json")


def _load_users_payload() -> dict:
    if not USERS_PATH.exists():
        return {"users": []}
    payload = json.loads(USERS_PATH.read_text(encoding="utf-8-sig"))
    users = payload.get("users", [])
    payload["users"] = users if isinstance(users, list) else []
    return payload


def _save_users_payload(payload: dict) -> None:
    USERS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=4), encoding="utf-8")


def _objective_label(value: str | None) -> str:
    labels = {
        "preservacion_capital": "Preservación de capital",
        "crecimiento_controlado": "Crecimiento controlado",
        "crecimiento": "Crecimiento agresivo",
    }
    return labels.get(str(value or ""), str(value or "N/D"))


def _users_table(users: list[dict]) -> pd.DataFrame:
    rows = []
    for user in users:
        kyc = user.get("kyc", {}) or {}
        rows.append(
            {
                "Usuario": user.get("username", "N/D"),
                "Nombre": user.get("full_name", "N/D"),
                "Rol": user.get("role", "user"),
                "Edad": kyc.get("age", "N/D"),
                "Experiencia": kyc.get("experience", "N/D"),
                "Tolerancia al riesgo": kyc.get("tolerance", "N/D"),
                "Objetivo principal": _objective_label(kyc.get("investment_objective")),
                "Perfil": kyc.get("fallback_profile", "N/D"),
                "Habeas Data": "Aceptado" if user.get("accepted_habeas_data") else "N/D",
            }
        )
    return pd.DataFrame(rows)


modo, _ = setup_dashboard_page(
    title="P.R.ED",
    subtitle="Desarrolla Tus Portafolios",
    filtros_label=None,
    page_title="Administración de usuarios",
    page_icon="Admin",
)

header_dashboard(
    "Administración de usuarios",
    "Módulo privado para superusuarios: consulta, descarga y remoción de registros.",
    modo=modo,
)

payload = _load_users_payload()
users = payload.get("users", [])
df = _users_table(users)

seccion("Resumen")
c1, c2, c3 = st.columns(3)
with c1:
    tarjeta_kpi("Usuarios registrados", str(len(users)), subtexto="Incluye clientes y superusuarios")
with c2:
    tarjeta_kpi("Superusuarios", str(sum(1 for user in users if user.get("role") == "superuser")), subtexto="Acceso administrativo")
with c3:
    tarjeta_kpi("Clientes", str(sum(1 for user in users if user.get("role") != "superuser")), subtexto="Usuarios finales")

render_info_card(
    "Privacidad",
    "Por seguridad no se muestran contraseñas. La tabla contiene datos personales KYC necesarios para auditoría y soporte del perfil de riesgo.",
)

seccion("Tabla de usuarios")
st.dataframe(df, use_container_width=True, hide_index=True)

csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Descargar tabla CSV",
    data=csv_bytes,
    file_name="usuarios_registrados.csv",
    mime="text/csv",
    use_container_width=True,
)

seccion("Remover usuario")
current_username = str(st.session_state.get("user_username", "")).strip().lower()
removable = [
    user
    for user in users
    if str(user.get("username", "")).strip().lower() != current_username
]

if not removable:
    render_info_card("Sin usuarios removibles", "No hay otros usuarios disponibles para remover.")
else:
    labels = [
        f"{user.get('username', 'N/D')} - {user.get('full_name', 'N/D')} ({user.get('role', 'user')})"
        for user in removable
    ]
    selected = st.selectbox("Usuario a remover", labels)
    selected_user = removable[labels.index(selected)]
    confirm = st.checkbox("Confirmo que deseo remover este usuario del registro.")

    if st.button("Remover usuario", type="primary", use_container_width=True):
        if not confirm:
            st.warning("Marca la confirmación antes de remover.")
        else:
            selected_username = str(selected_user.get("username", "")).strip().lower()
            payload["users"] = [
                user
                for user in users
                if str(user.get("username", "")).strip().lower() != selected_username
            ]
            _save_users_payload(payload)
            st.success(f"Usuario {selected_user.get('username')} removido correctamente.")
            st.rerun()
