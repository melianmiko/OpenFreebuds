def start_ram_trace(ctx):
    try:
        from openfreebuds_qt.utils.ram_trace.ram_trace_service import OfbQtRamTraceService
        OfbQtRamTraceService(ctx).start()
    except ImportError:
        pass
