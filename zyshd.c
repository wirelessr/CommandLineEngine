#include <stdio.h>

int show_interface(int argc, char **argv)
{
	int i;

	fprintf(stderr, "%s ", __func__);
	for(i = 0; i < argc; i++)
	{
		fprintf(stderr, "%s ", argv[i]);
	}
	return 0;
}

int show_ap_vlan(int argc, char **argv)
{
	int i;

	fprintf(stderr, "%s ", __func__);
	for(i = 0; i < argc; i++)
	{
		fprintf(stderr, "%s ", argv[i]);
	}
	return 0;
}

int show_ap_info(int argc, char **argv)
{
	int i;

	fprintf(stderr, "%s ", __func__);
	for(i = 0; i < argc; i++)
	{
		fprintf(stderr, "%s ", argv[i]);
	}
	return 0;
}

int config_ap_mode(int argc, char **argv)
{
	int i;

	fprintf(stderr, "%s ", __func__);
	for(i = 0; i < argc; i++)
	{
		fprintf(stderr, "%s ", argv[i]);
	}
	return 0;
}

int config_interface(int argc, char **argv)
{
	int i;

	fprintf(stderr, "%s ", __func__);
	for(i = 0; i < argc; i++)
	{
		fprintf(stderr, "%s ", argv[i]);
	}
	return 0;
}

