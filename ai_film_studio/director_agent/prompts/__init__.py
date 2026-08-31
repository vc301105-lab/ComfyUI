"""Prompt templates loader for the director."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def read_prompt(name):
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as f:
        return f.read()
