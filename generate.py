import os
import zipfile
from enum import StrEnum

loader: str = "0.14.22"


class IntermediaryType(StrEnum):
    LegacyFabric = "net.fabricmc.intermediary.json"
    LegacyFabricNoApplet = "net.fabricmc.intermediary.pre-1.7.json"
    LegacyFabricV2 = "net.fabricmc.intermediary.v2.json"
    Ornithe = "net.fabricmc.intermediary.ornithe.json"


def mkdir_if_not_exists(path: str):
    if not os.path.exists(path):
        os.mkdir(path)


class Generator:
    def __init__(self, loader_version: str, minecraft_version: str, lwjgl_version: str,
                 intermediary_type: IntermediaryType, path: str = "temp"):
        self.lwjgl_version: str = lwjgl_version
        self.minecraft_version: str = minecraft_version
        self.loader_version: str = loader_version
        self.intermediary_type: IntermediaryType = intermediary_type
        self.path: str = path

    def process(self, subject: str) -> str:
        subject = subject.replace("${loader_version}", self.loader_version)
        subject = subject.replace("${minecraft_version}", self.minecraft_version)
        subject = subject.replace("${lwjgl_version}", self.lwjgl_version)
        subject = subject.replace("${lwjgl_name}",
                                  "LWJGL 3" if self.lwjgl_version.startswith(
                                      "3") else "LWJGL 2")
        subject = subject.replace("${lwjgl_uid}",
                                  "org.lwjgl3" if self.lwjgl_version.startswith(
                                      "3") else "org.lwjgl")
        return subject

    def prepare_skeleton(self):
        mkdir_if_not_exists("temp")

        with open("skel/mmc-pack.json", "r") as f:
            with open("temp/mmc-pack.json", "w") as t:
                t.write(self.process(f.read()))

        with open("skel/instance.cfg", "r") as f:
            with open("temp/instance.cfg", "w") as t:
                t.write(self.process(f.read()))

        # ornithe naming convention
        if self.minecraft_version == "1.0":
            self.minecraft_version += ".0"
        if int(self.minecraft_version.split(".")[1]) < 3:
            self.minecraft_version += "-client"

        mkdir_if_not_exists("temp/patches")
        with open(f"skel/patches/{self.intermediary_type}", "r") as f:
            with open("temp/patches/net.fabricmc.intermediary.json", "w") as t:
                t.write(self.process(f.read()))

    def create_zip(self):
        with zipfile.ZipFile(
                f"out/{self.minecraft_version}+loader.{self.loader_version}+lwjgl.{self.lwjgl_version}.zip", "w") as z:
            z.write("temp/mmc-pack.json", "mmc-pack.json")
            z.write("temp/instance.cfg", "instance.cfg")
            z.write("temp/patches/net.fabricmc.intermediary.json",
                    "patches/net.fabricmc.intermediary.json")
            z.write("skel/legacyfabric.png", "legacyfabric.png")

        self.cleanup()

    def cleanup(self):
        for root, dirs, files in os.walk(self.path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for directory in dirs:
                os.rmdir(os.path.join(root, directory))

        os.rmdir(self.path)


versions = [
    ("1.13.2", "3.1.6", IntermediaryType.LegacyFabric),
    ("1.12.2", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.12", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabricV2),
    ("1.11.2", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.9.4", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.8.9", "2.9.4-nightly-20150209", IntermediaryType.LegacyFabric),
    ("1.8", "2.9.1", IntermediaryType.LegacyFabric),
    ("1.7.10", "2.9.1", IntermediaryType.LegacyFabric),
    ("1.7.4", "2.9.1-nightly-20131017", IntermediaryType.LegacyFabric),
    ("1.7.2", "2.9.0", IntermediaryType.LegacyFabric),
    ("1.6.4", "2.9.0", IntermediaryType.LegacyFabric),
    ("1.3.2", "2.9.0", IntermediaryType.LegacyFabric),
    ("1.0", "2.9.0", IntermediaryType.Ornithe)
]

print(f"target loader: {loader}")
mkdir_if_not_exists("out")
for version, lwjgl, intermediary in versions:
    print(f"generating {version} with LWJGL {lwjgl}...")
    g = Generator(loader, version, lwjgl, intermediary)
    g.prepare_skeleton()
    g.create_zip()
