from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BrewPackage(BaseModel):
    name: str
    version: str
    package_type: str = Field(alias="type", default="formula")

    model_config = {"populate_by_name": True}


class PipPackage(BaseModel):
    name: str
    version: str


class NpmPackage(BaseModel):
    name: str
    version: str
    global_: bool = Field(alias="global", default=True)

    model_config = {"populate_by_name": True}


class EnvVar(BaseModel):
    key: str
    value: str
    config_file: str = ".zshrc"


class Dotfile(BaseModel):
    path: str
    content: str
    sensitive: bool = False
    encrypted: bool = False


class VscodeConfig(BaseModel):
    extensions: list[str] = Field(default_factory=list)
    settings_path: Optional[str] = None
    settings_content: Optional[str] = None


class Manifest(BaseModel):
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    hostname: str = ""
    platform: str = ""
    arch: str = ""
    packages: dict[str, list[BrewPackage | PipPackage | NpmPackage]] = Field(default_factory=dict)
    env_vars: list[EnvVar] = Field(default_factory=list)
    dotfiles: list[Dotfile] = Field(default_factory=list)
    ide: dict[str, VscodeConfig] = Field(default_factory=dict)
