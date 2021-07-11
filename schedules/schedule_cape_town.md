# Schedule Cape Town Conversion Guide
The 
[official load shedding schedule (PDF)](https://www.capetown.gov.za/Loadshedding1/loadshedding/maps/Load_Shedding_All_Areas_Schedule_and_Map.pdf)
is available at
[City of Cape Town Load Shedding](https://www.capetown.gov.za/Family%20and%20home/Residential-utility-services/Residential-electricity-services/Load-shedding-and-outages).

This PDF needs to be converted to the `loadshedding` `.csv` input format.

## Convert PDF Tables to a Excel Workbook
[PDFTables](https://pdftables.com/) was used to convert the tables for each stage to an Excel Workbook. Note that the option to "Download as Excel" was not used.

Rather, the table for each stage was copied and pasted from the HTML webpage to an Worksheet in LibreCalc. Each Worksheet corresponds to a stage e.g., "Sheet1" to Stage 1, "Sheet2" to Stage 2 and so forth to Stage 8.

This Workbook was saved as an `.xlsx` file. Not that the final conversion script is not compatible with LibreOffice's `.ods` format.

See [cpt_schedule_intermediate.xlsx](cpt_schedule_intermediate.xlsx) for reference.

## Final Conversion
The conversion from the Workbook to the output `.csv` is scripted.
From the root directory of the project, the script can be run as
```
python3 schedules/schedule_cape_town_conversion.py
```