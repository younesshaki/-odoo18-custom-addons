def migrate(cr, version):
    # Ownership is reassigned in cidmo_curtain so the legacy module can remain a no-op shim.
    return None
