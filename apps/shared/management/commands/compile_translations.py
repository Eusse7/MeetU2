"""
Comando de gestión para compilar archivos .po a .mo sin requerir gettext binario en el SO.
    python manage.py compile_translations
"""
import array
import struct
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand


def po_to_mo(po_path: Path, mo_path: Path):
    """Compila un archivo .po a formato binario .mo según la especificación GNU gettext."""
    with open(po_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    messages = {}
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith('msgid "'):
            if current_msgid is not None and current_msgstr is not None:
                messages[current_msgid] = current_msgstr
            current_msgid = line[7:-1].replace(r'\"', '"').replace(r'\n', '\n')
            current_msgstr = None
            in_msgid = True
            in_msgstr = False
        elif line.startswith('msgstr "'):
            current_msgstr = line[8:-1].replace(r'\"', '"').replace(r'\n', '\n')
            in_msgid = False
            in_msgstr = True
        elif line.startswith('"') and line.endswith('"'):
            continuation = line[1:-1].replace(r'\"', '"').replace(r'\n', '\n')
            if in_msgid and current_msgid is not None:
                current_msgid += continuation
            elif in_msgstr and current_msgstr is not None:
                current_msgstr += continuation

    if current_msgid is not None and current_msgstr is not None:
        messages[current_msgid] = current_msgstr

    keys = sorted(messages.keys())
    offsets = []
    ids = b""
    strs = b""

    for k in keys:
        v = messages[k]
        k_enc = k.encode("utf-8") + b"\x00"
        v_enc = v.encode("utf-8") + b"\x00"
        offsets.append((len(ids), len(k_enc) - 1, len(strs), len(v_enc) - 1))
        ids += k_enc
        strs += v_enc

    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)

    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets.extend([l1, o1 + keystart])
        voffsets.extend([l2, o2 + valuestart])

    output = struct.pack(
        "Iiiiiii",
        0x950412DE,  # Magic number
        0,           # Version
        len(keys),   # Number of strings
        7 * 4,       # Offset of table with original strings
        7 * 4 + len(keys) * 8,  # Offset of table with translation strings
        0,           # Size of hashing table
        0,           # Offset of hashing table
    )
    output += array.array("i", koffsets).tobytes()
    output += array.array("i", voffsets).tobytes()
    output += ids
    output += strs

    with open(mo_path, "wb") as f:
        f.write(output)


class Command(BaseCommand):
    help = "Compila catálogos de traducción .po a .mo de manera multiplataforma."

    def handle(self, *args, **options):
        locale_dir = settings.BASE_DIR / "locale"
        compilados = 0
        for po_file in locale_dir.rglob("*.po"):
            mo_file = po_file.with_suffix(".mo")
            po_to_mo(po_file, mo_file)
            self.stdout.write(f"Compilado: {po_file.relative_to(settings.BASE_DIR)} -> {mo_file.name}")
            compilados += 1

        self.stdout.write(self.style.SUCCESS(f"Compilación i18n finalizada: {compilados} catálogos listos."))
