#!/bin/sh
logreopen=${VARPATH}/docket.logreopen
if [ ! -e "$logreopen" ]; then
  touch $logreopen
fi

/siq/env/python/bin/python /siq/env/python/bin/bake -m spire.tasks \
  spire.schema.deploy schema=docket config=/siq/svc/docket/docket.yaml
ln -sf ${SVCPATH}/docket/docket.yaml ${CONFPATH}/uwsgi/docket.yaml
