LANGFILES := $(shell find locale/ -name "*.po")

.DEFAULT_GOAL := default
.PHONY: default
default: $(LANGFILES:.po=.mo)

locale/%/LC_MESSAGES/Companion4Linux.mo : locale/%/LC_MESSAGES/Companion4Linux.po
	msgfmt $< -o $@
