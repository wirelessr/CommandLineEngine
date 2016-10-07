#include <stdio.h>

#define FUNC_INSTANCE do {\
	int i; \
\
	fprintf(stderr, "%s ", __func__);\
	for(i = 0; i < argc; i++)\
	{\
		fprintf(stderr, "%s ", argv[i]);\
	}\
	return 0;\
} while(0)

int show_interface(int argc, char **argv)
{
	FUNC_INSTANCE;
}

int show_tunnel(int argc, char **argv)
{
	FUNC_INSTANCE;
}

int show_ap_vlan(int argc, char **argv)
{
	FUNC_INSTANCE;
}

int show_ap_info(int argc, char **argv)
{
	FUNC_INSTANCE;
}

int config_ap_mode(int argc, char **argv)
{
	FUNC_INSTANCE;
}

int config_interface(int argc, char **argv)
{
	FUNC_INSTANCE;
}

int config_profile(int argc, char **argv)
{
	FUNC_INSTANCE;
}

