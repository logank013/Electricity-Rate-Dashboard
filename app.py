#This file will take in the form values from the admin page and decode them accordingly.

from flask import Flask, render_template, request
import firebase_admin
from firebase_admin import db, credentials
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import json
import plotly

app = Flask(__name__)

#This is the configuration we need to link up to the firebase database.
firebaseConfig = {
    'apiKey': "AIzaSyBne0nOWNTsRrhaXipwPZcl9W2cHK51RWc",
    'authDomain': "dashboard-iu.firebaseapp.com",
    'databaseURL': "https://dashboard-iu-default-rtdb.firebaseio.com/",
    'projectId': "dashboard-iu",
    'storageBucket': "dashboard-iu.appspot.com",
    'messagingSenderId': "37810784747",
    'appId': "1:37810784747:web:ea8344fa7702e5a52af1ae",
    'measurementId': "G-FGMYRGJSGB"
}

#Then we also need to link up to the credentials.json file that gives us permission to connect to the database.
cred = credentials.Certificate("credentials.json")
#We might not even need this default.app thing, not 100% sure
default_app = firebase_admin.initialize_app(cred,firebaseConfig)

########################################################################
#            CODE TO GET DATA FROM FIREBASE                            #
########################################################################

#Here's where we .get() each of the tables from firebase into this python file.
ref_main = db.reference("/main_table")
ref_zip = db.reference("/zipcode_table")
ref_s_rate = db.reference("/service_rate_table")
ref_utility = db.reference("/utility_table")

def no_sql_to_dataframe(table):
    data = table.get()
    data_no_nulls = []
    for val in data:
        if val != None :
            data_no_nulls.append(val)
    df = pd.DataFrame.from_dict(data_no_nulls)
    return df

main_df = no_sql_to_dataframe(ref_main)
zip_df = no_sql_to_dataframe(ref_zip)
s_rate_df = no_sql_to_dataframe(ref_s_rate)
utility_df = no_sql_to_dataframe(ref_utility)

def refresh_data():
    print('retrieving fresh data...')
    # retrieve data from firebase tables
    ref_main = db.reference("/main_table")
    ref_zip = db.reference("/zipcode_table")
    ref_s_rate = db.reference("/service_rate_table")
    ref_utility = db.reference("/utility_table")
    print('making dataframes...')
    # store data as dataframes
    main_df = no_sql_to_dataframe(ref_main)
    zip_df = no_sql_to_dataframe(ref_zip)
    s_rate_df = no_sql_to_dataframe(ref_s_rate)
    utility_df = no_sql_to_dataframe(ref_utility)
    print('merging coordinates...')
    # update zip table with lat/long coordinates
    zll_df = pd.read_csv('zip_lat_long.csv')
    zll_df = zll_df.rename(columns={"ZIP": "zip", "LAT": "lat", "LNG": "long"})
    zll_df['zip'] = zll_df['zip'].astype(str).str.zfill(5)
    zip_df=zip_df.merge(zll_df, how='left', on='zip')
    #zip_df=zip_df.dropna()
    # join tables/dataframes on primary keys
    print('joining tables...')
    primary_df = main_df.merge(zip_df, how='left', on='zipid')
    s_rate_util_df = s_rate_df.merge(utility_df, how='left', on='eiaid')
    primary_df = primary_df.merge(s_rate_util_df, how='left', on='serviceid')
    return primary_df

def refresh_data_map():
    print('retrieving fresh data...')
    # retrieve data from firebase tables
    ref_main = db.reference("/main_table")
    ref_zip = db.reference("/zipcode_table")
    ref_s_rate = db.reference("/service_rate_table")
    ref_utility = db.reference("/utility_table")
    print('making dataframes...')
    # store data as dataframes
    main_df = no_sql_to_dataframe(ref_main)
    zip_df = no_sql_to_dataframe(ref_zip)
    s_rate_df = no_sql_to_dataframe(ref_s_rate)
    utility_df = no_sql_to_dataframe(ref_utility)
    print('merging coordinates...')
    # update zip table with lat/long coordinates
    zll_df = pd.read_csv('zip_lat_long.csv')
    zll_df = zll_df.rename(columns={"ZIP": "zip", "LAT": "lat", "LNG": "long"})
    zll_df['zip'] = zll_df['zip'].astype(str).str.zfill(5)
    zip_df=zip_df.merge(zll_df, how='left', on='zip')
    zip_df=zip_df.dropna()
    # join tables/dataframes on primary keys
    print('joining tables...')
    primary_df = main_df.merge(zip_df, how='left', on='zipid')
    s_rate_util_df = s_rate_df.merge(utility_df, how='left', on='eiaid')
    primary_df = primary_df.merge(s_rate_util_df, how='left', on='serviceid')
    return primary_df
 
########################################################################
#          END CODE TO GET DATA FROM FIREBASE                         #
########################################################################

########################################################################
#           TEMP CODE FOR GENERATING TABLES                            #
########################################################################
'''
def refresh_data(): ################ THIS DOES NOT PULL CODE FROM FIREBASE TABLES
    zll_df = pd.read_csv('zip_lat_long.csv')
    non_iou_zipcode_df = pd.read_csv('non_iou_zipcodes_2020.csv')
    iou_zipcode_df = pd.read_csv('iou_zipcodes_2020.csv')
    
    zll_df = zll_df.rename(columns={"ZIP": "zip", "LAT": "lat", "LNG": "long"})
    zll_df['zip'] = zll_df['zip'].astype(str).str.zfill(5)

    primary_df = pd.concat([iou_zipcode_df,non_iou_zipcode_df])
    primary_df['zip'] = primary_df['zip'].astype(str).str.zfill(5)
    primary_df = primary_df.reset_index(drop=True)
    primary_df = primary_df.reset_index()
    primary_df = primary_df.rename(columns={'index':'id'})

    #primary_df['lat'] = primary_df['zip'].map(zll_df.set_index('zip')['lat'])
    #primary_df['long'] = primary_df['zip'].map(zll_df.set_index('zip')['long'])
    print('joining tables...')
    primary_df = primary_df.merge(zll_df, how='left', on='zip')
    return primary_df
'''
########################################################################
#           END TEMP CODE FOR GENERATING TABLES                        #
########################################################################
 
 #########################################################
 #               HEAT MAP CODE                           #
 #########################################################

def graph_heat_map(ric, ownership, service_type):

    #Store fresh tabular data in primary_df
    primary_df=refresh_data_map()
    print(primary_df.head())
    # Intialize output DF
    df= pd.DataFrame(columns = ['lat', 'long', 'rate'])

    
    # Assign rate type from parameter
    if(ric=='r'):
        rate_type='res_rate'
    elif(ric=='i'):
        rate_type='ind_rate'
    elif(ric=='c'):
        rate_type='comm_rate'
    else:
        print("Rate input error")

    # Go through rows and extract relavant data
    print("gathering data...")
    # Build output DF #
    for i in range(len(primary_df)):
        if ((ownership == 'All' or (primary_df['ownership'][i]==ownership)) and 
            (service_type == "All" or (primary_df['service_type'][i]==service_type))):
            rate = primary_df[rate_type][i]
            if float(rate) > 0: # only collect non-zero data
                lat = primary_df['lat'][i]
                long = primary_df['long'][i]
                # append the data to df which is the dataframe used for the graph.
                df.loc[i]=[lat, long, rate]
        if (i % 10000 == 0): print(f'Processed {i} rows...')

    print("rendering map...")

    # Graph output DF
    fig = px.scatter_mapbox(df, lat = 'lat', lon = 'long', color = 'rate',
                                size='rate',
                                center = dict(lat = 37.0902, lon = -95.7129),
                                zoom = 3,
                                mapbox_style = 'open-street-map',
                                height = 800)
    # Create graphJSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
     
    # Use render_template to pass graphJSON to html
    return render_template('graph.html', graphJSON=graphJSON)
    
 #########################################################
 #                 BAR CHART CODE                        #
 #########################################################

def return_rate_list(rate_type,df):
  init_list=(df[rate_type])
  nonzero_list=[i for i in init_list if i != 0]
  rates=pd.Series(nonzero_list)
  min_rate=rates.describe()[3]
  first_qt = rates.describe()[4]
  second_qt = rates.describe()[5]
  third_qt = rates.describe()[6]
  max_rate = rates.describe()[7]
  rate_list = [min_rate, first_qt, second_qt, third_qt, max_rate]
  return rate_list

def rate_chart():
    df=refresh_data()

    # set height of bar
    RES = return_rate_list('res_rate',df)
    COMM = return_rate_list('comm_rate',df)
    IND = return_rate_list('ind_rate',df)

    quantiles=['Min', '1st ', '2nd', '3rd', 'Max']

    fig = go.Figure(data=[
        go.Bar(name='Residential', x=quantiles, y=RES),
        go.Bar(name='Commercial', x=quantiles, y=COMM),
        go.Bar(name='Industrial', x=quantiles, y=IND)
    ])
    # Change the bar mode
    fig.update_layout(barmode='group', title_text='Quantile Data for Residential, Commercial, and Industrial Rates',title_x=0.5, height=800)
    # Create graphJSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
     
    # Use render_template to pass graphJSON to html
    return render_template('graph.html', graphJSON=graphJSON)
    

 #########################################################
 #                 PIE CHART CODE                        #
 #########################################################
def pie_chart(col):
    pie_chart_data, labels = return_pie_chart_data(col)


    if col=='ownership': 
        chart_title = 'Ownership Type'
    else: 
        chart_title = 'Service Type'
    fig = go.Figure(data=[go.Pie(labels=labels, values=pie_chart_data, textinfo='label+percent',
                             insidetextorientation='radial')])
    
    fig.update_layout(height=800)
     
    # Create graphJSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
     
    # Use render_template to pass graphJSON to html
    return render_template('graph.html', graphJSON=graphJSON)

def return_pie_chart_data(col):
    df=refresh_data() 
    pie_data = pd.Series(df[col])
    return_list=[]
    total_records = len(pie_data)

    if col=='ownership':
        labels = ['Investor Owned','Cooperative','Federal','Municipal','State']
        for i in labels: 
          return_list.append(df[col].value_counts()[i])
        return_list.append(total_records-sum(return_list))   
        labels.append('Other')
    elif col=='service_type':
        labels = ['Bundled', 'Delivery']
        for i in labels: 
          return_list.append(df[col].value_counts()[i])
        return_list.append(total_records-sum(return_list))   
        labels.append('Other')
    else: print('return_pie_chart error') 

    ########## append label list to include percentage ##############  
    '''
    for i in range(len(return_list)):
      labels[i] = labels[i] + " " + str(round(return_list[i]/total_records*100,1)) + "%" 
    print()
    '''
    return return_list, labels

#######################################################################
#                          TABLE CODE                                 #       
#######################################################################

def show_table(n, col, sort_by):
  primary_df = refresh_data()

  n = int(n)
  if n > len(primary_df): n=len(primary_df)

  df=primary_df.sort_values(by=col)

  df= df[df[col] != 0]

  if sort_by == 'asc':
    df = df.nsmallest(n, col, keep='last')
  elif sort_by == 'desc':
    df = df.nlargest(n, col, keep='last')
  else:
    print("show_table error")

  if col == 'res_rate':
    col = df.res_rate
    header_list = ['Zip Code', 'State', 'Utility Name', 'Residential Rate']
    cell_list = [df.zip, df.state, df.utility_name, df.res_rate]
  elif col == 'comm_rate':
    col = df.comm_rate
    header_list = ['Zip Code', 'State', 'Utility Name', 'Commercial Rate']
    cell_list = [df.zip, df.state, df.utility_name, df.comm_rate]
  elif col == 'ind_rate':
    col = df.ind_rate
    header_list = ['Zip Code', 'State', 'Utility Name', 'Industrial Rate']
    cell_list = [df.zip, df.state, df.utility_name, df.ind_rate]

  fig = go.Figure(data=[go.Table(
    header=dict(values=header_list, fill_color='paleturquoise', align='left'),
    cells=dict(values=cell_list, fill_color='lavender', align='left'))
  ])

  fig.update_layout(height=800)

  # Create graphJSON
  graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
  # Use render_template to pass graphJSON to html
  return render_template('graph.html', graphJSON=graphJSON)


##########################################################################################
#                                FLASK STUFF BELOW                                       #
##########################################################################################

#Next, we'll create Flask endpoints.  Endpoints are objects that can be queried to retrieve something from the (package?/pickle?).

@app.route('/')
def heat_map():
    #"render_template" is used to render files.  In our case, this will render our html files.
    return render_template("heat_map.html")

@app.route("/map", methods=['GET','POST'])
def generate_map():
    rate_type = request.form.get('rate_type')
    ownership = request.form.get('owner')
    service_type = request.form.get('service_type') 
    print(f"Rate type is {rate_type}, service type is {service_type}, and ownership type is {ownership}. ")
    chart = graph_heat_map(rate_type, ownership, service_type)
    return chart

@app.route("/table", methods=['GET','POST'])
def generate_table():
    table_rate_type = request.form.get('table_rate_type')
    num = request.form.get('num')
    sort_by = request.form.get('sort_by') 
    print(f"show_table is passed {num}, {table_rate_type}, and {sort_by}")
    chart = show_table(num, table_rate_type, sort_by)
    return chart

@app.route("/pct_pie_chart", methods=['GET','POST'])
def generate_pie_chart():
    col = request.form.get('pie_column_id')
    chart = pie_chart(col)
    return chart

@app.route("/rate_bar_chart", methods=['GET','POST'])
def rate_bar_chart():
    print("Generating Rate Chart...")
    chart = rate_chart()
    return chart


#************************************************************************************
#************************************************************************************
#************************************************************************************
#  Now that we've created the functions necessary to process the user's input, we can
#  actually look at the user's input and run the process.
#************************************************************************************
#************************************************************************************
#************************************************************************************

#Next, we'll create Flask endpoints.  Endpoints are objects that can be queried to retrieve something from the (package?/pickle?).

@app.route('/fake_home')
def home():
    #"render_template" is used to render files.  In our case, this will render our html files.
    return render_template("index.html")

#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************

@app.route('/admin.html')
def admin():
    #"render_template" is used to render files.  In our case, this will render our html files.
    return render_template("admin.html")

#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************

#"add_form_decoder" is used to receive values that have been returned from the admin.html form.
@app.route("/add_form_decoder",methods=['GET','POST'])
def add_form_decoder():

    ref_main = db.reference("/main_table")
    ref_zip = db.reference("/zipcode_table")
    ref_s_rate = db.reference("/service_rate_table")
    ref_utility = db.reference("/utility_table")

    def no_sql_to_dataframe(table):
        data = table.get()
        data_no_nulls = []
        for val in data:
            if val != None :
                data_no_nulls.append(val)
        df = pd.DataFrame.from_dict(data_no_nulls)
        return df

    main_df = no_sql_to_dataframe(ref_main)
    zip_df = no_sql_to_dataframe(ref_zip)
    s_rate_df = no_sql_to_dataframe(ref_s_rate)
    utility_df = no_sql_to_dataframe(ref_utility)

    #And here, we establish the max id for each table:
    max_id_value = max(main_df['id'])
    max_zipid_value = max(zip_df['zipid'])
    max_serviceid_value = max(s_rate_df['serviceid'])
    max_eiaid_value = max(s_rate_df['eiaid'])

    def zip_table_checker(zip_code,state):
        #We start by assuming the values are not in the table.  This is indicated by using the value "".
        zip_match = ""
        state_match = ""
        id_match = ""
        
        for i in range(len(zip_df)):
            if (zip_df['zip'][i] == zip_code) and (zip_df['state'][i] == state):
                zip_match = zip_df['zip'][i]
                state_match = zip_df['state'][i]
                id_match = zip_df['zipid'][i]
                break
            #elif (zip_df['zip'][i] == zip_code) and (zip_df['state'][i] != state):
            #    zip_match = "missing state"
            #elif (zip_df['zip'][i] != zip_code) and (zip_df['state'][i] == state):
            #    state_match = "missing zip"
            else:
                pass
            
        return id_match,zip_match,state_match

    def utility_table_checker(utility_name,ownership):
        #We start by assuming the values are not in the table.  This is indicated by using the value "".
        utility_match = ""
        ownership_match = ""
        id_match = ""
        
        for i in range(len(utility_df)):
            if (utility_df['utility_name'][i] == utility_name) and (utility_df['ownership'][i] == ownership):
                utility_match = utility_df['utility_name'][i]
                ownership_match = utility_df['ownership'][i]
                id_match = utility_df['eiaid'][i]
                break
            else:
                pass
            
        return id_match,utility_match,ownership_match

    def s_rate_table_checker(service_type,comm_rate,res_rate,ind_rate,eiaid):
        #We start by assuming the values are not in the table.  This is indicated by using the value "".
        service_type_match = ""
        comm_rate_match = ""
        res_rate_match = ""
        ind_rate_match = ""
        eiaid_match = ""
        id_match = ""
        
        for i in range(len(s_rate_df)):
            if ((s_rate_df['service_type'][i] == service_type) 
                and (s_rate_df['comm_rate'][i] == comm_rate) 
                and (s_rate_df['res_rate'][i] == res_rate)
                and (s_rate_df['ind_rate'][i] == ind_rate)
                and (s_rate_df['eiaid'][i] == eiaid)
            ):
                service_type_match = s_rate_df['service_type'][i]
                comm_rate_match = s_rate_df['comm_rate'][i]
                res_rate_match = s_rate_df['res_rate'][i]
                ind_rate_match = s_rate_df['ind_rate'][i]
                eiaid_match = s_rate_df['eiaid'][i]
                id_match = s_rate_df['serviceid'][i]
                break
            else:
                pass
            
        return id_match,service_type_match,comm_rate_match,res_rate_match,ind_rate_match,eiaid_match

    def main_table_checker(zipid,serviceid):
        zipid_match = ""
        serviceid = ""
        id_match = ""
        
        for i in range(len(main_df)):
            if ((main_df['zipid'][i] == zipid) and
                (main_df['serviceid'][i] == serviceid)):
                zipid_match = main_df['zipid'][i]
                serviceid = main_df['serviceid'][i]
                id_match = main_df['id'][i]
                break
            else:
                pass
            
        return id_match,zipid_match,serviceid

    print("\nRequest Form: ",request.form.values(),'\n')
    transformed_vals = [x for x in request.form.values()] #this converts the string values retrived via request.form.values() from model.py into float values.
    print("\nTransformed Vals: ",transformed_vals,'\n')

    zip_code = ''
    if transformed_vals[0] == ' ':
        zip_code = ''
    elif transformed_vals[0].isdigit() == True:
        zip_code = transformed_vals[0]
    else:
        zip_code = ''

    state = ''
    if (len(transformed_vals[1]) == 2) and (transformed_vals[1].isalpha() == True):
        state = transformed_vals[1]
    else:
        state = ''

    utility_name = transformed_vals[2]
    service_type = transformed_vals[3]
    ownership = transformed_vals[4]
    comm_rate = float(transformed_vals[5])
    res_rate = float(transformed_vals[6])
    ind_rate = float(transformed_vals[7])

    if((zip_code=='')or(state=='')or(utility_name=='')or(service_type=='')or(ownership=='')or(comm_rate=='')or(res_rate=='')or(ind_rate=='')):
        message = "Not all values were entered.  Please enter full values."
        cleaned_admin_form = message
    else:

        #Here is where we then check the values entered by the user to see if those values exist already in our tables.
        zip_query_results = zip_table_checker(zip_code,state)
        print('Zip Query Ran')
        utility_query_results = utility_table_checker(utility_name,ownership)
        print('Utility Query Ran')
        service_rate_query_results = s_rate_table_checker(service_type,comm_rate,res_rate,ind_rate,utility_query_results[0])
        print('Service Rate Query Ran')
        main_query_results = main_table_checker(zip_query_results[0],service_rate_query_results[0])
        print('Main Query Ran')


        #Here, we determine if the queries found a matching Key ID.
        #If there is NOT a matching ID, then we return the highest value Key ID +1 and set a new key-value pair 
        # at the end of the database.  Otherwise, if the ID matches, then we do nothing.
        if zip_query_results[0] == '':
            #then add the zipcode and state to the zip table
            max_zipid_value += 1
            zip_str = str(max_zipid_value)
            db.reference("/zipcode_table").child(zip_str).set({
                'zip':zip_code,
                'state':state,
                'zipid':max_zipid_value
                })
        else:
            pass

        #Same thing we did to the zipcode_table is what we're gonna do to the utility_table.
        if utility_query_results[0] == '':
            #then add the utility_name and ownership to the utility table
            max_eiaid_value += 1
            eiaid_str = str(max_eiaid_value)
            db.reference("/utility_table").child(eiaid_str).set({
                'eiaid':max_eiaid_value,
                'ownership':ownership,
                'utility_name':utility_name
                })
        else:
            pass

        #This is where things get different.
        # If there WAS a utility_name match BUT the other values of the service_rate_table did NOT match,
        # then add all the service_rate_table-related values input by the user AND the utility_table's EIAID.
        # ELSE IF both the service_rate_table and utility_table-related values have no matches, then add all related
        # values input by the user.
        # Otherwise, skip this.
        print(utility_query_results[0])
        if ((service_rate_query_results[0] == '') and (utility_query_results[0] == '')):
            max_serviceid_value += 1
            sid_str = str(max_serviceid_value)
            db.reference("/service_rate_table").child(sid_str).set({
                'comm_rate':comm_rate,
                'eiaid':max_eiaid_value,
                'ind_rate':ind_rate,
                'res_rate':res_rate,
                'service_type':service_type,
                'serviceid':max_serviceid_value
            })
        elif (service_rate_query_results[0] == ''):
            #then add the service_rate, comm_rate, res_rate, ind_rate, and eiaid to the service_rate table
            max_serviceid_value += 1
            sid_str = str(max_serviceid_value)
            db.reference("/service_rate_table").child(sid_str).set({
                'comm_rate':comm_rate,
                'eiaid':int(utility_query_results[0]),
                'ind_rate':ind_rate,
                'res_rate':res_rate,
                'service_type':service_type,
                'serviceid':max_serviceid_value
            })
        else:
            pass

        #This will be the same deal as service_rate_table, except that we are checking if either the zip_table OR the
        # service_rate_table returned matches.
        max_id_value += 1
        id_str = str(max_id_value)
        if ((zip_query_results[0] == '') and (service_rate_query_results[0] != '')):
            print("0")
            print(service_rate_query_results[0])
            db.reference("/main_table").child(id_str).set({
                'id':max_id_value,
                'serviceid':int(service_rate_query_results[0]),
                'zipid':max_zipid_value
                })
        elif ((zip_query_results[0] != '') and (service_rate_query_results[0] == '')):
            print("1")
            print(zip_query_results[0])
            db.reference("/main_table").child(id_str).set({
                'id':max_id_value,
                'serviceid':max_serviceid_value,
                'zipid':int(zip_query_results[0])
                })
        elif ((zip_query_results[0] == '') and (service_rate_query_results[0] == '')):
            #then add the zipid and serviceid to the main table
            print("2")
            db.reference("/main_table").child(id_str).set({
                'id':max_id_value,
                'serviceid':max_serviceid_value,
                'zipid':max_zipid_value
                })
        else:
            existing_sr_id = int(service_rate_query_results[0])
            existing_zip_id = int(zip_query_results[0])
            db.reference("/main_table").child(id_str).set({
                'id':max_id_value,
                'serviceid':existing_sr_id,
                'zipid':existing_zip_id})



        #this is where we aggregate the values input into the form.
        cleaned_admin_list = [zip_code,state,utility_name,service_type,ownership,comm_rate,res_rate,ind_rate]
        cleaned_admin_form = ("User has input the following values. ZIP: {}, State: {}, Utility Name: {}, Service Type: {}, Ownership: {}, Commercial Rate: {}, Residential Rate: {}, Industrial Rate : {}".format(
            cleaned_admin_list[0],
            cleaned_admin_list[1],
            cleaned_admin_list[2],
            cleaned_admin_list[3],
            cleaned_admin_list[4],
            cleaned_admin_list[5],
            cleaned_admin_list[6],
            cleaned_admin_list[7]))

    #Lastly, we specify which page we want to send this information to so it is available for request.
    #We also must specify what it's object name is for reference in the page, which in this case is "CleanedAdminForm".
    return render_template("admin.html",CleanedAdminForm1 = cleaned_admin_form)

#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************

@app.route("/update_form_decoder",methods=['GET','POST'])
def update_form_decoder():
    ref_main = db.reference("/main_table")
    ref_zip = db.reference("/zipcode_table")
    ref_s_rate = db.reference("/service_rate_table")
    ref_utility = db.reference("/utility_table")

    def no_sql_to_dataframe(table):
        data = table.get()
        data_no_nulls = []
        for val in data:
            if val != None :
                data_no_nulls.append(val)
        df = pd.DataFrame.from_dict(data_no_nulls)
        return df

    main_df = no_sql_to_dataframe(ref_main)
    zip_df = no_sql_to_dataframe(ref_zip)
    s_rate_df = no_sql_to_dataframe(ref_s_rate)
    utility_df = no_sql_to_dataframe(ref_utility)

    #And here, we establish the max id for each table:
    max_id_value = max(main_df['id'])
    max_zipid_value = max(zip_df['zipid'])
    max_serviceid_value = max(s_rate_df['serviceid'])
    max_eiaid_value = max(s_rate_df['eiaid'])

    print("\nRequest Form: ",request.form.values(),'\n')
    
    transformed_vals = [x for x in request.form.values()] #this converts the string values retrived via request.form.values() from model.py into float values.
    print("\nTransformed Vals: ",transformed_vals,'\n')

    zipid = transformed_vals[0]
    zip_code = ''
    if transformed_vals[1] == ' ':
        zip_code = ''
    elif transformed_vals[1].isdigit() == True:
        zip_code = transformed_vals[1]
    else:
        zip_code = ''

    state = ''
    if (len(transformed_vals[2]) == 2) and (transformed_vals[2].isalpha() == True):
        state = transformed_vals[2]
    else:
        state = ''

    eiaid = transformed_vals[3]
    utility_name = transformed_vals[4]
    ownership = transformed_vals[5]

    serviceid = transformed_vals[6]
    service_type = transformed_vals[7]
    comm_rate = transformed_vals[8]
    res_rate = transformed_vals[9]
    ind_rate = transformed_vals[10]
    #***********
    #***********
    #***********
    # Enter your UPDATE code here

    def table_checker(table_id,input_id):   
        match_finder = ""
        if input_id != '':
            input_id = int(input_id)
        
        for i in range(len(table_id)):
            if table_id[i] == input_id:
                match_finder = input_id #Why doesn't "table_id[i]" work?
                print('Record {} exists in table.'.format(match_finder))
                break
            else:
                pass
            
        return match_finder
    
    update_utility_matchfinder = table_checker(utility_df['eiaid'],eiaid)
    update_service_rate_matchfinder = table_checker(s_rate_df['serviceid'],serviceid)
    update_zip_matchfinder = table_checker(zip_df['zipid'],zipid)

    def utility_table_value_updater(eiaid_str,eiaid,ownership,utility_name):
        eiaid_str = str(eiaid)
        eiaid = int(eiaid)
        db.reference("/utility_table").child(eiaid_str).set({
                'eiaid':eiaid,
                'ownership':ownership,
                'utility_name':utility_name
            })
        
    #Same thing we did to the zipcode_table is what we're gonna do to the utility_table.
    utility_message = ''

    if update_utility_matchfinder != '':
        eiaid = int(eiaid)
        #Aside from this entry, the rest can stay pretty much the same for the other tables.
        utility_match_index_value = utility_df[utility_df['eiaid'] == eiaid].index[0]
        eiaid_str = str(eiaid)
        
        if((ownership == '')and(utility_name == '')):#if both are missing, then return a message saying no update made
            utility_message = 'No values were updated.'
        
        elif(ownership == ''): #if user didn't input ownership value, take it from the dataframe before setting value
            ownership = utility_df['ownership'][utility_df['eiaid']==eiaid].iloc[0]
            utility_table_value_updater(eiaid_str,eiaid,ownership,utility_name)
            utility_message = '{} was updated.'.format('Utility Name')
            
        elif(utility_name == ''): #if user didn't input ownership value, take it from the dataframe before setting value
            utility_name = utility_df['utility_name'][utility_df['eiaid']==eiaid].iloc[0]
            utility_table_value_updater(eiaid_str,eiaid,ownership,utility_name)
            utility_message = '{} was updated.'.format('Ownership')
            
        elif((ownership != '')and(utility_name != '')): #if all values are present, update all
            utility_table_value_updater(eiaid_str,eiaid,ownership,utility_name)
            utility_message = 'All Utility values were updated.'
            
        else:
            utility_message = 'No values were updated.'
            #return message saying nothing was changed
    else:
        #return message saying nothing was changed
        utility_message = 'The eiaid was missing, so nothing was updated.'
        
    print(utility_message)

    def service_rate_table_value_updater(sid_str,serviceid,comm_rate,eiaid,ind_rate,res_rate,service_type):
        sid_str = str(sid_str)
        serviceid = int(serviceid)
        comm_rate = float(comm_rate)
        eiaid = int(eiaid)
        ind_rate = float(ind_rate)
        res_rate = float(res_rate)
        
        db.reference("/service_rate_table").child(sid_str).set({
            'comm_rate':comm_rate,
            'eiaid':eiaid,
            'ind_rate':ind_rate,
            'res_rate':res_rate,
            'service_type':service_type,
            'serviceid':serviceid
        })

    #Next we search the Service Rate Table for the values and update them accordingly
    service_rate_message = ''

    existing_values = []
    values_not_updated = []

    if update_service_rate_matchfinder == '':
        service_rate_message = 'The serviceid was missing, so nothing was updated.'
    else:
        serviceid = int(serviceid)
        if ((service_type=='')and(comm_rate=='')and(res_rate=='')and(ind_rate=='')and(eiaid=='')):
            service_rate_message = 'All values were missing, so nothing was updated.'
        else:
            if service_type == '':
                service_type = s_rate_df['service_type'][s_rate_df['serviceid']==serviceid].iloc[0]
                values_not_updated.append('Service Type')
            else:
                existing_values.append('Service Type')
            
            if comm_rate == '':
                comm_rate = s_rate_df['comm_rate'][s_rate_df['serviceid']==serviceid].iloc[0]
                values_not_updated.append('Commercial Rate')
            else:
                existing_values.append('Commercial Rate')
            if res_rate == '':
                res_rate = s_rate_df['res_rate'][s_rate_df['serviceid']==serviceid].iloc[0]
                values_not_updated.append('Residential Rate')
            else:
                existing_values.append('Residential Rate')
            if ind_rate == '':
                ind_rate = s_rate_df['ind_rate'][s_rate_df['serviceid']==serviceid].iloc[0]
                values_not_updated.append('Industry Rate')
            else:
                existing_values.append('Industry Rate')
            if eiaid == '':
                eiaid = s_rate_df['eiaid'][s_rate_df['serviceid']==serviceid].iloc[0]
                values_not_updated.append('EIAID')
            else:
                existing_values.append('EIAID')
            
            if values_not_updated == []:
                service_rate_message = 'All Service Rate values were updated successfully!'
            else:
                service_rate_message = 'The following values did not update: {}.  All other values of the Service Rate table were updated.'.format(values_not_updated)
            
            srlist = [serviceid,service_type,comm_rate,res_rate,ind_rate,eiaid]
            for i in srlist:
                print(i)
            sid_str = str(serviceid)
            service_rate_table_value_updater(sid_str,serviceid,comm_rate,eiaid,ind_rate,res_rate,service_type)

    print(service_rate_message)

    #Lastly, we search the Zip Table for the values and update them accordingly
    def zip_table_value_updater(zipid,zip_str,zip_code,state):
        zipid = int(zipid)
        zip_str = str(zip_str)
        
        db.reference("/zipcode_table").child(zip_str).set({
            'zip':zip_code,
            'state':state,
            'zipid':zipid
        })

    zip_message = ''
    existing_values = []
    values_not_updated = []

    if update_zip_matchfinder == '':
        zip_message = 'The zipid was missing, so nothing was updated.'
    else:
        zipid = int(zipid)
        if ((zip_code=='')and(state=='')):
            zip_message = 'All values were missing, so nothing was updated.'
        else:
            if zip_code == '':
                zip_code = zip_df['zip'][zip_df['zipid']==update_zip_matchfinder].iloc[0]
                values_not_updated.append('Zip Code')
            else:
                existing_values.append('Zip Code')
            if state == '':
                state = zip_df['state'][zip_df['zipid']==update_zip_matchfinder].iloc[0]
                values_not_updated.append('State')
            else:
                existing_values.append('State')
            
            if values_not_updated == []:
                zip_message = 'All ZIP values were updated successfully!'
            else:
                zip_message = 'The following values did not update: {}.  All other values of the ZIP table were updated.'.format(values_not_updated)
            
            print(zip_code)
            zip_str = str(update_zip_matchfinder)
            zip_table_value_updater(update_zip_matchfinder,zip_str,zip_code,state)

    print(zip_message)

    utility_message
    service_rate_message
    zip_message
    update_message = [utility_message,service_rate_message,zip_message]

    #***********
    #***********
    #***********

    #this is where we aggregate the values input into the form.
    cleaned_admin_list = [zipid,zip_code,state,eiaid,utility_name,ownership,serviceid,service_type,comm_rate,res_rate,ind_rate]
    cleaned_admin_form = ("{}  {}  {}".format(update_message[0],update_message[1],update_message[2]))

    #Lastly, we specify which page we want to send this information to so it is available for request.
    #We also must specify what it's object name is for reference in the page, which in this case is "CleanedAdminForm".
    return render_template("admin.html",CleanedAdminForm2 = cleaned_admin_form)

#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************

@app.route("/delete_form_decoder",methods=['GET','POST'])
def delete_form_decoder():

    ref_main = db.reference("/main_table")
    ref_zip = db.reference("/zipcode_table")
    ref_s_rate = db.reference("/service_rate_table")
    ref_utility = db.reference("/utility_table")

    def no_sql_to_dataframe(table):
        data = table.get()
        data_no_nulls = []
        for val in data:
            if val != None :
                data_no_nulls.append(val)
        df = pd.DataFrame.from_dict(data_no_nulls)
        return df

    main_df = no_sql_to_dataframe(ref_main)
    zip_df = no_sql_to_dataframe(ref_zip)
    s_rate_df = no_sql_to_dataframe(ref_s_rate)
    utility_df = no_sql_to_dataframe(ref_utility)

    #And here, we establish the max id for each table:
    max_id_value = max(main_df['id'])
    max_zipid_value = max(zip_df['zipid'])
    max_serviceid_value = max(s_rate_df['serviceid'])
    max_eiaid_value = max(s_rate_df['eiaid'])

    #transformed_vals = request.form.values()
    print("\nRequest Form: ",request.form.values(),'\n')
    
    transformed_vals = [x for x in request.form.values()] #this converts the string values retrived via request.form.values() from model.py into float values.
    print("\nTransformed Vals: ",transformed_vals,'\n')

    main_id = int(transformed_vals[0])
    print('Main ID: ',main_id)
    
    def table_checker(table_id,input_id):   
        match_finder = ""
        
        for i in range(len(table_id)):
            if table_id[i] == input_id:
                match_finder = input_id #Why doesn't "table_id[i]" work?
                print('Record {} exists in table'.format(match_finder))
                break
            else:
                pass
            
        return match_finder

    delete_main_matchfinder = table_checker(main_df['id'],main_id)

    message = ''

    if delete_main_matchfinder == '':
        #If the ID isn't there or the user entered a blank, then:
        message = 'Invalid/missing id.  Please try again.'
    else:
        #Now we get the zipid and serviceid values.
        m_id = main_df['id'][main_df['id'] == main_id].iloc[0]
        print('Main ID: ',m_id)
        z_id = main_df['zipid'][main_df['id'] == main_id].iloc[0]
        print('ZIP ID: ',z_id)
        s_id = main_df['serviceid'][main_df['id'] == main_id].iloc[0]
        print('Service ID: ',s_id)
        print("Main ID Record: ",m_id,z_id,s_id)
        #After saving these values, we can delete this main_table record.
        db.reference('/main_table').child(str(main_id)).delete() #NEED TO REPLACE *****************************************************
        
        #Next, we look at the count of matching zipid's in the main_df.  
        if (main_df['zipid'] == z_id).sum() != 1:
            print('ZIP ID Count: ',(main_df['zipid'] == z_id).sum())
            pass
        else:
            #If there is exactly 1 count, we delete the zipid record from the zip_table.
            print('Only one {} found. Deleting record.'.format('ZIP ID'))
            #delete the zipid record
            db.reference('/zipcode_table').child(str(z_id)).delete() #NEED TO REPLACE *****************************************************
        
        #Next, we look at the count of matching serviceid's in the main_df.
        if (main_df['serviceid'] == s_id).sum() != 1:
            print('Service ID Count: ',(main_df['serviceid'] == s_id).sum())
            pass
        else:
            #If there is exactly 1 count, we delete the serviceid record from the service_rate_table.
            print('Only one {} found. Deleting record.'.format('Service ID'))
            #delete the serviceid record
            db.reference('/service_rate_table').child(str(s_id)).delete() #NEED TO REPLACE *****************************************************
            
            #Finally, we look at the count of matching eiaid's in the service table.
            e_id = s_rate_df['eiaid'][s_rate_df['serviceid'] == s_id].iloc[0]
            print("EIAID: ",e_id)
            if (s_rate_df['eiaid'] == e_id).sum() != 1:
                print('EIAID Count: ',(s_rate_df['eiaid'] == e_id).sum())
                pass
            else:
                #If there is exactly 1 count, we delete the eiaid record from the utility_table.
                print('Only one {} found. Deleting record.'.format('EIAID'))
                #delete the eiaid record
                db.reference('/utility_table').child(str(e_id)).delete() #NEED TO REPLACE *****************************************************

    print(message)

    cleaned_admin_list = [main_id]
    cleaned_admin_form = ("User has input: Main ID: {}.".format(cleaned_admin_list[0]))
    
    return render_template("admin.html",CleanedAdminForm3 = cleaned_admin_form)


#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************
#**********************************************

if __name__ == '__main__':
    app.run(debug=True)