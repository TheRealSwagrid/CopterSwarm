FROM python
ENV semantix_port=7500

COPY CopterSwarm.py.py /var
COPY requirements /var
COPY AbstractVirtualCapability.py /var
RUN apt-get update && apt-get install -y --no-install-recommends python-is-python3
#pkg-config libcairo2-dev gcc python3-dev libgirepository1.0-dev

RUN python -m pip install -r /var/requirements

CMD python /var/CopterSwarm.py ${semantix_port}