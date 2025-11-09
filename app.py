import streamlit as st
from datetime import datetime, time, timedelta
import uuid
import json
from collections import Counter

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mi Agenda", layout="centered", initial_sidebar_state="collapsed")

# --- ESTILOS CSS (CON ANIMACIÓN) ---
st.markdown("""
<style>
    /* ... (estilos de botones, día de hoy, etc. sin cambios) ... */
    button[data-testid="baseButton-primary"] { background-color: #4A4A4A; border: 1px solid #4A4A4A; color: white; }
    .today { font-weight: bold; color: #007AFF; }
    .task-count { font-size: 0.7em; font-weight: bold; color: white; background-color: #007AFF; border-radius: 50%; padding: 2px 6px; margin-left: 5px; vertical-align: top; }
    .task-description { font-size: 0.9em; color: #555; padding-left: 10px; border-left: 2px solid #ddd; }
    .task-group-header { font-size: 1.1em; font-weight: bold; margin-top: 20px; padding-bottom: 5px; border-bottom: 2px solid #eee; }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stButton"] button { padding: 0.25rem 0.5rem; font-size: 0.8rem; }
    
    /* ¡NUEVO! Animación de entrada para la lista de tareas */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .task-list-container {
        animation: fadeIn 0.5s ease-out forwards;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE GUARDADO Y CARGA ---
# (Sin cambios)
def guardar_tareas():
    tareas_para_guardar = []
    for tarea in st.session_state.get("tareas", []):
        t = tarea.copy(); t['fecha'] = t['fecha'].isoformat();
        if t.get('hora'): t['hora'] = t['hora'].isoformat()
        tareas_para_guardar.append(t)
    with open("tareas.json", "w") as f: json.dump(tareas_para_guardar, f, indent=4)

def cargar_tareas():
    try:
        with open("tareas.json", "r") as f:
            tareas_cargadas = json.load(f)
            tareas_reales = []
            for t in tareas_cargadas:
                t['fecha'] = datetime.fromisoformat(t['fecha']).date()
                if t.get('hora'): t['hora'] = time.fromisoformat(t['hora'])
                tareas_reales.append(t)
            return tareas_reales
    except (FileNotFoundError, json.JSONDecodeError): return []

# --- INICIALIZACIÓN DE ESTADO ---
if "tareas" not in st.session_state: st.session_state["tareas"] = cargar_tareas()
if "modo_edicion" not in st.session_state: st.session_state["modo_edicion"] = None
if "fecha_vista" not in st.session_state: st.session_state["fecha_vista"] = datetime.now().date()
# ¡NUEVO! Estado para el filtro, por defecto muestra solo las pendientes
if "filtro_actual" not in st.session_state: st.session_state["filtro_actual"] = "Pendientes"

# --- CALLBACKS ---
def actualizar_vista_semanal():
    st.session_state.fecha_vista = st.session_state.fecha_formulario

# --- TÍTULO Y NAVEGACIÓN ---
# (Sin cambios)
st.title("Mi Agenda")
st.markdown("---")
col_izq, col_centro, col_der = st.columns([3, 4, 3])
if col_izq.button("‹ Semana Anterior", use_container_width=True): st.session_state.fecha_vista -= timedelta(days=7); st.rerun()
if col_centro.button("Semana Actual (Hoy)", use_container_width=True): st.session_state.fecha_vista = datetime.now().date(); st.rerun()
if col_der.button("Semana Siguiente ›", use_container_width=True): st.session_state.fecha_vista += timedelta(days=7); st.rerun()

# --- VISTA DE SEMANA DINÁMICA ---
# (Sin cambios)
hoy = datetime.now().date(); vista_actual = st.session_state.fecha_vista
dia_inicio_semana = vista_actual - timedelta(days=vista_actual.weekday()); dia_fin_semana = dia_inicio_semana + timedelta(days=6)
st.header(f"{dia_inicio_semana.strftime('%d %b')} - {dia_fin_semana.strftime('%d %b %Y')}")
fechas_tareas = [t["fecha"] for t in st.session_state.tareas]; contador_tareas = Counter(fechas_tareas)
columnas_dias = st.columns(7); nombres_dias = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
for i, col in enumerate(columnas_dias):
    dia_actual_loop = dia_inicio_semana + timedelta(days=i)
    with col:
        st.write(f"**{nombres_dias[i]}**")
        clase_hoy = "today" if dia_actual_loop == hoy else ""
        contador_html = f"<span class='task-count'>{contador_tareas[dia_actual_loop]}</span>" if contador_tareas[dia_actual_loop] > 0 else ""
        st.markdown(f"<p class='{clase_hoy}' style='text-align:center;'>{dia_actual_loop.day} {contador_html}</p>", unsafe_allow_html=True)
st.markdown("---")

# --- FORMULARIO ---
# (La lógica es la misma, solo añadimos el toast al guardar)
if st.session_state.modo_edicion is None:
    if st.button("➕ Añadir Nueva Tarea", use_container_width=True): st.session_state.modo_edicion = "nueva_tarea"; st.rerun()
else:
    tarea_actual = {};
    if st.session_state.modo_edicion != "nueva_tarea": tarea_actual = next((t for t in st.session_state.tareas if t["id"] == st.session_state.modo_edicion), {})
    titulo_formulario = "Editar Tarea" if tarea_actual else "Nueva Tarea"
    with st.form(key="formulario_dinamico"):
        st.subheader(titulo_formulario); nombre_tarea = st.text_input("Nombre de la Tarea", value=tarea_actual.get("nombre", ""));
        descripcion_tarea = st.text_area("Descripción (opcional)", value=tarea_actual.get("descripcion", ""));
        fecha_tarea = st.date_input("Fecha", value=tarea_actual.get("fecha", st.session_state.fecha_vista), key="fecha_formulario", on_change=actualizar_vista_semanal);
        st.write("Hora (opcional)"); col_hora, col_min, col_ampm = st.columns(3);
        hora_actual = tarea_actual.get("hora");
        hora_val = hora_actual.hour % 12 if hora_actual and hora_actual.hour % 12 != 0 else (12 if hora_actual else None);
        min_val = f"{hora_actual.minute:02d}" if hora_actual else None;
        ampm_val = "PM" if hora_actual and hora_actual.hour >= 12 else ("AM" if hora_actual else None);
        with col_hora: hora_sel = st.selectbox("Hora", options=list(range(1, 13)), index=hora_val-1 if hora_val else None, placeholder="Hora");
        with col_min: min_sel = st.selectbox("Min", options=[f"{m:02d}" for m in range(0, 60, 5)], index=int(min_val)//5 if min_val else None, placeholder="Minuto");
        with col_ampm: ampm_sel = st.selectbox("AM/PM", options=["AM", "PM"], index=0 if ampm_val == "AM" else (1 if ampm_val == "PM" else None), placeholder="AM/PM");
        prioridad_tarea = st.selectbox("Prioridad", ["Alta", "Media", "Baja"], index=["Alta", "Media", "Baja"].index(tarea_actual.get("prioridad", "Media")));
        col_guardar, col_cancelar = st.columns(2);
        if col_guardar.form_submit_button("Guardar", use_container_width=True, type="primary"):
            if nombre_tarea:
                hora_final = None
                if all([hora_sel, min_sel, ampm_sel]):
                    hora_24 = hora_sel % 12 + (12 if ampm_sel == "PM" and hora_sel != 12 else 0)
                    if ampm_sel == "AM" and hora_sel == 12: hora_24 = 0
                    hora_final = time(hora_24, int(min_sel))
                datos_tarea = {"nombre": nombre_tarea, "descripcion": descripcion_tarea, "fecha": st.session_state.fecha_formulario, "hora": hora_final, "prioridad": prioridad_tarea}
                if st.session_state.modo_edicion == "nueva_tarea":
                    datos_tarea.update({"id": str(uuid.uuid4()), "completada": False})
                    st.session_state.tareas.append(datos_tarea)
                else:
                    tarea_actual.update(datos_tarea)
                st.session_state.modo_edicion = None
                guardar_tareas()
                st.toast('✅ ¡Tarea guardada!', icon='🎉') # ¡NUEVO! Mensaje de confirmación
                st.rerun()
            else: st.warning("El nombre de la tarea no puede estar vacío.")
        if col_cancelar.form_submit_button("Cancelar", use_container_width=True):
            st.session_state.modo_edicion = None; st.rerun()

# --- LISTA DE TAREAS CON FILTROS ---
st.header("Mis Tareas")

# ¡NUEVO! Botones de filtro
st.radio("Filtrar por:", ["Pendientes", "Completadas", "Todas"], key="filtro_actual", horizontal=True)

# ¡NUEVO! Envolvemos la lista en un contenedor para la animación
st.markdown('<div class="task-list-container">', unsafe_allow_html=True)

if not st.session_state["tareas"]:
    st.info("No tienes tareas pendientes.")
else:
    # Lógica de filtrado
    tareas_filtradas = st.session_state.tareas
    if st.session_state.filtro_actual == "Pendientes":
        tareas_filtradas = [t for t in st.session_state.tareas if not t["completada"]]
    elif st.session_state.filtro_actual == "Completadas":
        tareas_filtradas = [t for t in st.session_state.tareas if t["completada"]]

    if not tareas_filtradas:
        st.info(f"No tienes tareas en la vista '{st.session_state.filtro_actual}'.")
    else:
        tareas_ordenadas = sorted(tareas_filtradas, key=lambda t: (t["fecha"], t.get("hora") or time.min))
        ultimo_dia_mostrado = None
        for tarea in tareas_ordenadas:
            if tarea["fecha"] != ultimo_dia_mostrado:
                nombre_dia_semana = tarea["fecha"].strftime('%A')
                fecha_legible = f"{nombre_dia_semana.capitalize()}, {tarea['fecha'].day} de {tarea['fecha'].strftime('%B')}"
                st.markdown(f"<div class='task-group-header'>{fecha_legible}</div>", unsafe_allow_html=True)
                ultimo_dia_mostrado = tarea["fecha"]
            
            col_check, col_texto, col_edit, col_borrar = st.columns([1, 10, 1, 1])
            with col_check:
                completada = st.checkbox("", value=tarea["completada"], key=f"check_{tarea['id']}", label_visibility="collapsed")
                if completada != tarea["completada"]:
                    tarea["completada"] = completada; guardar_tareas(); st.rerun()
            with col_texto:
                hora_str = f" a las {tarea['hora'].strftime('%I:%M %p')}" if tarea['hora'] else ""
                texto_prioridad = f" ({tarea['prioridad']})"
                texto_tarea = f"**{tarea['nombre']}**{texto_prioridad}{hora_str}"
                if tarea["completada"]: st.markdown(f"~~<span style='color:grey;'>{texto_tarea}</span>~~", unsafe_allow_html=True)
                else: st.markdown(texto_tarea, unsafe_allow_html=True)
                if tarea.get("descripcion"): st.markdown(f"<div class='task-description'>{tarea['descripcion']}</div>", unsafe_allow_html=True)
            with col_edit:
                if st.button("✏️", key=f"edit_{tarea['id']}", help="Editar tarea", use_container_width=True):
                    st.session_state.modo_edicion = tarea["id"]; st.session_state.fecha_vista = tarea['fecha']; st.rerun()
            with col_borrar:
                if st.button("🗑️", key=f"delete_{tarea['id']}", help="Borrar tarea", use_container_width=True):
                    st.session_state["tareas"] = [t for t in st.session_state["tareas"] if t["id"] != tarea["id"]]; guardar_tareas()
                    st.toast('🗑️ Tarea eliminada.', icon='👍') # ¡NUEVO! Mensaje de confirmación
                    st.rerun()
        st.markdown("---")

st.markdown('</div>', unsafe_allow_html=True)
