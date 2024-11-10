# CLSEPA
Community Legal Services in East Palo Alto(CLSEPA) seeks to empower tenants to challenge landlords failing to maintain their legal obligations by analyzing historical public records to identity effective legal arguments based on past hearing orders

## Steps
### 1. Set up venv virtual environment
	python -m venv venv
	source venv/bin/activate
###	2. Install packages from requirements.txt
	pip install <package_name>
### 3. Set GOOGLE_API_KEY
	echo "export GOOGLE_API_KEY='your_actual_api_key_here'" >> ~/.zshrc
	source ~/.zshrc
### 4. Build database
	python src/main.py build
### 5. Find similar docs
	python main.py find path/to/query.pdf
	Or
	streamlit run src/app.py 
### 6. Deactivate the virtual environment
	deactivate