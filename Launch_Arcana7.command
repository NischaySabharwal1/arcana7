#!/bin/bash
# Move to the directory where this script is located
cd "$(dirname "$0")"

echo "------------------------------------------------"
echo "🔮 ARCANA7 - COST CALCULATOR"
echo "------------------------------------------------"
echo "Starting the engine... please wait."

# Check if uv is installed, if not use standard python
if command -v uv &> /dev/null
then
    uv run --with streamlit --with pandas --with plotly --with openpyxl --with fpdf2 streamlit run app.py
else
    echo "Using standard Python (uv not detected)..."
    pip install streamlit pandas plotly openpyxl fpdf2 --quiet
    python3 -m streamlit run app.py
fi
