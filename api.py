from flask import Flask, request, jsonify
import os
import json
import time
from phi.agent.python import Agent
from phi.agent import Agent
from phi.model.deepseek import DeepSeekChat
import re
from IPython.display import display, Markdown
import concurrent.futures
import asyncio
from collections import defaultdict
from datetime import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

app = Flask(__name__)



@app.route("/analyze", methods=["POST"])
def analyze():
    try:

        # # Load JSON files
        # with open("add_data_g1.json", "r") as f:
        #     add_data_g1= json.load(f)

        # with open("add_data_g2.json", "r") as f:
        #     add_data_g2 = json.load(f)

        # # Load both JSON files
        # with open("kpi_data_g1.json", "r") as f:
        #     kpi_data_g1 = json.load(f)

        # with open("kpi_data_g2.json", "r") as f:
        #     kpi_data_g2 = json.load(f)

        data = request.get_json()
        months = int(data.get("months", 12)) 
        api_key = data.get("api_key")
        if not api_key:
            return jsonify({"error": "API key is required"}), 400
        
        os.environ["DEEPSEEK_API_KEY"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key
        
        add_data_g1 = data.get("add_data_g1")
        add_data_g2 = data.get("add_data_g2")
        kpi_data_g1 = data.get("kpi_data_g1")
        kpi_data_g2 = data.get("kpi_data_g2")

        # Optional: validate these files exist and have expected structure
        if not all([add_data_g1, add_data_g2, kpi_data_g1, kpi_data_g2]):
            return jsonify({"error": "Missing one or more required data files"}), 400

        kpi_data_g1 = {
            "description": "Combined financial and transactional data.",
            "graph_data": kpi_data_g1,  # your first JSON block
            "additional_data": add_data_g1 # your second JSON block
        }



        kpi_data_g2 = {
            "description": "Combined financial and transactional data for Gross Profit, EBITDA, Net Income, Customer Payment Days, Supplier Payment Days.",
            "graph_data": kpi_data_g2,  # your first JSON block
            "additional_data": add_data_g2 # your second JSON block
        }









        def process_kpi_data(kpi_data, time_range_months):
            cutoff_date = datetime.today() - relativedelta(months=time_range_months)
            aggregated = {}

            for entry in kpi_data['graph_data']['data']:
                measure = entry['measure']
                monthly_amounts = defaultdict(float)

                for row in entry['sum_values']:
                    try:
                        date_obj = datetime.strptime(row['date'], "%d-%m-%Y")
                        if date_obj >= cutoff_date:
                            month_year = date_obj.strftime("%b-%Y")
                            monthly_amounts[month_year] += row['amount']
                    except Exception:
                        continue

                aggregated[measure] = sorted(
                    monthly_amounts.items(),
                    key=lambda x: datetime.strptime(x[0], "%b-%Y")
                )

            return aggregated





        kpi_data_g1_p = process_kpi_data(kpi_data_g1, months)
        kpi_data_g2_p = process_kpi_data(kpi_data_g2,months)


        kpi_data_g2_f = {
            "description": "Combined financial and transactional data for Gross Profit, EBITDA, Net Income, Customer Payment Days, Supplier Payment Days.",
            "graph_data": kpi_data_g2_p,  # your first JSON block
            "additional_data": add_data_g2 # your second JSON block
        }

        kpi_data_g1_f = {
            "description": "Combined financial and transactional data for Gross Profit, EBITDA, Net Income, Customer Payment Days, Supplier Payment Days.",
            "graph_data": kpi_data_g1_p,  # your first JSON block
            "additional_data": add_data_g1 # your second JSON block
        }


        # Agent 2: Analysis Agent
        # Single-KPI Analysis Agent
        Analysis_agent1 = Agent(
            name="Analysis Agent",
            role="Performs deep insight generation for a single financial KPI based on financial and transactional data",
            model=DeepSeekChat(),
            instructions = [f"""
            You are a financial analyst. You’ve received structured financial and transactional data from {kpi_data_g1_f}.

            Your role is to provide direct KPI insights in plain text. Do not describe your approach, process, or mention any code, tools, or next steps.

            1. Financial Trends
                - Commentate on the trend mentioning highs with value, lows and general direction. Mention the average and any outliers. 
                - Identify Spikes (value + dates)              
                - You must Explain your analysis through supporting transactional data. This will be the reason for the change / trend mentioned in your analysis.

            2. Transactional Correlation
                - Link KPI shifts with tagged transactional data
                - Mention hashed customer names
                - Example: Income peaked at $2,000 in May 2021 due to 100 new customers and higher invoice totals
                            
            3. Insight Output
                - For each KPI, provide:
                - Change value %
                - Professionally summarise the trend mentioning highs, lows and general direction. Mention the average and any outliers.
                - Transactional cause (figures + hashed customers) with dates that matches trend dates.
                - Format for Python’s `Display` function in markdown


            **Guidelines:**

            1. **Trend Analysis**:
            - Commentate on the trend mentioning highs, lows and general direction. Mention the average and any outliers.               
            - Use transactional data to explain causes (invoice count, totals, new customers, etc.).

            2. **KPI Breakdown**:
            - Income: Explain changes with invoice count and value, customer activity.
            - COS: Use supplier invoice totals, unit volume or price shifts.
            - Expenses: Breakdown by categories (e.g., Tech, Content) using tp_values and invoice totals.
            - Other Income: Link any spikes to known transactional records.

            3. **Correlate with Transactions**:
            - Use hashed customer names (e.g., Customer A, Supplier B).
            - Example: "Income peaked at $2,000 in May 2021 due to 100 new customers and higher invoice totals."

            4. **Root Cause**:
            - Only include causes proven by data. No assumptions.

            5. **Output Style**:
            - For each KPI:
                - Change in value or %
                - Commentate on the trend mentioning highs, lows and general direction. Mention the average and any outliers.               
                - You must Explain your analysis through supporting transactional data. This will be the reason for the change / trend mentioned in your analysis.
                - Dont use Sterics inless its a heading

            6. Report
            - Provide a clean, structured summary of insights across all KPIs 
            - Costumer Collection Days and Supplier Payment Days summary in tabular form.

            **Final Rules:**
            - Do not reference any KPI outside this set
            - Use only provided fields
            - Avoid code blocks, charts, or markdown formatting
            - Present in plain language
            - Dont use Sterics inless its a heading
            - Always identify peaks and troughs using exact numerical values from the data.
            - Use a sorting or max/min method to determine the true highest or lowest value for each KPI.
            - Do not estimate, infer, or guess trends—rely strictly on actual data values.
            - State both the exact value and the corresponding date/period.
            - Professionally summarise the trend mentioning highs, lows and general direction. Mention the average and any outliers.
            - Never round or modify values—report them as-is from the dataset.
            - Presentable format please
            - Make sure calculations are correct and accurate
            - Dont Break words or give wierd joined words
            - Dont Number the headings
            - Format for Markdown not in block.
            """],




            markdown=True,
            pip_install=False,
            structured_outputs=True,

        )





        # Single-KPI Analysis Agent
        Analysis_agent2 = Agent(
            name="Second Analysis Agent",
            role="Performs deep insight generation for a financial KPIs based on financial and transactional data",
            model=DeepSeekChat(),
            instructions = [f"""
            You are a finance and data analysis expert. You’ve received `data` (from {kpi_data_g2_f}) with:
            - Financial data (`graph_data`): Gross Profit, EBITDA, Net Income
            - Operational data (`additional_data`): Customer and Supplier payment days

            **Your Task:** Analyze KPI trends for Gross Profit, EBITDA, Net Income, and payment behavior metrics (Customer Collection Days, Supplier Payment Days). Use only data-backed explanations. No code, tools, or recommendations.

            **Workflow:**


            1. Financial Trends
            - Track KPI trends over time
            - Commentate on the trend mentioning highs, lows and general direction. Must Mention the average and any outliers. 


            2. Trend Analysis
            - Gross Profit, EBITDA, Net Income: Commentate on the trend mentioning highs, lows and general direction. Mention the average and any outlier, relate to operational or financial causes 
            - Commentate on the trend mentioning highs, lows and general direction. Mention the average and any outliers. 
            - Customer Collection Days & Supplier Payment Days:
            - For customer Collection Days and Supplier Payment Days, Use values ONLY from `scaled_avg_invoice_day` and `scaled_avg_due_day` in `tp_list` and `cp_list`
            - Do NOT use `formula_invoice_day` or `formula_dues_day`
            - `scaled_avg_invoice_day`: Avg days it takes to pay after invoice is issued
            - `scaled_avg_due_day`: Avg days payment is made after due date
            - For each `contact_id_name`, report both metrics
            - Example for Customer Collection Days: 
                - "Customer B usually paid invoices 13.6 days after issue, with no delay past due date"
                - "Investment Bank had an average delay of 10 days after due date"            
                - "Investment Bank typically paid invoices 11 days after issue, with payments delayed by an average of 10 days beyond the due date".
            - Example for Supplier Payment Days:
                - "Tax Consultants typically paid invoices 18 days after they were issued, with no delay past the due date."
                - "Marketing Experts had payments delayed by an average of 24.2 days beyond the due date."


            3. Root Cause
            - Identify and explain changes based on volume, timing, or activity metrics
            - You are responsible for analyzing key profitability metrics: Gross Profit, EBITDA, and Net Income. Use the provided KPI data to explain changes in these metrics with proper financial reasoning. You can derive them as follows:
                - Gross Profit = Income − Cost of Sales (CoS)
                - EBITDA = Gross Profit + Other Income − Expenses
                - Net Income = EBITDA (assuming no tax, depreciation, or interest in this dataset)
            - You must Explain your analysis through supporting transactional data {kpi_data_g1_f}. This will be the reason for the change / trend mentioned in your analysis:
                - Income
                - Cost of Sales
                - Expenses
                - Other Income
            - For each insight, break down why a change occurred, e.g., a drop in gross profit due to reduced income or increased CoS, or EBITDA being affected by a spike in expenses or dip in other income.

            4. Insight Output
            - For each KPI:
            - Change value/%
            - Commentate on the trend mentioning highs, lows and general direction. Mention the average and any outliers. 
            - Data-backed reason

            5. Report
            - Provide a clean, structured summary of insights across all KPIs 
            - Costumer Collection Days and Supplier Payment Days summary in tabular form.

            **Final Rules:**
            - Do not reference any KPI outside this set
            - Use only provided fields
            - Avoid code blocks, charts, or markdown formatting
            - Present in plain language
            - Dont use Sterics inless its a heading
            - Presentable format please
            - Make sure calculations are correct and accurate
            - Dont Break words or give weird joined words
            - Dont Number the headings
            """],


            markdown=True,
            pip_install=False,
            structured_outputs=True,

        )


        def run_agent(agent):
            result = agent.run()
            content = getattr(result, 'content', str(result))
            return content  # <-- return the content string
        


        agents = [Analysis_agent1, Analysis_agent2]



        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(run_agent, agents))




        end_time = time.time()

        







        return jsonify({
            "agents_result": results,
            "duration_seconds": round(end_time - start_time,2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
