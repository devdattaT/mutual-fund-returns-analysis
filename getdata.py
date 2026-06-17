import json
import os
import requests
import pandas as pd
import pyxirr


def CalculateSIPReturn(nav_data, starting_date, months, sipAmount):
    invested_amount = 0
    invested_units = 0
    current_value = 0
    previous_value = 0
    max_drawdown = 0
    investment_dates = []
    investment_values = []
    max_drawDown_date = None
    #accumulate the units for each month
    for month in range(months):
        this_date = starting_date + pd.DateOffset(months=month)
        #find the date in the dataframe which is equal to or just after this_date
        nav_row = nav_data[nav_data["date"] >= this_date].head(1)
        if not nav_row.empty:
            nav_value = nav_row["nav"].values[0]
            #load the previous value before updating current_value
            previous_value = current_value
            previous_units = invested_units
            #check what is the value of the investment before adding the new SIP amount
            current_value_of_investment = previous_units * nav_value
            drawDown = 0
            if(current_value_of_investment < previous_value):
                drawDown = 100* (previous_value - current_value_of_investment) / previous_value
              
            #add the SIP amount to the invested amount and calculate the new units
            invested_amount += sipAmount
            invested_units += sipAmount / nav_value
            current_value = invested_units * nav_value
            #add to the investment data
            investment_dates.append(this_date)
            investment_values.append(-1 * sipAmount)

            #check if the drawdown is greater than the max_drawdown
            if(drawDown > max_drawdown):
                max_drawdown = drawDown
                max_drawDown_date = this_date
                
    #calculate the final Values
    last_date = starting_date + pd.DateOffset(months=months+1)
    last_date_row = nav_data[nav_data["date"] >= last_date].head(1)
    last_date_nav = last_date_row["nav"].values[0]
    current_value = invested_units * last_date_nav
    #calculate the XIRR Returns
    investment_dates.append(last_date)
    investment_values.append(current_value)
    xirr = pyxirr.xirr(investment_dates, investment_values)

    return {
        'end_date': last_date,
        'invested_amount': invested_amount,
        'final_value': current_value,
        'xirr': xirr*100,
        "max_drawdown": max_drawdown,
        "max_drawdown_date": max_drawDown_date
    }

def getRollingSIPReturns(nav_data, years, sipAmount=5000):
    # Calculate the number of months in the given years
    months = years * 12
    # Sort the NAV data by date
    nav_data = nav_data.sort_values(by="date")
    
    returns_data = []
    latest_date = nav_data["date"].max()
    
    for index, row in nav_data.iterrows():
        #Only if the date is such that we can invest for the given number of years
        if row["date"] <= latest_date - pd.DateOffset(months=months+1):
            thisReturn = CalculateSIPReturn(nav_data, row["date"], months, sipAmount)
            returns_data.append(thisReturn)
        else:
            break

    return returns_data

def writeCSVFile(data, fileName):
    with open(fileName, 'w') as f:
        headers = list(data[0].keys())
        df = pd.DataFrame(data)
        df.to_csv(f, index=False, columns=headers)



def readDataFromFile(fileName):
    data = None
    with open(fileName, 'r') as f:
        data = json.load(f)
    return data

def getSchemeDetails(scheme_id):
    url = f"https://api.mfapi.in/mf/{scheme_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch scheme details for scheme_id: {scheme_id}. Status code: {response.status_code}")
        return None

if __name__ == "__main__":
    #these are the mutual funds to query
    fnds =[{'cd':'122639', 'name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth'}, 
           {'cd':'115676', 'name': 'SBI GOLD FUND REGULAR PLAN - GROWTH'},
           {'cd':'100822', 'name': 'UTI - NIFTY Index Fund- Regular Plan - Growth Option'},
           {'cd':'100377', 'name': 'Nippon India Growth Fund-Growth Plan-Growth Option'},
           {'cd':'106235', 'name': 'Nippon India Large Cap  Fund- Growth Plan -Growth Option'},
           {'cd':'105758', 'name': 'HDFC Mid-Cap Opportunities Fund - Growth Plan'},
           {'cd':'113177', 'name': 'Nippon India Small Cap Fund - Growth Plan - Growth Option'}           
           ]
    codes = [f['cd'] for f in fnds]
    for c in codes:
       print(f"Fetching data for scheme_id: {c}")
       fileName = os.path.join('mf_data', f"{c}.json")
       if not os.path.exists(fileName):
           schemeDetails = getSchemeDetails(c)
           #Dump to file with pretty print
           with open(fileName, 'w') as f:
               json.dump(schemeDetails, f, indent=4)
        #Assuming we have the data here
       data = readDataFromFile(fileName)
       scheme_name = data.get('meta', {}).get('scheme_name', 'Unknown Scheme')
       nav_data = pd.DataFrame(data.get('data', []))
       nav_data["date"] = pd.to_datetime(nav_data["date"], format="%d-%m-%Y")
       nav_data["nav"] = pd.to_numeric(nav_data["nav"])
       #Get the first and last Dates
       earliest = nav_data["date"].min()
       latest = nav_data["date"].max()

       print(f"Latest NAV for {scheme_name} (Scheme ID: {c}) on {latest.strftime('%Y-%m-%d')}: {nav_data.loc[nav_data['date'] == latest, 'nav'].values[0]}")
       print(f"Earliest NAV for {scheme_name} (Scheme ID: {c}) on {earliest.strftime('%Y-%m-%d')}: {nav_data.loc[nav_data['date'] == earliest, 'nav'].values[0]}")
       
       seven_year_file = os.path.join('returns_data', f"{c}_7year_returns.csv")
       ten_year_file = os.path.join('returns_data', f"{c}_10year_returns.csv")
       if not os.path.exists(seven_year_file):
           #We will calculate the all investments of a certain period  assuming a monthly SIP
           all7YearReturns = getRollingSIPReturns(nav_data, 7)
           #Write the returns to CSV files
           writeCSVFile(all7YearReturns, seven_year_file) 
       if not os.path.exists(ten_year_file):
           #We will calculate the all investments of a certain period  assuming a monthly SIP for 10 years
           all10YearReturns = getRollingSIPReturns(nav_data, 10)
           #Write the returns to CSV files
           writeCSVFile(all10YearReturns, ten_year_file)
