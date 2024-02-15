LANGFILES := $(shell find locales/ -name "*.po")

.DEFAULT_GOAL := default
.PHONY: default
default: $(LANGFILES:.po=.mo)

locales/%/LC_MESSAGES/Companion4Linux.mo : locales/%/LC_MESSAGES/Companion4Linux.po
	msgfmt $< -o $@
