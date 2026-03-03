from ecf.backends.direct_dgii import DirectDgiiBackend
from ecf.backends.pse_ecosea_stub import PseEcoseaStubBackend
from ecf.backends.pse_external import PseExternalBackend


def get_backend(mode: str):
    backends = {
        "DIRECT_DGII": DirectDgiiBackend(),
        "PSE_EXTERNAL": PseExternalBackend(),
        "PSE_ECOSEA": PseEcoseaStubBackend(),
    }
    return backends.get(mode)
