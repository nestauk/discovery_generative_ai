#!/bin/bash
python src/genai/eyfs/run_pinecone_index.py
python src/genai/dm/run_dm_index.py
python src/genai/parenting_chatbot/run_nhs_index_full_page.py
