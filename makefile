
#---collect extra arguments
RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)

#---print help
all:
	./controller

#---remake documenatation
docs: simuluxe sources/docs
	./controller make_docs ${RUN_ARGS} 

#---add a datapath to the local configuration file
addpath:
	./controller addpath ${RUN_ARGS}

#---add another configuration file
addconfig:
	./controller addconfig ${RUN_ARGS}
	
#---push to github (development)
gitpush:
	./controller gitpush ${RUN_ARGS}

#---push to github (development)
status:
	./controller status
