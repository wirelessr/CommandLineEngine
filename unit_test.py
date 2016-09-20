#!/usr/bin/python3

import sys
import shlex, subprocess

def ASSERT_EQUAL(command_line, expect_result):
	command_line = "./zysh parse_cli cli_exec \"" + command_line + "\""
	args = shlex.split(command_line)

	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	outs, errs = proc.communicate()

	if errs.decode().strip() != expect_result:
		raise

def ASSERT_FALSE(command_line):
	command_line = "./zysh parse_cli cli_exec \"" + command_line + "\""
	args = shlex.split(command_line)

	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	outs, errs = proc.communicate()

	if proc.returncode == 0:
		raise

ASSERT_FALSE("show capwap ap in")
ASSERT_EQUAL("show capwap ap info", "show_ap_info zysh ap info")
ASSERT_EQUAL("show capwap ap vlan", "show_ap_vlan zysh ap vlan")
ASSERT_EQUAL("show interface all", "show_interface zysh all")
ASSERT_EQUAL("show capwap ap idx 2", "show_ap_info zysh ap idx 2")
ASSERT_FALSE("show capwap ap idx 5")
ASSERT_EQUAL("show capwap vlan 20", "show_ap_vlan zysh vlan 20")
ASSERT_FALSE("show capwap vlan 200")
ASSERT_EQUAL("show interface eth0", "show_interface zysh eth0")
ASSERT_EQUAL("show interface wlan0", "show_interface zysh wlan0")
ASSERT_FALSE("show interface eth1")

ASSERT_EQUAL("config hybrid-mode standalone", "config_ap_mode zysh standalone")
ASSERT_EQUAL("config hybrid-mode manage", "config_ap_mode zysh manage")
ASSERT_EQUAL("config hybrid-mode controller", "config_ap_mode zysh controller")
ASSERT_FALSE("config hybrid-mode ap")

ASSERT_EQUAL("config radio-mode wlan1", "config_ap_mode zysh wlan1")
ASSERT_EQUAL("config radio-mode wlan0 ap", "config_ap_mode zysh wlan0 ap")
ASSERT_EQUAL("config radio-mode wlan2 monitor", "config_ap_mode zysh wlan2 monitor")

ASSERT_EQUAL("config interface vlan vid 10", "config_interface zysh vlan vid 10")
ASSERT_EQUAL("config interface mgnt-vlan vid 10", "config_interface zysh mgnt-vlan vid 10")
ASSERT_EQUAL("config interface vlan port eth0", "config_interface zysh vlan port eth0")
ASSERT_EQUAL("config interface mgnt-vlan port eth1", "config_interface zysh mgnt-vlan port eth1")

ASSERT_FALSE("config interface vlan vid 1000")
ASSERT_FALSE("config interface mgnt-vlan vid 1000")
ASSERT_FALSE("config interface mgnt-vlan port 1000")
ASSERT_FALSE("config interface vlan port eth3")

ASSERT_FALSE("config interface vlan")
