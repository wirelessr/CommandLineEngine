#!/usr/bin/python3

import sys
import shlex, subprocess

pass_cnt = 0
fail_cnt = 0
test_id = 0
fail_record = []

def summary(pass_cnt, fail_cnt, fail_record):
	print()
	print("PASS:", pass_cnt)
	print("FAIL:", fail_cnt)
	for i, s in fail_record:
		print("[%d] %s"%(i, s))
	if fail_cnt > 0:
		sys.exit(1)

def fail(command_line, expect_result=None, real_result=None):
	global fail_cnt, test_id, fail_record
	fail_cnt += 1
	test_id += 1
	print("-", end="", flush=True)

	if expect_result is not None:
		fail_string = "command:"+command_line+", expect:"+expect_result+"\n  but real:"+real_result
	else:
		fail_string = "failed"
	fail_record.append((test_id, fail_string))

def success():
	global pass_cnt, test_id
	pass_cnt += 1
	test_id += 1
	print("+", end="", flush=True)

def gen_cmd(command_line):
	return "./zysh CookedHandler cli_exec \"" + command_line + "\""

def ASSERT_EQUAL(command_line, expect_result):
	command_input = command_line
	command_line = gen_cmd(command_line)
	args = shlex.split(command_line)

	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	outs, errs = proc.communicate()

	if errs.decode().strip() != expect_result:
		fail(command_input, expect_result, errs.decode().strip())
	else:
		success()

def ASSERT_EQUAL_LIST(command_line, expect_list_result):
	command_input = command_line
	command_line = gen_cmd(command_line)
	args = shlex.split(command_line)

	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	outs, errs = proc.communicate()

	real_list_result = errs.decode().split()
	for tok in expect_list_result.split():
		if tok not in real_list_result:
			fail(command_input, expect_list_result, errs.decode().strip())
			break
	else:
		success()

def ASSERT_FALSE(command_line):
	command_input = command_line
	command_line = gen_cmd(command_line)
	args = shlex.split(command_line)

	proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	outs, errs = proc.communicate()

	if proc.returncode == 0:
		fail(command_input, "False", "True")
	else:
		success()

ASSERT_FALSE("show capwap ap in")
ASSERT_EQUAL("show capwap ap info", "show_ap_info zysh ap info")
ASSERT_EQUAL("show capwap ap vlan", "show_ap_vlan zysh ap vlan")
ASSERT_EQUAL("show interface all", "show_interface zysh all")
ASSERT_EQUAL("show capwap ap idx 2", "show_ap_info zysh ap idx 2")
ASSERT_FALSE("show capwap ap idx 5")
ASSERT_EQUAL("show capwap vlan 20", "show_ap_vlan zysh vlan 20")
ASSERT_FALSE("show capwap vlan 200")
ASSERT_EQUAL("show capwap profile NAMEXX", "show_ap_info zysh profile NAMEXX")
ASSERT_EQUAL("show interface eth0", "show_interface zysh eth0")
ASSERT_EQUAL("show interface wlan0", "show_interface zysh wlan0")
ASSERT_FALSE("show interface eth10")
ASSERT_FALSE("show interface wlan10")
ASSERT_EQUAL("show interface wlan2", "show_interface zysh wlan2")

ASSERT_EQUAL("config hybrid-mode standalone", "config_ap_mode zysh standalone")
ASSERT_EQUAL("config hybrid-mode manage", "config_ap_mode zysh manage")
ASSERT_EQUAL("config hybrid-mode controller", "config_ap_mode zysh controller")
ASSERT_FALSE("config hybrid-mode ap")

ASSERT_EQUAL("config radio-mode wlan1", "config_ap_mode zysh wlan1")
ASSERT_EQUAL("config radio-mode wlan0 ap", "config_ap_mode zysh wlan0 ap")
ASSERT_EQUAL("config radio-mode wlan2 monitor", "config_ap_mode zysh wlan2 monitor")
ASSERT_EQUAL("config radio-mode wlan0 ap off", "config_ap_mode zysh wlan0 ap off")
ASSERT_EQUAL("config radio-mode wlan2 monitor off", "config_ap_mode zysh wlan2 monitor off")

ASSERT_EQUAL("config interface vlan vid 10", "config_interface zysh vlan vid 10")
ASSERT_EQUAL("config interface mgnt-vlan vid 10", "config_interface zysh mgnt-vlan vid 10")
ASSERT_EQUAL("config interface vlan port eth0", "config_interface zysh vlan port eth0")
ASSERT_EQUAL("config interface mgnt-vlan port eth1", "config_interface zysh mgnt-vlan port eth1")

ASSERT_FALSE("config interface vlan vid 1000")
ASSERT_FALSE("config interface mgnt-vlan vid 1000")
ASSERT_FALSE("config interface mgnt-vlan port 1000")
ASSERT_FALSE("config interface vlan port eth3")

ASSERT_FALSE("config interface vlan")

#ASSERT_EQUAL_LIST("?", "show config")
#ASSERT_EQUAL_LIST("show ?", "capwap interface")
#ASSERT_EQUAL_LIST("show capwap ?", "vlan ap profile")
#ASSERT_EQUAL_LIST("show capwap vlan ?", "<1..50>")

ASSERT_EQUAL("config interface eth0", "config_interface zysh eth0")
ASSERT_EQUAL("config interface eth1 idx 5", "config_interface zysh eth1 idx 5")
ASSERT_FALSE("config interface eth2 idx")
ASSERT_FALSE("config interface eth3")
ASSERT_FALSE("config interface eth1 idx 50")
ASSERT_FALSE("config interface eth1 fast path")
ASSERT_EQUAL("config interface eth0 fast path activate", "config_interface zysh eth0 fast path activate")

ASSERT_EQUAL("config profile NAMEXX", "config_profile zysh NAMEXX")
ASSERT_EQUAL("config profile NAMEXX idx 1", "config_profile zysh NAMEXX idx 1")
ASSERT_EQUAL("config profile NAMEXX num 10", "config_profile zysh NAMEXX num 10")
ASSERT_EQUAL("config profile NAMEXX idx 1 num 10", "config_profile zysh NAMEXX idx 1 num 10")
ASSERT_EQUAL("config profile NAMEXX value 100", "config_profile zysh NAMEXX value 100")
ASSERT_EQUAL("config profile NAMEXX idx 1 value 100", "config_profile zysh NAMEXX idx 1 value 100")
ASSERT_EQUAL("config profile NAMEXX idx 1 value 100 activate", "config_profile zysh NAMEXX idx 1 value 100 activate")
ASSERT_FALSE("config profile NAMEXX activate value 100")

ASSERT_EQUAL("config profile NAMESS nested setting", "config_profile zysh NAMESS nested setting")
ASSERT_EQUAL("config profile NAMESS nested setting level 1", "config_profile zysh NAMESS nested setting level 1")
ASSERT_EQUAL("config profile NAMESS nested setting level 1 5 inner", "config_profile zysh NAMESS nested setting level 1 5 inner")
ASSERT_EQUAL("config profile NAMESS nested setting level 1 5 inner end of all", "config_profile zysh NAMESS nested setting level 1 5 inner end of all")

summary(pass_cnt, fail_cnt, fail_record)
