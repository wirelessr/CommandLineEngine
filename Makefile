CFLAGS=$(shell python3-config --cflags)
LDFLAGS=$(shell python3-config --ldflags)

PREP_SRC=cmd_func.c
SRCS=zysh.c zyshd.c

check: all
	@./unit_test.py || exit 1

all: prep
	gcc -O0 -g $(CFLAGS) $(SRCS) $(PREP_SRC) -o zysh $(LDFLAGS)

prep:
	rm -f $(PREP_SRC)
	python3 parse_cli.py

