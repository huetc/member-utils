from datetime import date

import pandas as pd

START_DATE = date(2026, 4, 8)
END_DATE = date(2026, 5, 8)
FILTER_DATE_KEY = "date_fin_adhesion"
KEEP_EMAILS = None

LOCAL_CSV_PATH = "local.csv"

DATE_FORMAT = "%d/%m/%Y"

if __name__ == "__main__":
    member_df = pd.read_csv(LOCAL_CSV_PATH)

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
        print(
            f"""
            @{target_membership["email"]}:\n
            Hello {target_membership["prenom"]} {target_membership["nom"]}.\n
            Your membership expires on {target_membership[export_membership_date_col]}
        """
        )
