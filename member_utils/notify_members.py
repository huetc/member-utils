import unicodedata

import pandas as pd
from googleapiclient.discovery import build

from member_utils.config import JobConfig
from member_utils.gmail_sender import build_gmail_service, send_email
from member_utils.google_auth import generate_creds
from member_utils.gsheet_loader import load_df
from member_utils.message_templater import get_jinja_env, render_message_template

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


if __name__ == "__main__":
    config = JobConfig()

    if config.local_csv_path:
        member_df = pd.read_csv(config.local_csv_path)
    else:
        creds = generate_creds(
            creds_path=config.google_auth_creds_path, token_path=config.google_auth_token_path, scopes=SCOPES
        )

        service = build("sheets", "v4", credentials=creds)

        member_df = load_df(
            gsheet_service=service,
            gsheet_id=config.gsheet_id,
            column_mapping=config.gsheet_column_mapping,
            sheet_name=config.gsheet_tab_name,
        )

    # Name and first name standardisation:
    # - replace specific characters (e.g. accents)
    # - replace "-" with white spaces
    # - write in lower/upper case
    member_df["nom_standard"] = (
        member_df["nom"]
        .apply(
            lambda name: "".join([
                character for character in unicodedata.normalize("NFKD", name) if not unicodedata.combining(character)
            ])
            if name
            else None
        )
        .replace("-", " ", regex=True)
        .str.upper()
    )

    member_df["prenom_standard"] = (
        member_df["prenom"]
        .apply(
            lambda first_name: "".join([
                character
                for character in unicodedata.normalize("NFKD", first_name)
                if not unicodedata.combining(character)
            ])
            if first_name
            else None
        )
        .replace("-", " ", regex=True)
        .str.upper()
    )

    member_df["date_debut_adhesion"] = pd.to_datetime(member_df["date_debut_adhesion"], format=config.date_format)
    member_df["date_fin_adhesion"] = pd.to_datetime(member_df["date_fin_adhesion"], format=config.date_format)

    latest_membership_date_col = f"last_{config.filter_date_key}"
    export_membership_start_date_col = "export_date_debut_adhesion"
    export_membership_end_date_col = "export_date_fin_adhesion"

    # Retrieving its most recent annual membership for each (standard first name, standard name)
    # Standardisation is useful to catch cases where accents or "-" would otherwise cause membership to be attached to
    # two different persons instead of one
    member_df[latest_membership_date_col] = member_df.groupby(["prenom_standard", "nom_standard"])[
        config.filter_date_key
    ].transform("max")

    member_df[export_membership_start_date_col] = member_df["date_debut_adhesion"].dt.strftime(config.date_format)
    member_df[export_membership_end_date_col] = member_df["date_fin_adhesion"].dt.strftime(config.date_format)

    if config.keep_emails:
        member_df = member_df.loc[member_df["email"].isin(config.keep_emails)]

    # Only keeping:
    # - the latest memberships
    # - whose target date falls between the chosen start and end
    member_df = member_df.loc[
        (member_df[config.filter_date_key].dt.date >= config.start_date)
        & (member_df[config.filter_date_key].dt.date < config.end_date)
        & (member_df[config.filter_date_key] == member_df[latest_membership_date_col])
    ]

    jinja_env = get_jinja_env(config.message_template_directory)

    for target_membership in member_df[
        ["email", "nom", "prenom", export_membership_start_date_col, export_membership_end_date_col]
    ].to_dict(orient="records"):
        message_body = render_message_template(
            jinja_env=jinja_env,
            template_file=config.message_template_file,
            render_variables={
                **target_membership,
                **{
                    "date_debut": target_membership[export_membership_start_date_col],
                    "date_fin": target_membership[export_membership_end_date_col],
                },
            },
        )
        if config.mail_dry_run:
            print(message_body)
        else:
            send_email(
                gmail_service=build_gmail_service(
                    creds=generate_creds(
                        creds_path=config.google_auth_creds_path,
                        token_path=config.google_auth_token_path,
                        scopes=SCOPES,
                    )
                ),
                subject=config.mail_subject,
                body=message_body,
                to_addresses=target_membership["email"],
                bcc_addresses=config.mail_bcc_addresses,
            )
