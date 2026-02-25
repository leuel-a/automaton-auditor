#!/usr/bin/env python3
import importlib
import os
import subprocess
import sys
from importlib.util import find_spec
from typing import Any

from colorama import Fore, Style, init
from langchain_core.language_models import BaseChatModel

_SUPPORTED_PROVIDERS = ["gemini", "ollama"]


class GenericLLMProvider:
    @classmethod
    def from_provider(cls, provider: str, **kwargs: Any) -> BaseChatModel:
        if provider == "gemini":
            _check_pkg("langchain_google_genai")
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=os.environ.get("LLM_PROVIDER_MODEL", "gemini-2.5-flash"),
                temperature=1.0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
            )
        elif provider == "ollama":
            _check_pkg("langchain_ollama")
            from langchain_ollama import ChatOllama

            llm = ChatOllama(model=os.environ.get("LLM_PROVIDER_MODEL", "gemini"), **kwargs)
        else:
            supported = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(
                f"Unsupported {provider}.\n\nSupported model providers are: {supported}"
            )
        return llm


def _check_pkg(pkg: str) -> None:
    if not find_spec(pkg):
        pkg_kebab = pkg.replace("_", "-")
        # Import colorama and initialize it
        init(autoreset=True)

        try:
            print(f"{Fore.YELLOW}Installing {pkg_kebab}...{Style.RESET_ALL}")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-U", pkg_kebab]
            )
            print(f"{Fore.GREEN}Successfully installed {pkg_kebab}{Style.RESET_ALL}")

            # Try importing again after install
            importlib.import_module(pkg)

        except subprocess.CalledProcessError:
            raise ImportError(
                Fore.RED
                + f"Failed to install {pkg_kebab}. Please install manually with "
                f"`pip install -U {pkg_kebab}`"
            )
