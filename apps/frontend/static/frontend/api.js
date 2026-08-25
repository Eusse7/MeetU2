const API_BASE = "/api/v1";   // Horizonte 3: apuntar al Gateway

async function apiFetch(ruta, opciones = {}) {
  const res = await fetch(`${API_BASE}${ruta}`, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });

  const cuerpo = res.status === 204 ? null : await res.json();

  if (!res.ok) {
    const err = cuerpo?.error ?? {};
    throw new ApiError(err.mensaje || "Error inesperado", err.codigo, res.status);
  }
  return cuerpo;
}

class ApiError extends Error {
  constructor(mensaje, codigo, status) {
    super(mensaje);
    this.codigo = codigo;
    this.status = status;
  }
}

const api = {
  registrarUsuario: (datos) =>
    apiFetch("/identidad/usuarios", { method: "POST", body: JSON.stringify(datos) }),

  convertirEnOrganizador: (idUsuario, datos) =>
    apiFetch(`/identidad/usuarios/${idUsuario}/organizador`, {
      method: "POST",
      body: JSON.stringify(datos),
    }),

  verificarOrganizador: (idOrganizador, aprobado) =>
    apiFetch(`/identidad/organizadores/${idOrganizador}/verificacion`, {
      method: "PATCH",
      body: JSON.stringify({ aprobado }),
    }),

  listarExperiencias: () => apiFetch("/catalogo/experiencias"),

  publicarExperiencia: (datos) =>
    apiFetch("/catalogo/experiencias", { method: "POST", body: JSON.stringify(datos) }),
};

function toast(mensaje, tipo = "info") {
  const el = document.getElementById("toast");
  el.textContent = mensaje;
  el.className = `toast ${tipo}`;
  setTimeout(() => el.classList.add("oculto"), 4000);
}