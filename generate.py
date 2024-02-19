import os
import zipfile
from enum import StrEnum
from typing import Optional

from requests import request


class IntermediaryType(StrEnum):
    LegacyFabric = "net.fabricmc.intermediary.json"
    LegacyFabricNoAppletOldArgs = "net.fabricmc.intermediary.pre-1.6.json"
    LegacyFabricNoApplet = "net.fabricmc.intermediary.1.6.x.json"
    LegacyFabricV2 = "net.fabricmc.intermediary.v2.json"
    Ornithe = "net.fabricmc.intermediary.ornithe.pre-1.6.json"


def mkdirs(*paths: str):
    for path in paths:
        if not os.path.exists(path):
            os.mkdir(path)


class Generator:
    def __init__(self, minecraft_version: str, lwjgl_version: str, intermediary_type: IntermediaryType, path: str = "temp"):
        self.lwjgl_version = lwjgl_version
        self.minecraft_version = minecraft_version
        self.intermediary_type = intermediary_type
        self.path = path
        self.minecraft_version_additions = self.fix_version(version)

    def process(self, subject: str) -> str:
        subject = subject.replace("${loader_version}", loader_version)
        subject = subject.replace("${minecraft_version}", self.minecraft_version + self.minecraft_version_additions)
        subject = subject.replace("${lwjgl_version}", self.lwjgl_version)
        subject = subject.replace("${lwjgl_name}", "LWJGL 3" if self.lwjgl_version.startswith("3") else "LWJGL 2")
        subject = subject.replace("${lwjgl_uid}", "org.lwjgl3" if self.lwjgl_version.startswith("3") else "org.lwjgl")
        return subject

    def prepare_skeleton(self):
        mkdirs("temp", "temp/patches")
        self.process_file("mmc-pack.json", "instance.cfg")
        self.process_file(f"patches/{self.intermediary_type}", out="patches/net.fabricmc.intermediary.json")

    def create_zip(self):
        with zipfile.ZipFile(f"out/{self.minecraft_version}+loader.{loader_version}.zip", "w") as z:
            z.write("temp/mmc-pack.json", "mmc-pack.json")
            z.write("temp/instance.cfg", "instance.cfg")
            z.write("temp/patches/net.fabricmc.intermediary.json", "patches/net.fabricmc.intermediary.json")
        self.cleanup()

    def cleanup(self):
        for root, dirs, files in os.walk(self.path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for directory in dirs:
                os.rmdir(os.path.join(root, directory))
        os.rmdir(self.path)

    def process_file(self, *files: str, out: Optional[str] = None):
        for file in files:
            with open(f"skel/{file}", "r") as f:
                with open(f"temp/{out if out is not None else file}", "w") as t:
                    t.write(self.process(f.read()))

    @staticmethod
    def fix_version(candidate: str) -> str:
        if candidate.count(".") < 2:
            return ""
        # accounts for the ornithe naming convention
        addition = ""
        if candidate == "1.0":
            addition += ".0"
        if int(candidate.split(".")[1]) < 3:
            addition += "-client"
        return addition


versions = [
    ("1.13.2", "3.1.6", IntermediaryType.LegacyFabric),
    ("1.12.2", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.12", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabricV2),
    ("1.11.2", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.10.2", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.9.4", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.8.9", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.8", "2.9.1", IntermediaryType.LegacyFabric),
    ("1.7.10", "2.9.1", IntermediaryType.LegacyFabric),
    # vanilla provides 2.9.1-nightly-20131017 but multimc and prism meta both use 2.9.4-nightly-20150209
    ("1.7.4", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.7.2", "2.9.0", IntermediaryType.LegacyFabric),
    ("1.6.4", "2.9.0", IntermediaryType.LegacyFabricNoApplet),
    ("1.5.2", "2.9.0", IntermediaryType.LegacyFabricNoAppletOldArgs),
    ("1.4.7", "2.9.0", IntermediaryType.LegacyFabricNoAppletOldArgs),
    ("1.4.2", "2.9.0", IntermediaryType.LegacyFabricNoAppletOldArgs),
    ("1.3.1", "2.9.0", IntermediaryType.LegacyFabricNoAppletOldArgs),
    # ("1.2.5", "2.9.0", IntermediaryType.Ornithe),
    # ("1.1", "2.9.0", IntermediaryType.Ornithe),
    # ("1.0", "2.9.0", IntermediaryType.Ornithe)
    ("15w14a", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.RV-Pre1", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabricV2)
]

loader_version = "0.15.3"
try:
    loader_version = request("GET", "https://meta.fabricmc.net/v2/versions/loader").json()[0].get("version")
except ConnectionError:
    pass
mkdirs("out")

for version, lwjgl, intermediary in versions:
    print(f"generating {version} with LWJGL {lwjgl}...")
    g = Generator(version, lwjgl, intermediary)
    g.prepare_skeleton()
    g.create_zip()
