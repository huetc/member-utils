import logging

import pandas as pd
from google.auth.external_account_authorized_user import Credentials as ExternalCredentials
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def build_gsheet_service(creds: Credentials | ExternalCredentials):
    """Build the service to GSheets.

    :param creds: the path to the credential file
    """
    return build(
        "sheets",
        "v4",
        credentials=creds,
    )


def load_df(
    gsheet_service,
    gsheet_id: str,
    column_mapping: dict[str, str],
    start_row: str = "",
    end_row: str = "",
    sheet_name: str = "Sheet1",
) -> pd.DataFrame:
    """Load a DataFrame from a GSheet.

    :param gsheet_service: the service used to connect to the GSheet API
    :param gsheet_id: the ID of the GSheet
    :param column_mapping: the keys are the column letters in the GSheet column.
      The values are the column headers.
    :param start_row: first row of the selected range
    :param end_row: last row of the selected range. Can be set without
        *start_row*, which will be set to 1. *end_row* will not work
        correctly in Google API call if set alone
        (e.g.: A:A10 actually yields A10:A1000)
    :param sheet_name: the sheet name in the spreadsheets. Default value is
        the default name of the first sheet of any spreadsheet
    """
    # Warning : end_row cannot be set alone
    # (e.g. : A:A10 actually yields A10:A1000)
    if end_row and not start_row:
        start_row = "1"
    results: dict[str, pd.Series] = {}
    for col_location, col_name in column_mapping.items():
        col_data = (
            gsheet_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=gsheet_id,
                range=f"{sheet_name}!{col_location}{start_row}:{col_location}{end_row}",
            )
            .execute()
        )
        if not (col_values := col_data.get("values")):
            empty_col_err_msg = f"In sheet {gsheet_id}, column {col_location} is empty."
            logging.error(empty_col_err_msg)
            raise ValueError(empty_col_err_msg)
        try:
            # Retrieving the values excluding the first header row
            values = col_values[1:]
            results[col_name] = pd.Series(one_col_row[0] if one_col_row else None for one_col_row in values)
        except IndexError as exc:
            idx_err_msg = (
                f"In sheet {gsheet_id}, for column '{col_name}' and "
                f"location {col_location}, got no values in the range."
            )
            logging.exception(idx_err_msg)
            raise ValueError(idx_err_msg) from exc

    result_df = pd.DataFrame(results) if len(results) > 0 else pd.DataFrame(columns=column_mapping.values())
    logging.info("Successfully imported data from GSheet %s", gsheet_id)
    logging.debug(
        "From the GSheet : \n%s\n, imported the following table: \n%s",
        gsheet_id,
        result_df.describe(),
    )
    return result_df
