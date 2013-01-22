#!/bin/sh
/siq/env/python/bin/python /siq/env/python/bin/bake -m spire.tasks \
  spire.schema.deploy schema=docket config=/siq/svc/appstack/appstack.yaml
