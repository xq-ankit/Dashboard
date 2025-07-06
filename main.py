from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_username():
    return os.getlogin().lower()
    
def get_full_display_name():
    username = os.getlogin()
    try:
        result = subprocess.run(
            ['powershell', '-Command', f"(Get-LocalUser -Name '{username}').FullName"],
            capture_output=True,
            text=True
        )
        full_name = result.stdout.strip()
        return full_name if full_name else username
    except Exception:
        return username

@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/api/dashboard/1")
def dashboard_1():
    try:
        # Correct header row (4th row, index 3)
        df = pd.read_excel('dashboard1.xlsx', sheet_name='Sheet1', header=3)

        # Filter relevant columns and drop rows with missing data
        df = df[['Employee Name', 'WFO']].dropna()

        # Convert WFO safely to numeric
        df['WFO'] = pd.to_numeric(df['WFO'], errors='coerce')
        df = df.dropna(subset=['WFO'])

        # Sum total WFO per employee
        total_wfo = df.groupby('Employee Name')['WFO'].sum().reset_index()

        # Match current user
        user = get_username()
        matched = total_wfo[
            total_wfo['Employee Name']
            .str.replace(" ", "")
            .str.lower()
            .str.contains(user)
        ]

        if not matched.empty:
            employee = matched.iloc[0]
            return {
                "employee": employee['Employee Name'],
                "wfo_count": int(employee['WFO'])
            }
        else:
            return JSONResponse(
                content={"error": f"No WFO data found for user: {user}"},
                status_code=404
            )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/api/dashboard/2")
def dashboard_2():
    try:
        df = pd.read_excel('dashboard2.xlsx', sheet_name='Sheet2', skiprows=2)
        df.dropna(how='all', inplace=True)

        user = get_username()
        current_name = None
        leave_data = {}

        for _, row in df.iterrows():
            row_label = str(row[0]).strip()

            if row_label.lower() == "grand total":
                continue

            if "leave" not in row_label.lower() and not row_label.lower().startswith("total"):
                current_name = row_label
                if user in current_name.lower().replace(" ", ""):
                    leave_data['employee'] = current_name
                    leave_data['leaves'] = {}
            elif current_name and 'employee' in leave_data and current_name == leave_data['employee']:
                leave_type = row[0]
                taken = row[1]
                available = row[2]
                if pd.notna(taken) and pd.notna(available):
                    leave_data['leaves'][leave_type] = {
                        'taken': float(taken),
                        'available': float(available)
                    }

        if 'leaves' in leave_data:
            total_taken = sum(v['taken'] for v in leave_data['leaves'].values())
            total_available = sum(v['available'] for v in leave_data['leaves'].values())
            leave_data['summary'] = {
                "total_taken": total_taken,
                "total_available": total_available
            }

        return leave_data if leave_data else JSONResponse(
            content={"error": f"No leave data found for user: {user}"}, status_code=404
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

from fastapi.responses import JSONResponse
import pandas as pd

@app.get("/api/dashboard/3")
def dashboard_3():
    try:
        df = pd.read_excel("dashboard3.xlsx", sheet_name=0, header=0)

        # Keep only necessary columns and drop rows with missing data
        df = df[['name_fam_full', 'client_suffix', 'hours']].dropna()
        df['client_suffix'] = pd.to_numeric(df['client_suffix'], errors='coerce')
        df['hours'] = pd.to_numeric(df['hours'], errors='coerce')
        df = df.dropna(subset=['client_suffix', 'hours'])

        # Filter only client_suffix = 34
        df = df[df['client_suffix'] == 34]

        # Get full display name (PowerShell) and normalize spacing/lowercase
        user = get_full_display_name().strip().lower().replace(" ", "")

        # Match against `name_fam_full` directly
        matched = df[
            df['name_fam_full']
            .astype(str)
            .str.lower()
            .str.replace(" ", "")
            .str.contains(user)
        ]

        if matched.empty:
            return JSONResponse(
                content={"error": f"No billable hours found for user: {user}"},
                status_code=404
            )

        total_hours = matched['hours'].sum()
        matched_name = matched.iloc[0]['name_fam_full']

        return {
            "employee": matched_name,
            "total_billable_hours": round(total_hours, 2)
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
