/**
 * Cliente HTTP del front.
 *
 * Toda la aplicacion pasa por rutas relativas: Nginx decide quien responde.
 *   /api/v1/...        -> monolito Django
 *   /api/v2/pagos/...  -> microservicio Flask (Strangler Pattern, Taller 02)
 * Ambos devuelven los errores con la misma forma {error: {codigo, mensaje}},
 * asi que apiFetch no distingue entre uno y otro.
 */
const API_BASE = "/api/v1";
const API_V2 = "/api/v2";

/** Feature toggle del Strangler: lo pinta Django en <body data-pagos-v2>. */
const pagosV2Habilitado = () => document.body?.dataset.pagosV2 === "1";

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

async function apiFetch(ruta, opciones = {}, base = API_BASE) {
  const res = await fetch(`${base}${ruta}`, {
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

  // ------------------------------------------ pagos (microservicio Flask)
  pagar: (datos) =>
    apiFetch("/pagos", { method: "POST", body: JSON.stringify(datos) }, API_V2),

  pagosDeUsuario: (idUsuario) =>
    apiFetch(`/pagos${qs({ id_usuario: idUsuario })}`, {}, API_V2),

  reembolsar: (idReserva) =>
    apiFetch(
      "/pagos/reembolsos",
      { method: "POST", body: JSON.stringify({ id_reserva: idReserva }) },
      API_V2
    ),

  liquidacionOrganizador: (idOrganizador) =>
    apiFetch(`/pagos/organizadores/${idOrganizador}/liquidacion`, {}, API_V2),

  // ------------------------------------------ social (v1 monolito & v2 microservicio)
  crearResena: (datos) =>
    apiFetch("/social/resenas", { method: "POST", body: JSON.stringify(datos) }),

  resenaDeReserva: (idReserva) =>
    apiFetch(`/social/reservas/${idReserva}/resena`),

  resenasDeExperiencia: (idExperiencia) =>
    apiFetch(`/social/experiencias/${idExperiencia}/resenas`),

  metricasExperiencia: (idExperiencia) =>
    apiFetch(`/social/experiencias/${idExperiencia}/metricas`),

  resenasDeOrganizador: (idOrganizador) =>
    apiFetch(`/social/organizadores/${idOrganizador}/resenas`),

  // ------------------------- microservicios v2 (Strangler Pattern >70%)
  socialV2: {
    salud: () => apiFetch("/social/salud", {}, API_V2),
    crearResena: (datos) =>
      apiFetch("/social/resenas", { method: "POST", body: JSON.stringify(datos) }, API_V2),
    resenasExperiencia: (expId) =>
      apiFetch(`/social/resenas${qs({ experiencia_id: expId })}`, {}, API_V2),
    reputacionOrganizador: (orgId) =>
      apiFetch(`/social/organizadores/${orgId}/reputacion`, {}, API_V2),
  },

  notificacionesV2: {
    salud: () => apiFetch("/notificaciones/salud", {}, API_V2),
    enviar: (datos) =>
      apiFetch("/notificaciones/enviar", { method: "POST", body: JSON.stringify(datos) }, API_V2),
    historial: (usuarioId) =>
      apiFetch(`/notificaciones/historial/${usuarioId}`, {}, API_V2),
  },

  catalogoV2: {
    salud: () => apiFetch("/catalogo/salud", {}, API_V2),
    experiencias: (filtros = {}) =>
      apiFetch(`/catalogo/experiencias${qs(filtros)}`, {}, API_V2),
    categorias: () => apiFetch("/catalogo/categorias", {}, API_V2),
    ubicaciones: () => apiFetch("/catalogo/ubicaciones", {}, API_V2),
  },

  metricasOrganizador: (idOrganizador) =>
    apiFetch(`/social/organizadores/${idOrganizador}/metricas`),

  listarResenasRecientes: () =>
    apiFetch("/social/resenas"),

  // ---------------------------------------------------- integraciones (E2)
  clima: (ciudad, lat, lon) =>
    apiFetch(`/integracion/clima${qs({ ciudad, lat, lon })}`),

  planesAliados: () =>
    apiFetch("/integracion/aliados/planes/"),

  solicitarReporteAsincrono: (correo) =>
    apiFetch("/integracion/reportes/asincrono/", {
      method: "POST",
      body: JSON.stringify({ correo }),
    }),

  consultarReporteAsincrono: (taskId) =>
    apiFetch(`/integracion/reportes/asincrono/${taskId}/`),
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

const I18N_EN = {
  // Session & Header
  "Iniciar sesión": "Sign in",
  "Crear cuenta": "Sign up",
  "Organizador": "Organizer",
  "Asistente": "Attendee",
  "Cerrar sesión": "Log out",
  "Sesión cerrada.": "Logged out.",
  "sin sesion": "no session",

  // Titles & Catalog Records
  "Cena a ciegas en El Poblado": "Blind Dining in El Poblado",
  "Picnic y astronomía en Santa Elena": "Picnic & Stargazing in Santa Elena",
  "Taller de cerámica y vino": "Pottery & Wine Workshop",
  "Ruta de café de especialidad": "Specialty Coffee Tour",
  "Cata de café especial": "Specialty Coffee Tasting",
  "Cena clandestina": "Secret Dining",
  "Degustación multisensorial a oscuras con maridaje de cinco tiempos para abrir la conversación y conectar.": "Multi-sensory dining in the dark with five-course pairing to spark conversation and connection.",
  "Observación de constelaciones con telescopio profesional, fogata y canasta gourmet de quesos locales.": "Stargazing with professional telescope, campfire, and gourmet local cheese basket.",
  "Modela tu propia taza o jarrón mientras disfrutas de una selección de vinos orgánicos en un estudio de arte.": "Shape your own mug or vase while enjoying organic wines in an art studio.",
  "Host de la comunidad": "Community Host",
  "afín": "match",
  "PRÓXIMAMENTE": "COMING SOON",

  // Partner Network Experiences
  "Cena en la oscuridad": "Dining in the Dark",
  "Clase de barista y cata de café": "Barista Class & Coffee Tasting",
  "Senderismo guiado por la sierra": "Guided Mountain Hiking",
  "Noche de jazz y tapas": "Jazz & Tapas Night",

  // Categories & Locations
  "Gastronomia": "Gastronomy",
  "Gastronomía": "Gastronomy",
  "Aire libre": "Outdoors",
  "Aventura": "Adventure",
  "Arte": "Art",
  "Creatividad": "Creativity",
  "Bienestar": "Wellness",
  "Musica": "Music",
  "Música": "Music",
  "Juegos de mesa": "Board games",
  "Medellín": "Medellin",
  "Medellin": "Medellin",
  "Madrid": "Madrid",
  "El Poblado": "El Poblado",
  "Santa Elena": "Santa Elena",
  "Laureles": "Laureles",

  // Weather descriptions & recommendations
  "Cielo despejado": "Clear sky",
  "Mayormente despejado": "Mainly clear",
  "Parcialmente nublado": "Partly cloudy",
  "Nublado": "Overcast",
  "Lluvia ligera": "Light rain",
  "Lluvia moderada": "Moderate rain",
  "Tormenta": "Thunderstorm",
  "Clima ideal para actividades y planes al aire libre.": "Ideal weather for outdoor activities and plans.",
  "Clima agradable para disfrutar planes urbanos o al aire libre.": "Pleasant weather to enjoy urban or outdoor plans.",
  "Clima variable; considera llevar abrigo ligero para actividades exteriores.": "Changeable weather; consider bringing a light jacket for outdoor activities.",
  "Probabilidad de lluvia; recomendamos actividades en espacios cubiertos.": "Rain likely; we recommend indoor activities.",

  // Reviews Wall
  "¡Increíble experiencia! Conocí gente maravillosa y el anfitrión fue excepcional.": "Incredible experience! Met wonderful people and the host was exceptional.",
  "Súper recomendado para romper la rutina. La comida estuvo deliciosa y el ambiente inmejorable.": "Highly recommended to break the routine. The food was delicious and the atmosphere unbeatable.",
  "Una tarde mágica. La organización impecable y aprendí muchísimo sobre el tema.": "A magical afternoon. Impeccable organization and I learned so much on the subject.",

  // Cards & Catalog
  "Agotada": "Sold out",
  "Plazas agotadas": "Sold out",
  "Quedan": "Spots left:",
  "plazas": "spots",
  "plazas disponibles": "available spots",
  "desde": "from",
  "Por": "By",
  "Reservar plaza": "Book spot",
  "Reseñas": "Reviews",
  "Guardado en tus planes favoritos ♥": "Saved to your favorite plans ♥",
  "Guardar en favoritos": "Save to favorites",
  "Cargando opiniones...": "Loading reviews...",
  "Cargando comentarios...": "Loading comments...",
  "Cargando métricas...": "Loading metrics...",
  "★ Nuevo en MeetU2": "★ New to MeetU2",
  "★ Nuevo": "★ New",
  "opinión": "review",
  "opiniones": "reviews",
  "opinión verificada": "verified review",
  "opiniones verificadas": "verified reviews",
  "reseñas con asistencia comprobada": "verified attendee reviews",
  "✓ Check-in verificado": "✓ Verified check-in",
  "✓ Asistencia verificada": "✓ Verified attendance",
  "✓ Solo asistentes con check-in": "✓ Only checked-in attendees",
  "Sin comentario escrito": "No written comment",
  "Esta experiencia aún no tiene calificaciones registradas.": "This experience has no reviews yet.",
  "Sé la primera persona en asistir y calificar este plan.": "Be the first to attend and review this plan.",
  "No encontramos experiencias para este filtro. ¡Prueba buscando otra palabra o categoría!": "No experiences found for this filter. Try another keyword or category!",
  "Inicia sesión para calcular tus planes recomendados según tus intereses": "Sign in to get personalized recommendations based on your interests",
  "Catálogo personalizado con afinidad según tus gustos.": "Personalized catalogue matching your interests.",
  "Inicia sesión o regístrate para reservar tu cupo": "Sign in or register to book your spot",
  "disponibles": "available",
  "Procesando...": "Processing...",
  "Confirmar reserva →": "Confirm booking →",
  "Ver en plataforma aliada ↗": "View on partner platform ↗",
  "Cargando planes de la red aliada...": "Loading partner plans...",
  "No hay planes disponibles en la red aliada en este momento.": "No partner plans available right now.",
  "No fue posible conectar con el servicio aliado.": "Could not connect to partner service.",
  "Red Aliada": "Partner Network",
  
  // Bookings / Reservas
  "Inicia sesión para consultar tus reservas": "Sign in to view your bookings",
  "Accede con tu correo para ver tus tickets de asistencia y estado de pagos.": "Log in with your email to view your attendance tickets and payment status.",
  "Iniciar sesión ahora": "Sign in now",
  "Aún no tienes reservas activas": "You have no active bookings yet",
  "Explora los planes recomendados y asegura tu plaza en la comunidad.": "Explore recommended plans and secure your spot in the community.",
  "Explorar catálogo →": "Explore catalogue →",
  "Experiencia": "Experience",
  "Fecha y hora": "Date and time",
  "Ticket": "Ticket",
  "Plazas": "Spots",
  "Total": "Total",
  "Estado": "Status",
  "Acciones": "Actions",
  "Pagar ahora": "Pay now",
  "Cancelar": "Cancel",
  "⭐ Calificar": "⭐ Rate",
  "Reseña publicada": "Review published",
  "Reembolso:": "Refund:",
  "Reembolso": "Refund",
  "PENDIENTE PAGO": "PENDING PAYMENT",
  "PENDIENTE_PAGO": "PENDING PAYMENT",
  "CONFIRMADA": "CONFIRMED",
  "CHECK IN": "CHECKED IN",
  "CHECK_IN": "CHECKED IN",
  "CANCELADA": "CANCELLED",
  "EXPIRADA": "EXPIRED",
  "NO ASISTIO": "NO SHOW",
  "NO_ASISTIO": "NO SHOW",
  "Pago registrado con éxito. ¡Reserva confirmada!": "Payment registered successfully. Booking confirmed!",
  "cancelada por el asistente": "cancelled by attendee",
  "Reembolso aplicado": "Refund applied",

  // Organizer Dashboard
  "Inicia sesión primero para vincular o ver tu perfil de organizador.": "Log in first to link or view your organizer profile.",
  "Inicia sesión en la parte superior y luego crea aquí tu perfil de organizador.": "Log in at the top and then create your organizer profile here.",
  "Sin calificaciones todavía": "No ratings yet",
  "reputación": "reputation",
  "Perfil:": "Profile:",
  "Calificación Promedio": "Average Rating",
  "Total Evaluaciones": "Total Reviews",
  "Tus asistentes aún no han publicado reseñas para tus planes.": "Your attendees have not published reviews for your plans yet.",
  "Pagos procesados": "Processed payments",
  "transacciones": "transactions",
  "Total recaudado bruto": "Gross revenue collected",
  "Reembolsos por cancelaciones": "Refunds from cancellations",
  "Comisión de plataforma (10%)": "Platform fee (10%)",
  "Neto a desembolsar": "Net payout",
  "Aún no has publicado experiencias.": "You have not published experiences yet.",
  "Título": "Title",
  "Precio": "Price",
  "libres": "spots left",
  "Cancelar plan": "Cancel plan",
  "Experiencia cancelada.": "Experience cancelled.",
  "PUBLICADA": "PUBLISHED",
  "VERIFICADO": "VERIFIED",
  "PENDIENTE": "PENDING"
};

function t(texto) {
  if (document.documentElement.lang === "en" && I18N_EN[texto]) {
    return I18N_EN[texto];
  }
  return texto;
}
window.t = t;

function pintarSesion() {
  const usuario = sesion.get();
  
  // Legacy / fallback text container
  const caja = document.getElementById("sesion-actual");
  if (caja) {
    caja.textContent = usuario
      ? `${usuario.nombre} (${usuario.correo})`
      : t("sin sesion");
  }

  // Modern navigation auth container
  const navAuth = document.getElementById("nav-auth-container");
  if (navAuth) {
    if (usuario) {
      const inicial = (usuario.nombre || "U").charAt(0).toUpperCase();
      const rol = usuario.es_organizador ? t("Organizador") : t("Asistente");
      navAuth.innerHTML = `
        <div class="user-session-badge" title="${usuario.correo}">
          <div class="user-avatar-circle">${inicial}</div>
          <div class="user-session-info">
            <span class="user-session-name">${usuario.nombre}</span>
            <span class="user-session-role">${rol}</span>
          </div>
          <button class="btn-logout" onclick="cerrarSesionUsuario()" title="${t("Cerrar sesión")}">✕</button>
        </div>
      `;
    } else {
      navAuth.innerHTML = `
        <button class="btn-link" onclick="abrirModalAuth('login')">${t("Iniciar sesión")}</button>
        <button class="btn-black-pill" onclick="abrirModalAuth('registro')">${t("Crear cuenta")}</button>
      `;
    }
  }
}

function abrirModalAuth(modo = 'login') {
  const modal = document.getElementById("modal-global-auth");
  if (!modal) return;
  const tabLogin = document.getElementById("auth-tab-login");
  const tabRegistro = document.getElementById("auth-tab-registro");
  const panelLogin = document.getElementById("auth-panel-login");
  const panelRegistro = document.getElementById("auth-panel-registro");
  
  if (modo === 'registro') {
    tabLogin?.classList.remove("active");
    tabRegistro?.classList.add("active");
    panelLogin?.classList.add("oculto");
    panelRegistro?.classList.remove("oculto");
  } else {
    tabLogin?.classList.add("active");
    tabRegistro?.classList.remove("active");
    panelLogin?.classList.remove("oculto");
    panelRegistro?.classList.add("oculto");
  }
  modal.classList.remove("oculto");
}

function cerrarModalAuth() {
  document.getElementById("modal-global-auth")?.classList.add("oculto");
}

function abrirModalComoFunciona() {
  document.getElementById("modal-como-funciona")?.classList.remove("oculto");
}

function cerrarModalComoFunciona() {
  document.getElementById("modal-como-funciona")?.classList.add("oculto");
}

function cerrarSesionUsuario() {
  sesion.limpiar();
  toast("Sesión cerrada.");
  if (typeof window.onSesionCambiada === "function") {
    window.onSesionCambiada(null);
  }
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

const dinero = (valor) => {
  const locale = document.documentElement.lang === "en" ? "en-US" : "es-CO";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(valor));
};

const fecha = (iso) => {
  if (!iso) return "-";
  const locale = document.documentElement.lang === "en" ? "en-US" : "es-CO";
  return new Date(iso).toLocaleString(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  });
};

function fechaTarjeta(iso) {
  if (!iso) return t("PRÓXIMAMENTE");
  try {
    const d = new Date(iso);
    const es = document.documentElement.lang !== "en";
    const dias = es
      ? ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"]
      : ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
    const meses = es
      ? ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
      : ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const diaSemana = dias[d.getDay()];
    const diaNum = d.getDate();
    const mes = meses[d.getMonth()];
    const horas = String(d.getHours()).padStart(2, "0");
    const minutos = String(d.getMinutes()).padStart(2, "0");
    return `${diaSemana}, ${diaNum} ${mes} · ${horas}:${minutos}`;
  } catch {
    return "-";
  }
}

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  pintarSesion();
});
