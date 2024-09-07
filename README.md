Follow the instructions below to start the Flask server.

1. Setting up the Environment  <br>
   a. Create and Active a Virtual Environment with the command shown below for different operating systems. (Optional) <br>
   Windows: python -m venv venv <br>
   macOS/Linux: python3 -m venv venv

   b. Install Dependencies by running the following command shown below to install the required packages <br>
   pip install -r requirements.txt

2. Configuring Environment Variables
   Set the necessary environment variables with the following command shown below to run the Flask application. <br>
   Windows: <br>
   set FLASK_APP=app.py <br>
   set FLASK_ENV=development

   macOS/Linux: <br>
   export FLASK_APP=app.py <br>
   export FLASK_ENV=development

3. Running the Flask Application
   Once the environment is set up and the dependencies are installed, you can run the Flask application with the following command shown below. <br>
   flask run

4. Accessing the Application <br>
   By default, Flask runs on http://127.0.0.1:5000/. <br>
   Open your web browser and navigate to this URL to access the web application.

6. Stopping the Flask Server <br>
   To stop the Flask server, press Ctrl+C in the terminal where the server is running.

Troubleshooting Tips
1. Issue 'flask: command not found' <br>
   Solution: Ensure that the virtual environment is activated and Flask is installed. <br>
   You might need to add the virtual environment's Scripts (Windows) or bin (macOS/Linux) directory to your defined PATH.

2. Issue: Application not loading <br>
   Solution: Check if the FLASK_APP environment variable is correctly set to the entry point of your application (e.g., app.py). <br>
   Check that all dependencies are installed.

