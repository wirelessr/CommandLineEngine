CFLAGS=$(shell python3-config --cflags)
LDFLAGS=$(shell python3-config --ldflags)

PREP_SRC=cmd_func.c
SRCS=zysh.c zyshd.c

antlr4=java -Xmx500M -cp "/usr/local/lib/antlr-4.5-complete.jar:$CLASSPATH" org.antlr.v4.Tool
antlr4py3=$(antlr4) -Dlanguage=Python3

check: all
	@echo "Unit Test Start"
	@./unit_test.py || exit 1

all: prep
	@gcc -O0 -g $(CFLAGS) $(SRCS) $(PREP_SRC) -o zysh $(LDFLAGS)

prep:
	@rm -f $(PREP_SRC)
	@$(antlr4py3) -visitor Zysh.g4
	@python3 parse_cli.py

