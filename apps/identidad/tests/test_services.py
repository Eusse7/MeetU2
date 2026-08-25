"""
Pruebas de la capa de aplicacion de Identidad.

Corren sin base de datos: los servicios reciben repositorios en memoria.
"""
from uuid import uuid4

import pytest

from apps.identidad.application.dtos import (
    ConvertirEnOrganizadorDTO,
    RegistrarUsuarioDTO,
    VincularInteresDTO,
)
from apps.identidad.application.services import (
    ConvertirEnOrganizadorService,
    RegistrarUsuarioService,
    VerificarOrganizadorService,
    VincularInteresService,
)
from apps.identidad.domain.exceptions import (
    CorreoYaRegistrado,
    DatosPerfilInvalidos,
    OrganizadorNoEncontrado,
    UsuarioNoEncontrado,
    YaEsOrganizador,
)
from apps.identidad.domain.models import Organizador, Usuario
from apps.identidad.domain.policies import PoliticaVerificacion
from apps.shared.domain.enums import EstadoValidacion, TipoPerfil
from apps.shared.tests.dobles import (
    CategoriasSiempreExisten,
    InteresRepositoryEnMemoria,
    OrganizadorRepositoryEnMemoria,
    UsuarioRepositoryEnMemoria,
)


def usuario_de_prueba(**kwargs) -> Usuario:
    datos = {
        "id": uuid4(),
        "nombre": "Ana",
        "correo": "ana@meetu2.co",
        "tipo_perfil": TipoPerfil.ASISTENTE,
        "activo": True,
    }
    datos.update(kwargs)
    return Usuario(**datos)


# ------------------------------------------------------------- Registro
def test_registrar_usuario_normaliza_nombre_y_correo():
    repo = UsuarioRepositoryEnMemoria()

    usuario = RegistrarUsuarioService(usuarios=repo).ejecutar(
        RegistrarUsuarioDTO(nombre="  Jhon   Pulgarin ", correo="  A@B.CO ")
    )

    assert usuario.correo == "a@b.co"
    assert usuario.nombre == "Jhon Pulgarin"
    assert usuario.tipo_perfil == TipoPerfil.ASISTENTE
    assert len(repo.items) == 1


def test_correo_duplicado_es_conflicto_409():
    repo = UsuarioRepositoryEnMemoria([usuario_de_prueba(correo="a@b.co")])

    with pytest.raises(CorreoYaRegistrado) as exc:
        RegistrarUsuarioService(usuarios=repo).ejecutar(
            RegistrarUsuarioDTO(nombre="Otro", correo="A@B.co")
        )

    assert exc.value.status_code == 409


def test_correo_malformado_es_validacion_400():
    with pytest.raises(DatosPerfilInvalidos) as exc:
        RegistrarUsuarioService(usuarios=UsuarioRepositoryEnMemoria()).ejecutar(
            RegistrarUsuarioDTO(nombre="Ana", correo="sin-arroba")
        )

    assert exc.value.status_code == 400


# -------------------------------------------------------- Ser organizador
def test_convertir_en_organizador_cambia_el_tipo_de_perfil():
    usuario = usuario_de_prueba()
    usuarios = UsuarioRepositoryEnMemoria([usuario])
    organizadores = OrganizadorRepositoryEnMemoria()

    organizador = ConvertirEnOrganizadorService(
        usuarios=usuarios, organizadores=organizadores
    ).ejecutar(
        ConvertirEnOrganizadorDTO(
            id_usuario=usuario.id, nombre_comercial="Cafe & Ritmo"
        )
    )

    assert organizador.estado_verificacion == EstadoValidacion.PENDIENTE
    assert usuarios.obtener_por_id(usuario.id).tipo_perfil == TipoPerfil.ORGANIZADOR


def test_convertir_dos_veces_es_conflicto_409():
    usuario = usuario_de_prueba()
    organizadores = OrganizadorRepositoryEnMemoria(
        [Organizador(id=uuid4(), usuario=usuario, nombre_comercial="Ya existe")]
    )

    with pytest.raises(YaEsOrganizador):
        ConvertirEnOrganizadorService(
            usuarios=UsuarioRepositoryEnMemoria([usuario]),
            organizadores=organizadores,
        ).ejecutar(
            ConvertirEnOrganizadorDTO(id_usuario=usuario.id, nombre_comercial="Otro")
        )


def test_convertir_usuario_inexistente_es_404():
    with pytest.raises(UsuarioNoEncontrado) as exc:
        ConvertirEnOrganizadorService(
            usuarios=UsuarioRepositoryEnMemoria(),
            organizadores=OrganizadorRepositoryEnMemoria(),
        ).ejecutar(
            ConvertirEnOrganizadorDTO(id_usuario=uuid4(), nombre_comercial="Cafe")
        )

    assert exc.value.status_code == 404


# ------------------------------------------------------------ Verificacion
@pytest.mark.parametrize(
    "aprobado,esperado",
    [(True, EstadoValidacion.VERIFICADO), (False, EstadoValidacion.RECHAZADO)],
)
def test_verificar_organizador_resuelve_el_estado(aprobado, esperado):
    organizador = Organizador(
        id=uuid4(), usuario=usuario_de_prueba(), nombre_comercial="Cafe"
    )
    repo = OrganizadorRepositoryEnMemoria([organizador])

    resultado = VerificarOrganizadorService(organizadores=repo).ejecutar(
        organizador.id, aprobado
    )

    assert resultado.estado_verificacion == esperado


def test_verificar_organizador_inexistente_es_404():
    with pytest.raises(OrganizadorNoEncontrado):
        VerificarOrganizadorService(
            organizadores=OrganizadorRepositoryEnMemoria()
        ).ejecutar(uuid4(), True)


def test_solo_un_organizador_verificado_puede_publicar():
    assert PoliticaVerificacion.puede_publicar(EstadoValidacion.VERIFICADO)
    assert not PoliticaVerificacion.puede_publicar(EstadoValidacion.PENDIENTE)
    assert not PoliticaVerificacion.puede_publicar(EstadoValidacion.RECHAZADO)


# --------------------------------------------------------------- Intereses
def test_vincular_interes_dos_veces_actualiza_el_nivel():
    usuario = usuario_de_prueba()
    intereses = InteresRepositoryEnMemoria()
    servicio = VincularInteresService(
        usuarios=UsuarioRepositoryEnMemoria([usuario]),
        intereses=intereses,
        categorias=CategoriasSiempreExisten(),
    )
    id_categoria = uuid4()

    servicio.ejecutar(
        VincularInteresDTO(
            id_usuario=usuario.id, id_categoria=id_categoria, nivel_afinidad=2
        )
    )
    servicio.ejecutar(
        VincularInteresDTO(
            id_usuario=usuario.id, id_categoria=id_categoria, nivel_afinidad=5
        )
    )

    assert len(intereses.items) == 1
    assert intereses.items[0].nivel_afinidad == 5


def test_vincular_categoria_inexistente_es_400():
    usuario = usuario_de_prueba()

    with pytest.raises(DatosPerfilInvalidos):
        VincularInteresService(
            usuarios=UsuarioRepositoryEnMemoria([usuario]),
            intereses=InteresRepositoryEnMemoria(),
            categorias=CategoriasSiempreExisten(existentes=set()),
        ).ejecutar(
            VincularInteresDTO(id_usuario=usuario.id, id_categoria=uuid4())
        )
