SRC = $(wildcard src/*.cpp)
INPUT ?= $(wildcard inputs/*/*.x)

.PHONY: all verify clean

all: sim

CXXFLAGS = -std=c++17 -g -O2

sim: $(SRC)
	g++ $(CXXFLAGS) $^ -o $@

debug: CXXFLAGS += -DDEBUG
debug: sim

basesim: $(SRC)
	g++ -std=c++17 -g -O2 $^ -o $@

run: sim
	@python run.py $(INPUT)

clean:
	rm -rf *.o *~ sim sim.dSYM

