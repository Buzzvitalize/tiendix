from ecf.backends.direct_dgii import DirectDgiiBackend
from ecf.backends.pse_ecosea_stub import PseEcoseaStubBackend
from ecf.backends.pse_external import PseExternalBackend
from ecf.constants import DIRECT_DGII, PSE_ECOSEA, PSE_EXTERNAL


def get_backend(mode: str):
    backend_map = {
        DIRECT_DGII: DirectDgiiBackend,
        PSE_EXTERNAL: PseExternalBackend,
        PSE_ECOSEA: PseEcoseaStubBackend,
    }
    backend_cls = backend_map.get((mode or "").strip())
    if backend_cls is None:
        raise ValueError(f"Modo e-CF no soportado: {mode}")
    return backend_cls()


def assert_enabled(cfg) -> None:
    if cfg is None:
        raise ValueError("Configuración e-CF no encontrada para la compañía")
    if not bool(getattr(cfg, "enabled", False)):
        raise ValueError("Facturación electrónica no está habilitada para la compañía")
