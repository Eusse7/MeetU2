"""
Patron Builder aplicado a `Experiencia`, la entidad mas compleja del sistema.

Por que Builder y no un constructor normal:

1. Alta cardinalidad de parametros (13 campos, 5 opcionales) y varios de ellos
   son *derivados*: `cupo_disponible` nace del `cupo_maximo`, el `estado`
   depende de si se publica al vuelo, el `precio` puede llevar descuento.
2. La construccion es **validada por pasos**: cada `con_*` aplica la politica de
   dominio que le corresponde, de modo que es imposible obtener un objeto a
   medio construir o incoherente. El error se detecta en el paso culpable y no
   al final con un mensaje generico.
3. Aisla al servicio de aplicacion de los detalles de armado: el servicio
   orquesta (permisos, transaccion, notificacion) y el builder ensambla.

Uso tipico:

    experiencia = (
        ExperienciaBuilder(ahora=timezone.now())
        .para_organizador(id_org)
        .con_titulo("Cata de cafe")
        .en_ubicacion(ubicacion)
        .en_fecha(fecha)
        .con_precio(Decimal("50000"), descuento_porcentaje=Decimal("0.1"))
        .con_cupo(12)
        .publicada()
        .construir()
    )
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from apps.catalogo.domain.enums import EstadoExperiencia, Modalidad
from apps.catalogo.domain.exceptions import DatosExperienciaInvalidos
from apps.catalogo.domain.models import CategoriaInteres, Experiencia, Ubicacion
from apps.catalogo.domain.policies import (
    CalculadoraPrecio,
    PoliticaAforo,
    PoliticaAgenda,
)

TITULO_MINIMO = 5


class ExperienciaBuilder:
    """Ensambla una `Experiencia` valida paso a paso. No toca la base de datos."""

    def __init__(self, ahora: datetime):
        self._ahora = ahora
        self._organizador_id: UUID | None = None
        self._titulo: str | None = None
        self._descripcion: str = ""
        self._modalidad: str = Modalidad.PRESENCIAL
        self._fecha_hora: datetime | None = None
        self._duracion_minutos: int = 120
        self._precio: Decimal | None = None
        self._cupo_maximo: int | None = None
        self._ubicacion: Ubicacion | None = None
        self._categorias: list[CategoriaInteres] = []
        self._estado: str = EstadoExperiencia.BORRADOR

    # ------------------------------------------------------------- pasos
    def para_organizador(self, id_organizador: UUID) -> ExperienciaBuilder:
        self._organizador_id = id_organizador
        return self

    def con_titulo(self, titulo: str, descripcion: str = "") -> ExperienciaBuilder:
        limpio = (titulo or "").strip()
        if len(limpio) < TITULO_MINIMO:
            raise DatosExperienciaInvalidos(
                f"El titulo debe tener al menos {TITULO_MINIMO} caracteres"
            )
        self._titulo = limpio
        self._descripcion = (descripcion or "").strip()
        return self

    def en_ubicacion(self, ubicacion: Ubicacion) -> ExperienciaBuilder:
        if ubicacion is None:
            raise DatosExperienciaInvalidos("La experiencia requiere una ubicacion")
        self._ubicacion = ubicacion
        return self

    def en_fecha(
        self, fecha_hora: datetime, duracion_minutos: int = 120
    ) -> ExperienciaBuilder:
        PoliticaAgenda.validar_fecha(fecha_hora, self._ahora)
        if duracion_minutos < 15:
            raise DatosExperienciaInvalidos("La duracion minima es de 15 minutos")
        self._fecha_hora = fecha_hora
        self._duracion_minutos = duracion_minutos
        return self

    def con_precio(
        self, precio: Decimal, descuento_porcentaje: Decimal = Decimal("0")
    ) -> ExperienciaBuilder:
        base = CalculadoraPrecio.normalizar(Decimal(precio))
        self._precio = CalculadoraPrecio.calcular_precio_final(
            base, Decimal(descuento_porcentaje)
        )
        return self

    def con_cupo(self, cupo_maximo: int) -> ExperienciaBuilder:
        aforo = self._ubicacion.aforo_maximo if self._ubicacion else None
        PoliticaAforo.validar(cupo_maximo, aforo)
        self._cupo_maximo = cupo_maximo
        return self

    def con_modalidad(self, modalidad: str) -> ExperienciaBuilder:
        if modalidad not in Modalidad.values:
            raise DatosExperienciaInvalidos(f"Modalidad desconocida: {modalidad}")
        self._modalidad = modalidad
        return self

    def con_categorias(
        self, categorias: list[CategoriaInteres]
    ) -> ExperienciaBuilder:
        self._categorias = list(categorias or [])
        return self

    def publicada(self) -> ExperienciaBuilder:
        self._estado = EstadoExperiencia.PUBLICADA
        return self

    def como_borrador(self) -> ExperienciaBuilder:
        self._estado = EstadoExperiencia.BORRADOR
        return self

    # ------------------------------------------------------------ producto
    @property
    def categorias(self) -> list[CategoriaInteres]:
        """Se asignan tras persistir: una M2M exige que exista la fila padre."""
        return list(self._categorias)

    def construir(self) -> Experiencia:
        faltantes = [
            nombre
            for nombre, valor in (
                ("organizador", self._organizador_id),
                ("titulo", self._titulo),
                ("ubicacion", self._ubicacion),
                ("fecha_hora", self._fecha_hora),
                ("precio", self._precio),
                ("cupo_maximo", self._cupo_maximo),
            )
            if valor is None
        ]
        if faltantes:
            raise DatosExperienciaInvalidos(
                "Faltan datos obligatorios: " + ", ".join(faltantes)
            )

        return Experiencia(
            organizador_id=self._organizador_id,
            titulo=self._titulo,
            descripcion=self._descripcion,
            modalidad=self._modalidad,
            fecha_hora=self._fecha_hora,
            duracion_minutos=self._duracion_minutos,
            precio=self._precio,
            cupo_maximo=self._cupo_maximo,
            # Invariante: al nacer, todo el cupo esta libre.
            cupo_disponible=self._cupo_maximo,
            estado=self._estado,
            ubicacion=self._ubicacion,
        )
