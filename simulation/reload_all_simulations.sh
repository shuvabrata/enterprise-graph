#!/bin/bash

# Script to reload all simulation data from scratch
# Layer 1 clears the entire database, then subsequent layers are loaded

set -e  # Exit on error

echo "Starting complete data reload..."
echo "================================"

cd "$(dirname "$0")"

echo -e "\n[1/8] Loading Layer 1: People & Teams (clears entire database)..."
cd layer1 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n[2/8] Loading Layer 2: Jira Initiatives..."
cd layer2 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n[3/8] Loading Layer 3: Jira Epics..."
cd layer3 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n[4/8] Loading Layer 4: Jira Stories & Bugs..."
cd layer4 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n[5/8] Loading Layer 5: Git Repositories..."
cd layer5 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n[6/8] Loading Layer 6: Git Branches..."
cd layer6 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n[7/8] Loading Layer 7: Git Commits & Files..."
cd layer7 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n[8/8] Loading Layer 8: Pull Requests..."
cd layer8 && python generate_data.py && python load_to_neo4j.py && cd ..

echo -e "\n================================"
echo "✓ All layers loaded successfully!"
echo "Open http://localhost:7474 to explore the data"
