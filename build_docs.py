#!/usr/bin/env python3
"""Run this script to regenerate docs.json from ~/ashby_docs/"""
import json
import os
import glob

DOCS_DIR = os.path.expanduser("~/ashby_docs")
OUT_FILE = os.path.join(os.path.dirname(__file__), "netlify/functions/docs.json")

docs = {}
for filepath in glob.glob(os.path.join(DOCS_DIR, "*.md")):
    slug = os.path.basename(filepath)[:-3]
    with open(filepath) as f:
        docs[slug] = f.read()

with open(OUT_FILE, "w") as f:
    json.dump(docs, f)

print(f"Built docs.json with {len(docs)} articles")
