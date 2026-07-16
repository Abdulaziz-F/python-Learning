import streamlit as st

from phishing_backend import (
    analyze_email,
    build_report,
    create_pdf_file,
    create_txt_file
)


st.set_page_config(
    page_title="AI Phishing Email Detector",
    page_icon="🛡️",
    layout="centered"
)


st.title("🛡️ AI Phishing Email Detector")

st.write(
    "Analyze an email and check its links using "
    "Gemini and VirusTotal."
)


sender = st.text_input(
    "Sender Email"
)

subject = st.text_input(
    "Email Subject"
)

email_body = st.text_area(
    "Email Body",
    height=250
)


analyze_button = st.button(
    "Analyze Email"
)


if analyze_button:

    if not sender.strip():
        st.error(
            "Please enter the sender email."
        )

    elif not subject.strip():
        st.error(
            "Please enter the email subject."
        )

    elif not email_body.strip():
        st.error(
            "Please enter the email body."
        )

    else:
        try:
            gemini_api_key = st.secrets[
                "GEMINI_API_KEY"
            ]

            vt_api_key = st.secrets[
                "VT_API_KEY"
            ]

            with st.spinner(
                "Analyzing the email..."
            ):
                result = analyze_email(
                    sender=sender,
                    subject=subject,
                    email_body=email_body,
                    gemini_api_key=gemini_api_key,
                    vt_api_key=vt_api_key
                )

                report = build_report(
                    result
                )

            st.success(
                "Analysis completed successfully!"
            )

            analysis = result["analysis"]

            st.subheader("Classification")

            classification = analysis["classification"]

            if classification == "Safe":
                background_color = "#123c2d"
                border_color = "#2ecc71"
                icon = "🟢"

            elif classification == "Suspicious":
                background_color = "#4a3515"
                border_color = "#f39c12"
                icon = "🟠"

            else:
                background_color = "#4a1f23"
                border_color = "#e74c3c"
                icon = "🔴"


            st.markdown(
                f"""
                <div style="
                    background-color: {background_color};
                    border: 2px solid {border_color};
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                    margin-bottom: 20px;
                ">
                    <h2 style="
                        color: white;
                        margin: 0;
                    ">
                        {icon} {classification.upper()}
                    </h2>
                </div>
                """,
                unsafe_allow_html=True
)
            st.subheader(
                "Risk Score"
            )

            risk_score = analysis[
                "risk_score"
            ]

            st.progress(
                risk_score / 100
            )

            st.write(
                f"{risk_score}/100"
            )


            st.subheader(
                "Confidence"
            )

            st.write(
                f'{analysis["confidence"]}%'
            )


            st.subheader(
                "Summary"
            )

            st.write(
                analysis["summary"]
            )


            st.subheader(
                "Threat Indicators"
            )

            threat_indicators = analysis[
                "threat_indicators"
            ]

            if threat_indicators:
                for item in threat_indicators:
                    st.write(
                        "-",
                        item
                    )
            else:
                st.write(
                    "No threat indicators were identified."
                )


            st.subheader(
                "Reasons"
            )

            for item in analysis["reasons"]:
                st.write(
                    "-",
                    item
                )


            st.subheader(
                "Recommendation"
            )

            st.write(
                analysis["recommendation"]
            )


            st.subheader(
                "VirusTotal Results"
            )

            vt_results = result[
                "virustotal_results"
            ]

            if vt_results:
                for item in vt_results:
                    st.json(item)
            else:
                st.info(
                    "No URLs were found in the email."
                )


            txt_data = create_txt_file(
                report
            )

            pdf_data = create_pdf_file(
                report
            )


            st.subheader(
                "Download Report"
            )

            st.download_button(
                label="Download TXT",
                data=txt_data,
                file_name="phishing_report.txt",
                mime="text/plain"
            )

            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name="phishing_report.pdf",
                mime="application/pdf"
            )

        except KeyError as error:
            st.error(
                f"Missing configuration or response field: {error}"
            )

        except Exception as error:
            st.error(
                f"An error occurred: {error}"
            )