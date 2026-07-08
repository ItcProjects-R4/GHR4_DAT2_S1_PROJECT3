"Flight Analytics & Delay Insights System"

Project Idea:
"The primary objective of this project is to develop an Aviation Operational Intelligence System that transforms raw flight and meteorological data into actionable insights. By integrating historical flight records with weather datasets, the system aims to:
1.	Analyze Delay Root Causes: Identify whether flight delays are primarily driven by adverse weather conditions, airport congestion, or operational scheduling inefficiencies.
2.	Predictive Delay Analysis: Utilize advanced machine learning models (such as CatBoost) to predict the probability of flight delays, enabling proactive decision-making for airline operations.
3.	Enhance Decision Support: Provide an interactive Power BI dashboard that allows stakeholders to visualize operational bottlenecks and optimize flight turnarounds, ultimately improving overall service reliability and passenger satisfaction."
Project Objectives:
	Analyze Delay Root Causes: Identify the primary factors driving flight delays, such as adverse weather conditions, airport congestion, or operational scheduling inefficiencies.
	Predictive Delay Analysis: Utilize advanced machine learning models (such as CatBoost) to predict the probability of flight delays, enabling proactive decision-making for airline operations.
	Enhance Decision Support: Provide an interactive Power BI dashboard that allows stakeholders to visualize operational bottlenecks and optimize flight turnarounds, ultimately improving overall service reliability and passenger satisfaction.
Technologies Used:
	Programming Language: Python was the primary language used throughout the project.
	Development Environment: Jupyter Notebooks (.ipynb) were utilized for data exploration, cleaning, and analysis workflows.
	Data Analysis & Processing: Pandas and NumPy libraries were employed for data manipulation, cleaning, and handling outliers.
	Data Storage: Data was processed and stored in CSV format, including both raw datasets and cleaned versions (e.g., aviationstack_flights_cleaned.csv, Weather_Clean_2026_Ready.csv).
	GUI Development: A graphical user interface was developed using Python to interact with the project data, as indicated by the presence of the GUI.py file.

Key Project Features:
	Comprehensive Data Pipeline: The project implements a complete data workflow, including raw data collection, automated cleaning processes, and structural refinement to ensure data quality. 
	Aviation Data Analytics: Built-in capabilities to handle and analyze aviation and flight data, allowing for efficient exploration of flight-related metrics. 
	Meteorological Data Processing: Includes specialized scripts for processing weather datasets, which involves identifying and handling outliers to maintain dataset integrity. 
	Interactive User Interface: Features a dedicated Graphical User Interface (GUI) developed in Python, providing a user-friendly way to interact with the project’s functionalities. 
	Scalable Codebase: The project is modularized into distinct directories (Analysis, Airports, Aviation, Weather), making it easy to maintain, scale, and integrate new features in the future.

How to Run the Project:
Follow these steps to set up and run the project environment:
1. Prerequisites:
Ensure you have Python 3.x installed on your machine. You will also need to install the required libraries: pip install pandas numpy requests jupyter.
2. Project Structure:
The project is organized into modular directories. Make sure your local environment mirrors the following structure:
•	/Airports: Contains notebooks for airport data cleaning.
•	/Aviation: Contains code for API data collection and flight data cleaning.
•	/Weather: Contains code for weather data processing and outlier detection.
•	/Analysis: Contains the main analytics engine.
3.Execution Steps:
To reproduce the results or run the analytics, follow the pipeline in this order:
1.	Data Preparation (Aviation):
o	Open Aviation/code for creating datase/Aviation_API.ipynb to fetch/prepare the flight data.
o	Run Aviation/code for cleaning data/Aviation_cleaning_(1).ipynb and (2).ipynb to clean the flight records.
2.	Data Preparation (Weather & Airports):
o	Run Airports/Airports_cleaned_.ipynb to process the airport dimensions.
o	Run Weather/code for clean data/weather_clean_.ipynb and Weather/code for Creating dataset/Weather_column_.ipynb to align weather data.
3.	Outlier Analysis:
o	Execute Weather/Code for exploring outliers/Explore_outliers_in_weather_column.ipynb to verify data integrity.
4.	Running the Analytics Engine:
o	Finally, run the notebooks in the /Analysis folder to execute the analytics engine, which generates the aviation_analytics_output.xlsx report.
4. User Interface:
If you wish to use the graphical interface, run the following command in your terminal: python GUI.py




Project File Structure:
The project is organized into modular directories, each serving a specific purpose in the Data Science lifecycle:
•	/Aviation: Contains code for data extraction (API) and flight data cleaning processes.
•	/Weather: Includes scripts for weather dataset alignment and outlier detection to ensure data integrity.
•	/Airports: Contains notebooks for airport dimension processing and filtering.
•	/Analysis: Houses the main analytics engine that generates performance reports and trends.
•	/Cleaned Data: The final destination for all processed and ready-to-use CSV files.
•	GUI.py: The main interface file for user interaction and predictive modeling.
Challenges Faced:
	Data Alignment & Time-Shift: One of the main challenges was aligning flight schedules with meteorological data. Since the flight dataset and the weather dataset had different timeframes, I had to implement a time-shift alignment algorithm to ensure each flight record corresponded accurately to the weather conditions on that specific date.
	Handling Missing & Noisy Data: The raw data contained significant gaps (missing arrival/departure delays) and outliers. I addressed this by using Winsorization (capping at 5th and 95th percentiles) and Yeo-Johnson transformations to normalize the data distributions.
	Feature Engineering: Creating meaningful features such as Flight_Efficiency and the weather_key (for data merging) was essential for achieving model accuracy. Ensuring the weather_key was unique across all datasets was a critical step for consistent data joins.
	GUI & Data Preprocessing Compatibility: A major hurdle was ensuring that the data entered by the user in the GUI is pre-processed exactly like the training data. I overcame this by integrating the trained OrdinalEncoder directly into the prediction pipeline to avoid ValueError issues during inference.
	Environmental Constraints: Managing the transition between local development and collaborative environments (Google Colab/Local) required handling file paths dynamically to prevent FileNotFoundError and ensure smooth execution.









  
