paper:
	./mk paper
report:
	./mk report
meta:
	./mk meta
all:
	./mk report
	./mk paper
clean:
	./mk -C paper
	./mk -C report
	./mk -C meta
