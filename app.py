
from flask import Flask, render_template, request, send_file, session
import pandas as pd
import datetime as dt
import loan
import io
import xlsxwriter
import yagmail

app = Flask(__name__)
app.secret_key = "1642"


@app.before_request
def session_default():
    if "session_pointer" not in session:
        session["session_pointer"] = 0


@app.route("/")
def home():
    try:
        if session["session_pointer"] == 0:
            return render_template("loan.html")
        else:
            defaultamount = session.get("amountBorrowed")
            defaultinterest = session.get("interestRate")
            defaultpartial = session.get("ifPartiallyAmortized")
            defaulttime = session.get("timeHorizon")
            defaultby = session.get("by")
            defaultdate = session.get("startDate")
            defaultemail = session["emailAddress"]
            return render_template("loan.html", defaultAmount=defaultamount,
                                   defaultInterest=defaultinterest,
                                   defaultPartial=defaultpartial,
                                   defaultTime=defaulttime,
                                   defaultBy=defaultby,
                                   defaultDate=defaultdate,
                                   defaultEmail=defaultemail)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        session["session_pointer"] = 1

        session["loanType"] = request.form.get("loanType")
        session["repaymentDescription"] = request.form.get(
            "repaymentDescription")
        session["repaymentTimeframe"] = request.form.get("repaymentTimeframe")
        session["amountBorrowed"] = request.form.get("amountBorrowed")
        session["interestRate"] = request.form.get("interestRate")
        session["timeHorizon"] = request.form.get("timeHorizon")
        session["interestType"] = request.form.get("interestType")
        session["ifPartiallyAmortized"] = request.form.get(
            "ifPartiallyAmortized")
        session["by"] = request.form.get("by")
        session["startDate"] = request.form.get("startDate")
        session["emailAddress"] = request.form.get("emailAddress")

        repayframe = session["repaymentTimeframe"]
        if repayframe == "Annually":
            monthequivalent = 12
        elif repayframe == "Semi_annually":
            monthequivalent = 6
        elif repayframe == "Quarterly":
            monthequivalent = 3
        elif repayframe == "Bimonthly":
            monthequivalent = 2
        elif repayframe == "Monthly":
            monthequivalent = 1
        if (int(session["timeHorizon"])/monthequivalent) != int((int(session["timeHorizon"])/monthequivalent)):
            return ("""
                   Invalid repayment timeframe: The selected period must evenly divide the total loan term (in months).""")

        loanlist = loan.loanAmortizer(
            loan_type=session["loanType"],
            repayment_description=session["repaymentDescription"],
            repayment_timeframe=session["repaymentTimeframe"],
            amount_borrowed=int(session["amountBorrowed"]),
            annual_interest=(float(session["interestRate"]))/100,
            number_months=int(session["timeHorizon"]),
            annual_interest_type=session["interestType"],
            partial_endpayment=int(session["ifPartiallyAmortized"] or 0),
            incre_decre_amount=int(session["by"] or 0),
            start_date=dt.datetime.strptime(
                session["startDate"], "%Y-%m-%d").date()
        )
        loanData = loanlist[0].applymap(
            lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else x)
        loanData = loanData.to_html(index=False)
        total_interest = loanlist[1]

        # Sending an email when when used
        sender_email = "kamarasekou798@gmail.com"
        app_password = "qheg zquf mtqe wcol"
        receiver_email = session.get("emailAddress", "N/A")

        subject = "New Loan Calculation Request"
        body = f"""
        Hello,

        A user with the  email: {receiver_email} has just completed a loan calculation on the platform.
        
        Best regards,
        Afya Sacco Loan Calculator System
        """
        yag = yagmail.SMTP(sender_email, app_password)
        yag.send(to=receiver_email, subject=subject, contents=body)

        return render_template("schedule.html", totalInterest=total_interest,
                               scheduleTable=loanData,
                               loanType=session["loanType"],
                               amountBorrowed=int(session["amountBorrowed"]),
                               interestRate=(float(session["interestRate"])),
                               repaymentDescription=session["repaymentDescription"],
                               repaymentTimeframe=session["repaymentTimeframe"],
                               startDate=dt.datetime.strptime(
                                   session["startDate"], "%Y-%m-%d").date(),
                               by=session["by"],
                               interestType=session["interestType"],
                               numberOfMonths=session["timeHorizon"],
                               ifPartial=session["ifPartiallyAmortized"])
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route("/download")
def download():
    try:
        loanlist = loan.loanAmortizer(
            loan_type=session.get("loanType"),
            repayment_description=session.get("repaymentDescription"),
            repayment_timeframe=session.get("repaymentTimeframe"),
            amount_borrowed=int(session.get("amountBorrowed") or 0),
            annual_interest=(float(session.get("interestRate") or 0))/100,
            number_months=int(session.get("timeHorizon") or 0),
            annual_interest_type=session.get("interestType"),
            partial_endpayment=int(session.get("ifPartiallyAmortized") or 0),
            incre_decre_amount=int(session.get("by") or 0),
            start_date=dt.datetime.strptime(session.get(
                "startDate") or "2024-01-01", "%Y-%m-%d").date()
        )

        loanData = loanlist[0]
        if session["loanType"] != "Interest_only":
            if session["loanType"] != "Flat_interest":
                metadata = {
                    "Field": [
                        "Mail Address", "Loan Type", "Amount Borrowed", "Interest Rate",
                        "Interest Type", "Repayment Description", "Repayment Timeframe",
                        "Start Date"
                    ],
                    "Value": [
                        session.get("emailAddress", "N/A"),
                        session.get("loanType", "N/A"),
                        f"{float(session.get('amountBorrowed', 0)):,.2f}",
                        f"{float(session.get('interestRate', 0)):.2f}%",
                        session.get("interestType", "N/A"),
                        session.get("repaymentDescription", "N/A"),
                        session.get("repaymentTimeframe", "N/A"),
                        session.get("startDate", "N/A")
                    ]
                }

                if session.get("repaymentDescription") != "Level" and session["loanType"] == "Partially_amortized":
                    metadata["Field"].insert(2, "IfPartial")
                    metadata["Field"].insert(7, "By")

                    metadata["Value"].insert(
                        2, session.get("ifPartiallyAmortized", "N/A"))
                    metadata["Value"].insert(7, session.get("by", "N/A"))
                elif session["loanType"] == "Partially_amortized":
                    metadata["Field"].insert(2, "IfPartial")
                    metadata["Value"].insert(
                        2, session.get("ifPartiallyAmortized", "N/A"))
                elif session.get("repaymentDescription", "N/A") != "Level":
                    metadata["Field"].insert(6, "By")
                    metadata["Value"].insert(6, session.get("by", "N/A"))
            else:
                metadata = {
                    "Field": [
                        "Mail Address", "Loan Type", "Amount Borrowed", "Interest Rate",
                        "Interest Type", "Repayment Description", "Repayment Timeframe",
                        "Start Date"
                    ],
                    "Value": [
                        session.get("emailAddress", "N/A"),
                        session.get("loanType", "N/A"),
                        f"{float(session.get('amountBorrowed', "N/A")):,.2f}",
                        f"{float(session.get('interestRate', "N/A")):.2f}%",
                        "Nominal",
                        "Level",
                        session.get("repaymentTimeframe", "N/A"),
                        session.get("startDate", "N/A")
                    ]
                }
        else:
            metadata = {
                "Field": [
                    "Email Address", "Loan Type", "Amount Borrowed", "Interest Rate",
                    "Interest Type", "Repayment Timeframe",
                    "Start Date"
                ],
                "Value": [
                    session.get("emailAddress", "N/A"),
                    session.get("loanType", "N/A"),
                    f"{float(session.get('amountBorrowed', "N/A")):,.2f}",
                    f"{float(session.get('interestRate', "N/A")):.2f}%",
                    session.get("interestType", "N/A"),
                    session.get("repaymentTimeframe", "N/A"),
                    session.get("startDate", "N/A")
                ]
            }

        metadata = pd.DataFrame(metadata)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            metadata.to_excel(writer, sheet_name="Loan Metadata",
                              index=False)  # Metadata sheet
            loanData.to_excel(writer, sheet_name="Loan Schedule",
                              index=False)  # Loan schedule sheet

        output.seek(0)

        # Send the file as an Excel download
        return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         as_attachment=True, download_name="loan_details.xlsx")
    except Exception as e:
        return f"An error occurred: {str(e)}", 500


@app.route("/userGuide")
def unserGuide():
    return render_template("userGuide.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
