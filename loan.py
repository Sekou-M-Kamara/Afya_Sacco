
import numpy as np
import pandas as pd
import datetime as dt


def loanAmortizer(loan_type,
                  repayment_description,
                  repayment_timeframe,
                  amount_borrowed,
                  number_months,
                  annual_interest_type,
                  annual_interest,
                  incre_decre_amount=0,
                  partial_endpayment=0,
                  start_date=dt.date.today()):

    # start_date = dt.date.today() if start_date == dt.date.today(
    # ) else dt.date(start_date[0], start_date[1], start_date[2])

    if repayment_timeframe == "Annually":
        month_equivalent = 12
        year_devisor = 1
        offset_date = 1
    elif repayment_timeframe == "Semi_annually":
        month_equivalent = 6
        year_devisor = 2
        offset_date = 6
    elif repayment_timeframe == "Quarterly":
        month_equivalent = 3
        year_devisor = 4
        offset_date = 3
    elif repayment_timeframe == "Bimonthly":
        month_equivalent = 2
        year_devisor = 6
        offset_date = 2
    elif repayment_timeframe == "Monthly":
        month_equivalent = 1
        year_devisor = 12
        offset_date = 1

    period_length = int(number_months / month_equivalent)
    period_interest = (1 + annual_interest) ** (month_equivalent/12) - \
        1 if annual_interest_type == "Effective" else annual_interest / year_devisor

    annuity_factor = (1-(1+period_interest) **
                      (-period_length)) / period_interest
    annuity_due_factor = annuity_factor * (1 + period_interest)
    annuity_growth_factor = (annuity_due_factor - (period_length * (
        (1 + period_interest) ** (-period_length)))) / period_interest

    if loan_type == "Amortized" or loan_type == "Partially_amortized":
        print("yes")
        if loan_type == "Partially_amortized":
            end_payment_pv = partial_endpayment * \
                ((1 + period_interest) ** -(period_length))
        else:
            end_payment_pv = 0
            partial_endpayment = 0
        if repayment_description == "Level":
            level_payment = (amount_borrowed -
                             end_payment_pv) / annuity_factor
            repayment_arr = np.full(
                period_length, level_payment)
        elif repayment_description == "Increasing":
            initial_increase_payment = (
                (amount_borrowed - (incre_decre_amount * annuity_growth_factor) - end_payment_pv) / annuity_factor) + incre_decre_amount
            repayment_arr = [
                initial_increase_payment + (i * incre_decre_amount) for i in range(period_length)]
        elif repayment_description == "Decreasing":
            initial_decrease_payment = (
                (amount_borrowed + (incre_decre_amount * annuity_growth_factor) - end_payment_pv) / annuity_factor) - incre_decre_amount
            repayment_arr = [
                initial_decrease_payment - (i * incre_decre_amount) for i in range(period_length)]

        repayment_arr = np.insert(repayment_arr, 0, 0)
        repayment_arr[-1] = repayment_arr[-1] + \
            partial_endpayment
        balance_arr = np.zeros((1+period_length))
        interestpay_arr = np.zeros((1+period_length))
        principal_repay_arr = np.zeros((1+period_length))

        balance_arr[0] = amount_borrowed
        for i in range(1, (1+period_length)):
            interestpay_arr[i] = period_interest * \
                balance_arr[i-1]
            principal_repay_arr[i] = repayment_arr[i] - \
                interestpay_arr[i]
            balance_arr[i] = balance_arr[i-1] - \
                principal_repay_arr[i]

    elif loan_type == "Interest_only":
        repayment_arr = np.full(
            period_length, (amount_borrowed*period_interest))
        repayment_arr[-1] = repayment_arr[-1] + \
            amount_borrowed
        repayment_arr = np.insert(repayment_arr, 0, 0)

        balance_arr = np.full(
            period_length,  amount_borrowed)
        balance_arr = np.insert(
            balance_arr, 0,  amount_borrowed)
        balance_arr[-1] = 0

        interestpay_arr = np.full(
            period_length, (amount_borrowed*period_interest))
        interestpay_arr = np.insert(interestpay_arr, 0, 0)

        principal_repay_arr = np.zeros(period_length)
        principal_repay_arr = np.insert(
            principal_repay_arr, 0, 0)
        principal_repay_arr[-1] = amount_borrowed
    elif loan_type == "Flat_interest":
        period_interest = annual_interest / year_devisor

        principal_repay_arr = np.full(
            period_length, (amount_borrowed / period_length))
        principal_repay_arr = np.insert(principal_repay_arr, 0, 0)

        interestpay_arr = np.full(
            period_length, (amount_borrowed * period_interest))
        interestpay_arr = np.insert(interestpay_arr, 0, 0)

        repayment_arr = interestpay_arr + principal_repay_arr

        balance_arr = np.full((period_length + 1), amount_borrowed)
        balance_arr = balance_arr - np.cumsum(principal_repay_arr)

    repayment_arr = np.round(repayment_arr, 2)
    balance_arr = np.round(balance_arr, 2)
    balance_arr[-1] = abs(balance_arr[-1])
    interestpay_arr = np.round(interestpay_arr, 2)
    principal_repay_arr = np.round(principal_repay_arr, 2)

    if repayment_timeframe == "Semi_annually" or repayment_timeframe == "Quarterly" or repayment_timeframe == "Monthly" or repayment_timeframe == "Bimonthly":
        date_range = [
            start_date + pd.DateOffset(months=offset_date * i) for i in range((period_length + 1))]
    elif repayment_timeframe == "Annually":
        date_range = [
            start_date + pd.DateOffset(years=offset_date * i) for i in range((period_length + 1))]
    date_range = pd.DatetimeIndex(date_range)

    loan_sch_dict = {
        "date":  date_range,
        "repayment":  repayment_arr,
        "interest_payment":  interestpay_arr,
        "principal_repayment":  principal_repay_arr,
        "balance":  balance_arr
    }

    if loan_type != "Flat_interest":
        def correction_test():
            discount_factor_arr = np.array([(1 + period_interest) ** (-i)
                                            for i in range(1, (1+period_length))])
            pv_cashflow_arr = repayment_arr[1:] * discount_factor_arr
            pv_cashflow = sum(pv_cashflow_arr)
            return (pv_cashflow)

        if round(correction_test()) == amount_borrowed and round(abs(balance_arr[-1])) == 0:
            loan_sch_dframe = pd.DataFrame(loan_sch_dict)
        else:
            raise Exception
    else:
        loan_sch_dframe = pd.DataFrame(loan_sch_dict)

    # loan_sch_dframe = loan_sch_dframe.loc[1:]
    # loan_sch_dframe = loan_sch_dframe[[
    #     "date", "repayment", "interest_payment", "principal_repayment"]]
    # loan_id = np.full(period_length, loan_id)
    # status = np.full(period_length, "Awaiting")
    # amount_paid = np.full(period_length, 0)
    # loan_sch_dframe.insert(0, "loan_id", loan_id)
    # loan_sch_dframe["amount_paid"] = amount_paid
    # loan_sch_dframe["status"] = status
    total_interest = round(sum(interestpay_arr), 2)

    return ([loan_sch_dframe, total_interest])
