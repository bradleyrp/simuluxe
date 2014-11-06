
#---valid function names from the python script
TARGETS := $(shell perl -n -e '@parts = /^def\s+[a-z,_]+/g; $$\ = "\n"; print for @parts;' controller | awk '{print $$2}')

#---collect arguments
RUN_ARGS := $(wordlist 1,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)

#---hack to always run makefile interfaced with python
scripts=controller
$(shell touch $(scripts))
checkfile=.pipeline_up_to_date

$(checkfile): $(scripts)
	touch $(checkfile)
	./controller ${RUN_ARGS}

default: $(checkfile)
$(TARGETS): $(checkfile)
