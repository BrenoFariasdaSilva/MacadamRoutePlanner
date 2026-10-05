# Macadam project interface. Application arguments travel through environment variables.
.DEFAULT_GOAL := help
STEPS =
MINIMUM =
DEBUG = 0
USER_IMAGE =
GIRLFRIEND_IMAGE =
IMAGE =
COINS =
ARGS =
export MACADAM_STEPS := $(STEPS)
export MACADAM_MINIMUM := $(MINIMUM)
export MACADAM_DEBUG := $(DEBUG)
export MACADAM_USER_IMAGE := $(USER_IMAGE)
export MACADAM_GIRLFRIEND_IMAGE := $(GIRLFRIEND_IMAGE)
export MACADAM_IMAGE := $(IMAGE)
export MACADAM_COINS := $(COINS)
export MACADAM_ARGS := $(ARGS)
ifeq ($(OS),Windows_NT)
SHELL := powershell.exe
.SHELLFLAGS := -NoProfile -Command
PYTHON_CMD ?= python
EXECUTE := &
FINISH := ; exit $$LASTEXITCODE
else
PYTHON_CMD ?= python3
EXECUTE :=
FINISH :=
endif

help setup install run run-couple run-single compile validate clean dependencies generate_requirements:
	@$(EXECUTE) "$(PYTHON_CMD)" project_tasks.py $@ $(FINISH)

all: help
.PHONY: all help setup install run run-couple run-single compile validate clean dependencies generate_requirements
