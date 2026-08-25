/**
 * Cliente HTTP del front.
 *
 * Toda la aplicacion pasa por API_BASE. En el Horizonte 3 (ver Wiki) esa
 * constante apunta al API Gateway en lugar del monolito y ningun otro archivo
 * del front cambia.
 */
const API_BASE = "/api/v1";

class ApiError extends Error {
  constructor(mensaje, codigo, status) {
    super(mensaje);
    this.codigo = codigo;
    this.status = status;
  }
}

function csrfToken() {
  const fila = document.cookie
    .split("; ")
    .find((c) => c.startsWith("csrftoken="));
  return fila ? fila.split("=")[1] : "";
}

async function apiFetch(ruta, opciones = {}) {
  const res = await fetch(`${API_BASE}${ruta}`, {
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken(),
    },
    ...opciones,
  });

  const cuerpo = res.status === 204 ? null : await res.json().catch(() => null);

  if (!res.ok) {
    // El backend responde siempre {error: {codigo, mensaje}} para los errores
    // de dominio; DRF usa otra forma para los de validacion de serializer.
    const err = cuerpo?.error;
    const mensaje = err?.mensaje ?? primerMensajeDrf(cuerpo) ?? "Error inesperado";
    throw new ApiError(mensaje, err?.codigo ?? "validacion", res.status);
  }
  return cuerpo;
}

function primerMensajeDrf(cuerpo) {
  if (!cuerpo || typeof cuerpo !== "object") return null;
  const [campo, valor] = Object.entries(cuerpo)[0] ?? [];
  if (!campo) return null;
  const detalle = Array.isArray(valor) ? valor[0] : valor;
  return `${campo}: ${detalle}`;
}

const qs = (params) => {
  const limpio = Object.entries(params).filter(
    ([, v]) => v !== "" && v !== null && v !== undefined
  );
  return limpio.length ? `?${new URLSearchParams(limpio)}` : "";
};

const api = {
  // ---------------------------------------------------------- identidad
  registrarUsuario: (datos) =>
    apiFetch("/identidad/usuarios", { method: "POST", body: JSON.stringify(datos) }),

  buscarUsuarioPorCorreo: (correo) =>
    apiFetch(`/identidad/usuarios/buscar${qs({ correo })}`),

  convertirEnOrganizador: (idUsuario, datos) =>
    apiFetch(`/identidad/usuarios/${idUsuario}/organizador`, {
      method: "POST",
      body: JSON.stringify(datos),
    }),

  perfilOrganizador: (idUsuario) =>
    apiFetch(`/identidad/usuarios/${idUsuario}/perfil-organizador`),

  verificarOrganizador: (idOrganizador, aprobado) =>
    apiFetch(`/identidad/organizadores/${idOrganizador}/verificacion`, {
      method: "PATCH",
      body: JSON.stringify({ aprobado }),
    }),

  listarIntereses: (idUsuario) =>
    apiFetch(`/identidad/usuarios/${idUsuario}/intereses`),

  vincularInteres: (idUsuario, idCategoria, nivel) =>
    apiFetch(`/identidad/usuarios/${idUsuario}/intereses`, {
      method: "POST",
      body: JSON.stringify({ id_categoria: idCategoria, nivel_afinidad: nivel }),
    }),

  // ----------------------------------------------------------- catalogo
  listarExperiencias: (filtros = {}) =>
    apiFetch(`/catalogo/experiencias${qs(filtros)}`),

  obtenerExperiencia: (id) => apiFetch(`/catalogo/experiencias/${id}`),

  recomendaciones: (idUsuario) =>
    apiFetch(`/catalogo/usuarios/${idUsuario}/recomendaciones`),

  publicarExperiencia: (datos) =>
    apiFetch("/catalogo/experiencias", {
      method: "POST",
      body: JSON.stringify(datos),
    }),

  experienciasDeOrganizador: (idOrganizador) =>
    apiFetch(`/catalogo/organizadores/${idOrganizador}/experiencias`),

  cancelarExperiencia: (idExperiencia, idOrganizador, motivo) =>
    apiFetch(`/catalogo/experiencias/${idExperiencia}/cancelacion`, {
      method: "POST",
      body: JSON.stringify({ id_organizador: idOrganizador, motivo }),
    }),

  listarUbicaciones: () => apiFetch("/catalogo/ubicaciones"),

  crearUbicacion: (datos) =>
    apiFetch("/catalogo/ubicaciones", {
      method: "POST",
      body: JSON.stringify(datos),
    }),

  listarCategorias: () => apiFetch("/catalogo/categorias"),

  crearCategoria: (datos) =>
    apiFetch("/catalogo/categorias", {
      method: "POST",
      body: JSON.stringify(datos),
    }),

  // ----------------------------------------------------------- reservas
  reservar: (datos) =>
    apiFetch("/reservas/reservas", { method: "POST", body: JSON.stringify(datos) }),

  misReservas: (idUsuario) =>
    apiFetch(`/reservas/usuarios/${idUsuario}/reservas`),

  confirmarReserva: (idReserva, referenciaPago) =>
    apiFetch(`/reservas/reservas/${idReserva}/confirmacion`, {
      method: "POST",
      body: JSON.stringify({ referencia_pago: referenciaPago }),
    }),

  cancelarReserva: (idReserva, idUsuario, motivo) =>
    apiFetch(`/reservas/reservas/${idReserva}/cancelacion`, {
      method: "POST",
      body: JSON.stringify({ id_usuario: idUsuario, motivo }),
    }),

  reservasDeExperiencia: (idExperiencia) =>
    apiFetch(`/reservas/experiencias/${idExperiencia}/reservas`),

  checkIn: (codigoTicket, idOrganizador) =>
    apiFetch("/reservas/reservas/check-in", {
      method: "POST",
      body: JSON.stringify({
        codigo_ticket: codigoTicket,
        id_organizador: idOrganizador,
      }),
    }),
};

/* ------------------------------------------------------------------ sesion
 * No hay autenticacion todavia (Entrega 2). Guardamos el usuario activo en el
 * navegador para poder recorrer el flujo completo en la sustentacion.
 */
const sesion = {
  get() {
    try {
      return JSON.parse(localStorage.getItem("meetu2_usuario")) || null;
    } catch {
      return null;
    }
  },
  set(usuario) {
    try {
      localStorage.setItem("meetu2_usuario", JSON.stringify(usuario));
    } catch {
      /* modo privado: la sesion dura lo que dure la pagina */
    }
    pintarSesion();
  },
  limpiar() {
    try {
      localStorage.removeItem("meetu2_usuario");
    } catch {
      /* ignorar */
    }
    pintarSesion();
  },
};

function pintarSesion() {
  const caja = document.getElementById("sesion-actual");
  if (!caja) return;
  const usuario = sesion.get();
  caja.textContent = usuario
    ? `${usuario.nombre} (${usuario.correo})`
    : "sin sesion";
}

/* -------------------------------------------------------------------- ui */
function toast(mensaje, tipo = "info") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = mensaje;
  el.className = `toast ${tipo}`;
  clearTimeout(el._temporizador);
  el._temporizador = setTimeout(() => el.classList.add("oculto"), 4500);
}

function mostrarError(e) {
  toast(`${e.status ?? ""} ${e.codigo ?? ""} · ${e.message}`.trim(), "error");
}

const dinero = (valor) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(valor));

const fecha = (iso) =>
  iso
    ? new Date(iso).toLocaleString("es-CO", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "-";

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", pintarSesion);
