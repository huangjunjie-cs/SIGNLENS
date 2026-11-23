============
Installation
============

The Python package (Python >= 3.10)::

    $ pip install signlens                 # core library + CLI
    $ pip install "signlens[server]"       # + FastAPI web server
    $ pip install "signlens[plot]"         # + matplotlib figures in reports

From source, with the web app::

    $ git clone https://github.com/huangjunjie-cs/SIGNLENS && cd SIGNLENS
    $ pip install -e ".[server,dev]"
    $ (cd web && npm install && npm run build)
    $ signlens congress            # optional: build the 1789-today Congress series (~15 min)
    $ signlens serve               # http://127.0.0.1:8000

For frontend development run ``npm run dev`` in ``web/`` (proxies ``/api`` to port 8000).

The 2021 package name still works: ``from sign_lens import SignLens``.
