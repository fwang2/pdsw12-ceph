paper:
	./mk paper
report:
	./mk report
all:
	./mk report
	./mk paper
clean:
	./mk -C paper
	./mk -C report
