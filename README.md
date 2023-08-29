# Electricity Rate Information Cooperation
## templates
In this folder, it contains the static html files for our website. This includes the html templates as well as the bootstrap framework additions.
- heat_map.html: This webpage acts as our homepage (or index page) for the website. On here, you can select options and click buttons to generate visualizations with our data.
- admin.html: The admin page is where we can add, update, or delete information. Essentially, there are 3 separate forms for each function.
- graph.html: This html page acts in the background as a transfer layer between the flask application and html. This helps turn the Python generated visualizations into JavaScript equivalent which can be displayed on the webpage. 

## app.py
app.py contains all of the flask application code. In here, we work through the database logic for reading from the database, as well as writing to the database for add, update, and delete. This flask file also contains the visualization generating part for the heat_map.html

## credentials.json 
credentials.json includes the credntials for our firebase database

## requirements.txt
requirements.txt is a support document for the flask application

## zip_lat_long.csv
zip_lat_long.csv includes and outside set of data from our database with the latitude and longitude data for US zipcodes. This was neccesary for visualizing the maps.

## Data
The data was published by the National Renewable Energy Laboratory and hosted on data.gov, where metadata is updated on a regular basis by Jay Huggins.  The purpose of this dataset is to provide anyone residing in the US with information on how exactly they are charged for electricity to make more informed decisions regarding their energy usage. (https://data.openei.org/submissions/5650)
