#include <stdio.h>

int show_interface(int argc, char **argv)
{
	int i;

	printf("%s:%d %s\n", __FILE__, __LINE__, __func__);
	for(i = 0; i < argc; i++)
	{
		printf("argv[%d]=%s\n", i, argv[i]);
	}
	return 0;
}

int show_ap_vlan(int argc, char **argv)
{
	int i;

	printf("%s:%d %s\n", __FILE__, __LINE__, __func__);
	for(i = 0; i < argc; i++)
	{
		printf("argv[%d]=%s\n", i, argv[i]);
	}
	return 0;
}

int show_ap_info(int argc, char **argv)
{
	int i;

	printf("%s:%d %s\n", __FILE__, __LINE__, __func__);
	for(i = 0; i < argc; i++)
	{
		printf("argv[%d]=%s\n", i, argv[i]);
	}
	return 0;
}

