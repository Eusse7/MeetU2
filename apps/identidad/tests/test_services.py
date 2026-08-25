import pytest

from apps.identidad.application.dtos import RegistrarUsuarioDTO
from apps.identidad.application.ports import UsuarioRepositoryPort
from apps.identidad.application.services import RegistrarUsuarioService
from apps.identidad.domain.exceptions import CorreoYaRegistrado


class FakeUsuarioRepository(UsuarioRepositoryPort):
    def __init__(self, correos=()):
        self.correos = set(correos)
        self.guardados = []

    def guardar(self, usuario):
        self.guardados.append(usuario)
        return usuario

    def obtener_por_id(self, id_usuario):
        return None

    def existe_correo(self, correo):
        return correo in self.correos


def test_registra_usuario_normaliza_correo():
    repo = FakeUsuarioRepository()
    servicio = RegistrarUsuarioService(usuarios=repo)

    usuario = servicio.ejecutar(RegistrarUsuarioDTO(nombre="  Jhon ", correo="A@B.CO"))

    assert usuario.correo == "a@b.co"
    assert usuario.nombre == "Jhon"
    assert len(repo.guardados) == 1


def test_correo_duplicado_lanza_conflicto():
    servicio = RegistrarUsuarioService(
        usuarios=FakeUsuarioRepository(correos={"a@b.co"})
    )

    with pytest.raises(CorreoYaRegistrado) as exc:
        servicio.ejecutar(RegistrarUsuarioDTO(nombre="Jhon", correo="a@b.co"))

    assert exc.value.status_code == 409