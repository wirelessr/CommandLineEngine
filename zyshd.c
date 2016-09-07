#include <stdio.h>

int show_interface(int argc, char **argv)
{
	printf("%s:%d %s\n", __FILE__, __LINE__, __func__);
	return 0;
}

int show_ap_vlan(int argc, char **argv)
{
	printf("%s:%d %s\n", __FILE__, __LINE__, __func__);
	return 0;
}

int show_ap_info(int argc, char **argv)
{
	printf("%s:%d %s\n", __FILE__, __LINE__, __func__);
	return 0;
}

