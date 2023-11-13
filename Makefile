#makefile for VoiceChat

install:
	@echo "Installing env"
	
	python -m venv .venv && \
	source .venv/bin/activate && \
	pip install poetry==1.6.1 && \
	poetry install

