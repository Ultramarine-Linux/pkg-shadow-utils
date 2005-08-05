# Makefile for source rpm: shadow-utils
# $Id: Makefile,v 1.1 2004/09/09 12:21:12 cvsdist Exp $
NAME := shadow-utils
SPECFILE = $(firstword $(wildcard *.spec))

include ../common/Makefile.common
