# Makefile for source rpm: shadow-utils
# $Id$
NAME := shadow-utils
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
