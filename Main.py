from math import radians, cos, sin, asin, sqrt
from statistics import mean
import pandas as pd
from fastapi import FastAPI
import os
import asyncio
import xlsxwriter
import time
from calendar import timegm


def unique(dataset):
    output = []
    for x in dataset:
        if x not in output:
            output.append(x)
    return output


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r


app = FastAPI()

try:
    @app.get("/assetReport")
    def assetReport(startTime: str, endTime: str):

        tripInfoData = pd.ExcelFile('Trip-Info.xlsx')
        df = tripInfoData.parse('Trip-Info')

        wb = xlsxwriter.Workbook("assetReport.xlsx")
        ws = wb.add_worksheet("Report")
        ws.write('A1', 'License plate number')
        ws.write('B1', 'Distance')
        ws.write('C1', 'Number of Trips Completed')
        ws.write('D1', 'Average Speed')
        ws.write('E1', 'Transporter Name')
        ws.write('F1', 'Number of Speed Violations')

        rowIndex = 2

        directory = 'EOL-dump'
        totalFiles = len(os.listdir(directory))
        error = 0
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)

            # checking if it is a file
            if os.path.isfile(f):
                file = pd.read_csv(f, engine='python')
                print(f)
                dataset = file[file["tis"].between(int(startTime), int(endTime), inclusive=True)]
                dataset.dropna(subset=["spd"], inplace=True)

                if len(dataset) > 0:
                    # Average speed
                    # print(mean(dataset["spd"]))

                    # License plate number
                    licensePlateNumber = unique(dataset["lic_plate_no"])
                    # print(licensePlateNumber[0])

                    # Number of trips
                    noOfTrips = df[df['vehicle_number'] == licensePlateNumber[0]]
                    if len(noOfTrips) == 0:
                        totalTrips = 0
                        transporterName = [""]
                    else:
                        totalTrips = 0
                        for x in range(len(noOfTrips)):
                            tripTime = timegm(time.strptime(str(noOfTrips.iloc[x]["date_time"]), "%Y%m%d%H%M%S"))
                            if int(startTime) <= tripTime <= int(endTime):
                                totalTrips += 1
                        print(totalTrips)

                        # Transporter Name
                        transporterName = unique(noOfTrips['transporter_name'])

                    # Number of speed violation
                    count = sum(bool(x) for x in dataset['osf'])

                    # Calculate Distance
                    first_loc = dataset.iloc[0]
                    last_loc = dataset.iloc[-1]
                    distance = haversine(first_loc["lon"], first_loc["lat"], last_loc["lon"], last_loc["lat"])

                    ws.write('A' + str(rowIndex), licensePlateNumber[0])
                    ws.write('B' + str(rowIndex), distance)
                    ws.write('C' + str(rowIndex), totalTrips)
                    ws.write('D' + str(rowIndex), mean(dataset["spd"]))
                    ws.write('E' + str(rowIndex), transporterName[0])
                    ws.write('F' + str(rowIndex), count)

                    rowIndex += 1
                else:
                    error += 1
                    print("error")
        if error == totalFiles:
            os.remove("assetReport.xlsx")
            return "No Data Available"
        else:
            wb.close()
            return "Asset Report Generated"

except Exception as e:
    pass
