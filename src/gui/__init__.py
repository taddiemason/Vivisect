"""Native Kivy GUI for Vivisect.

A fully in-process desktop/touch frontend onto the shared VivisectEngine. Unlike
the web GUI under ``src/web``, this opens NO network listener and runs NO browser
or JS engine — it calls the forensics modules directly on a background thread pool
and marshals results back to the Kivy main thread.
"""
