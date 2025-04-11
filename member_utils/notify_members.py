from datetime import date

import pandas as pd
from googleapiclient.discovery import build

from member_utils.google_auth import generate_creds
from member_utils.gsheet_loader import load_df

CREDS_PATH = "credentials.json"
TOKEN_PATH = "token.json"  # noqa:S105

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

GSHEET_ID = "REPLACE_BY_GSHEET_ID"
TAB_NAME = "REPLACE_BY_GSHEET_TAB"
COLUMN_MAPPING = {
    "A": "email",
    "B": "nom",
    "C": "prenom",
    "D": "date_fin_adhesion",
}

START_DATE = date(2026, 4, 8)
END_DATE = date(2026, 5, 8)
FILTER_DATE_KEY = "date_fin_adhesion"
KEEP_EMAILS = None

LOCAL_CSV_PATH = "local.csv"

DATE_FORMAT = "%d/%m/%Y"

if __name__ == "__main__":
    if LOCAL_CSV_PATH:
        member_df = pd.read_csv(LOCAL_CSV_PATH)
    else:
        creds = generate_creds(creds_path=CREDS_PATH, token_path=TOKEN_PATH, scopes=SCOPES)

        service = build("sheets", "v4", credentials=creds)

        member_df = load_df(
            gsheet_service=service,
            gsheet_id=GSHEET_ID,
            column_mapping=COLUMN_MAPPING,
            sheet_name=TAB_NAME,
        )

    member_df[FILTER_DATE_KEY] = pd.to_datetime(member_df[FILTER_DATE_KEY], format=DATE_FORMAT)

    latest_membership_date_col = f"last_{FILTER_DATE_KEY}"
    export_membership_date_col = f"export_{FILTER_DATE_KEY}"

    # Retrieving its most recent annual membership for each (first name, name)
    member_df[latest_membership_date_col] = member_df.groupby(["prenom", "nom"])[FILTER_DATE_KEY].transform("max")

    member_df[export_membership_date_col] = member_df[FILTER_DATE_KEY].dt.strftime(DATE_FORMAT)

    if KEEP_EMAILS:
        member_df = member_df.loc[member_df["email"].isin(KEEP_EMAILS)]

    # Only keeping:
    # - the latest memberships
    # - whose target date falls between the chosen start and end
    member_df = member_df.loc[
        (member_df[FILTER_DATE_KEY].dt.date >= START_DATE)
        & (member_df[FILTER_DATE_KEY].dt.date < END_DATE)
        & (member_df[FILTER_DATE_KEY] == member_df[latest_membership_date_col])
    ]

    for target_membership in member_df[["email", "nom", "prenom", export_membership_date_col]].to_dict(
        orient="records"
    ):
        print(f"""
            @{target_membership["email"]}:\n
            Hello {target_membership["prenom"]} {target_membership["nom"]}.\n
            Your membership expires on {target_membership[export_membership_date_col]}
        """)
