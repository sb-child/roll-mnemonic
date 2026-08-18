from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractAllSourcesOptions:
    tpm_random_server_endpoint: Optional[str]
