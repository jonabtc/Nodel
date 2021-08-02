import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import gspread

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "credentials.json"

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
SAMPLE_SPREADSHEET_ID = "1DRD97TAw2WIuTCG0Nh6BW-aVvDKAgY1wvJb38V-3vU8"
WRITE_SPREADSHEET_ID = "1No3fUTM43z7btO2qJi1o5fEtk2GdctDtx8EmuAZhsr4"
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()


def get_data():
    result = (
        sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Reto1").execute()
    )
    values = result.get("values", [])

    return pd.DataFrame(values[1:], columns=values[0])


def create_table(data_frame):
    return pd.pivot_table(
        data_frame,
        values=["Country", "Theme"],
        columns=("Country", "Theme"),
        index=["Author", "Sentiment"],
        aggfunc={"Country": lambda x: x is not None, "Theme": lambda x: x is not None},
        fill_value=False,
    )


def write_data(data_to_export):
    client = gspread.authorize(creds)
    sht1 = client.open_by_key(WRITE_SPREADSHEET_ID).sheet1

    country_list = []
    theme_list = []
    for x in data_to_export.columns:
        a, b, c = x
        if a == "Country":
            country_list.append(b)
        else:
            theme_list.append(c)

    # cleaning the sheet
    sht1.clear()
    sht1.delete_rows(start_index=1, end_index=2)
    for record in data_to_export.to_records():
        sht1.append_row(list(record))

    # insert table headers
    axes = data_to_export.index.dtypes.axes[0].values
    axes_length = len(axes)
    country_length = len(country_list)
    theme_length = len(theme_list)
    sht1.insert_row(list(axes) + country_list + theme_list)
    sht1.insert_row([None] * axes_length + ["Country"] * country_length + ["Theme"] * theme_length)
    sht1.merge_cells(1, 1 + axes_length, 1, axes_length + country_length)
    sht1.merge_cells(1, 1 + axes_length + country_length, 1, axes_length+country_length+theme_length)
    sht1.format("1", {"horizontalAlignment": "CENTER"})


if __name__ == "__main__":
    data = get_data()
    table = create_table(data)
    write_data(table)
