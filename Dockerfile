# Will be based on
FROM didzis/visualsmatch

COPY bottle.py /vsmatch/

COPY smatch.py /vsmatch/
COPY amr.py /vsmatch/

COPY smatch_api.py /vsmatch/
COPY rules.py /vsmatch/
COPY server.py /vsmatch/

COPY static /vsmatch/static

CMD cd /vsmatch && ./server.py
