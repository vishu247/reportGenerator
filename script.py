import requests
import json
from datetime import datetime, timedelta
import boto3
import os
from dotenv import load_dotenv
import yaml
import subprocess
from jinja2 import Template

load_dotenv()


#Get the current date and time
current_date_time = datetime.now()

# Get the current date
Today_date = current_date_time.date()
LastDaySprintCronExecuteDate = current_date_time.date()

RECIEVER = os.getenv("MAIL")
SENDER = os.getenv("SENDER")


#Git-Hub access token
TOKEN = os.getenv("GIT_HUB_TOKEN")

#Project node ID
PROJECT_NODE_ID = os.getenv("PROJECT_NODE_ID")

#Final Data store
final_data = {
    "Done": {
        "ENTT:": {},
        "INFRA:": {},
        "INTT:": {},
        "TASK:": {},
        "SRE:": {},
        "SMAR:": {}
    },
    "Under Review": {
        "ENTT:": {},
        "INFRA:": {},
        "INTT:": {},
        "TASK:": {},
        "SRE:": {},
        "SMAR:": {}
    },
}

#Final Efforts stores
final_effort = {
    "Done": {
        "ENTT:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "INFRA:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "INTT:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "TASK:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "SRE:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "SMAR:": {
            "Estimate": 0,
            "FinalEffort": 0
        }

    },
    "Under Review":{
        "ENTT:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "INFRA:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "INTT:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "TASK:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "SRE:": {
            "Estimate": 0,
            "FinalEffort": 0
        },
        "SMAR:": {
            "Estimate": 0,
            "FinalEffort": 0
        }
    }
}

assigneeReport={}

# Define the YAML content as a string
mail_content = f"""
mail:
  - {RECIEVER}
SENDER_MAIL: {SENDER}
"""

#Fetch all the ticket description
def run_gh_command(owner, project_item_list, limit):
    gh_command = f'gh project item-list {project_item_list} --owner {owner} --limit {limit} --format json'
    full_command = f'{gh_command}'
    try:
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Command output: {e.stdout}")
        return None

#Fetch current iteration id,title,dt_name
def get_current_iteration_id(LastDaySprintCronExecuteDate):
    query = f'''
    query {{
      node(id:"{PROJECT_NODE_ID}") {{
        ... on ProjectV2 {{
          fields(first: 20) {{
            nodes {{
              ... on ProjectV2IterationField {{
                id
                name
                configuration {{
                  iterations {{
                    startDate
                    id
                    title
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    '''

    print(TOKEN)
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
    }

    payload = {'query': query}
    current_iteration_value = []
    try:
        print("now trying to hit the graphql api")
        print(headers)
        print(json)
        response = requests.post('https://api.github.com/graphql', headers=headers, json=payload)
        print("successfully get the response")
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        print("Successfully get the data")

        iterations = data['data']['node']['fields']['nodes']
        iteration_year_name = data.get('data', {}).get('node', {}).get('fields', {}).get('nodes', [{}])[8].get('name')        
        current_date = datetime.now()

        # Find the current iteration
        for iteration in iterations:
            if 'configuration' in iteration and 'iterations' in iteration['configuration']:
                for current_iteration in iteration['configuration']['iterations']:

                    start_date = datetime.strptime(current_iteration['startDate'], "%Y-%m-%d")
                    # Calculate the end date (2 weeks after the start date)
                    end_date = start_date + timedelta(weeks=2)
                    LastDaySprintCronExecuteDate=(start_date+timedelta(days=13)).date()
                    # Check if the current date is within the iteration
                    if start_date <= current_date <= end_date:
                        current_iteration_value.append(iteration_year_name)
                        current_iteration_value.append(current_iteration['title'])
                        current_iteration_value.append(current_iteration['id'])
                        current_iteration_value.append(LastDaySprintCronExecuteDate)

                        return current_iteration_value
                        
    except requests.RequestException as e:
        print(f"Error making GraphQL request: {e}")
    except KeyError as e:
        print(f"Error extracting data from GraphQL response: {e}")

    return None

#Fetch the current iteration data which are done and under review state and store in JSON DB
def create_iteration_data(project_data, current_iterationID_title):
    items = project_data.get('items', [])  # Get the 'items' list, default to empty list if key does not exist
    for item in items:
        iteration_dt=item.get("d"+current_iterationID_title[0][1:])
        if iteration_dt:
            if iteration_dt.get('title') == current_iterationID_title[1]:

                task_data={}
                task_data.update({"Title": item.get('title')})
                task_data.update({"Assignees": item.get('assignees')})
                task_data.update({"Original_Effort": item.get('estimate')})
                task_data.update({"Final_Effort": item.get('final Efforts')})


                if item.get('assignees'):
                    assignee_key = item.get('assignees')
                    for assignee_data in assignee_key:
                        if assignee_data not in assigneeReport:
                            assigneeReport[assignee_data] = {
                                'completedTicket': 0,
                                'CompletedEstimatedEffort': 0,
                                'CompletedFinalEffort': 0,
                                'CompletedEstimatedFinaldrift': 0.0,
                                'IncompleteEstimatedEffort': 0, 
                                'IncompleteTickets': 0
                            }
                        if item.get('status') in ["Done", "Under Review"]:  
                            assigneeReport[assignee_data]['completedTicket']+=1
                            assigneeReport[assignee_data]['CompletedEstimatedEffort']+= ( item.get('estimate') or 0 )
                            assigneeReport[assignee_data]['CompletedFinalEffort']+= ( item.get('final Efforts') or 0 )
                            if assigneeReport[assignee_data]['CompletedEstimatedEffort'] != 0:
                                assigneeReport[assignee_data]['CompletedEstimatedFinaldrift']=round((((assigneeReport[assignee_data]['CompletedFinalEffort'] - assigneeReport[assignee_data]['CompletedEstimatedEffort'] )/(assigneeReport[assignee_data]['CompletedEstimatedEffort']  )) * 100),2)
                            # assigneeReport[assignee_data]['CompletedEstimatedFinaldrift']+=(((item.get('final Efforts') or 0) - ( item.get('estimate') or 0 ) )/(item.get('estimate'))) * 100
                        else:
                            assigneeReport[assignee_data]['IncompleteTickets']+=1
                            assigneeReport[assignee_data]['IncompleteEstimatedEffort']+= ( item.get('estimate') or 0 )
                if item.get('assignees') != None and item.get('status') in ["Done", "Under Review"]:      
                    final_data.get(item.get('status')).get(item.get('title').split()[0]).update({item.get('content').get('number'): task_data })
                    final_effort[item.get('status')][item.get('title').split()[0]]["Estimate"]=final_effort.get(item.get('status')).get(item.get('title').split()[0]).get('Estimate')+item.get('estimate')
                    final_effort[item.get('status')][item.get('title').split()[0]]["FinalEffort"]=final_effort.get(item.get('status')).get(item.get('title').split()[0]).get('FinalEffort')+( item.get('final Efforts') or 0  )


            
                
               
# Send the mail to the assignee
def send_email(body):
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region_name = os.getenv("AWS_REGION")

    # Loading email from yaml files
    emails = yaml.safe_load(mail_content)

    assignee_emails = emails.get('mail')

    # Getting sender's email from yaml
    sender_email = emails.get("SENDER_MAIL", '')

    ses_client = boto3.client('ses', aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key,region_name=region_name)

    for mail in assignee_emails:
        to_email = mail
        subject = f"Sprint Report Summary "
        try:
            response = ses_client.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [to_email],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': 'UTF-8',
                            'Data': body,
                        },
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': subject,
                    },
                }
            )
            print(f"Email sent to {to_email} successfully. Message ID: {response['MessageId']}")
        except Exception as e:
            print(f"Error sending email to {to_email}: {str(e)}")




def main():
    print(os.getenv("GIT_HUB_TOKEN"))
    print(os.getenv("AWS_SECRET_ACCESS_KEY"))
    print(os.getenv("LIMIT"))
    print(os.getenv("PROJECT"))
    print(os.getenv("REPO"))
    print(os.getenv("SENDER"))
    print(os.getenv("AWS"))
    print(os.getenv("MAIL"))
    print(os.getenv("AWS_REGION"))
    print(os.getenv("AWS_ACCESS_KEY_ID"))
    print(os.getenv("PROJECT_NODE_ID"))
    
    


    global PROJECT_NODE_ID, TOKEN

    #load the project node id and github token from the .env file
    PROJECT_NODE_ID = os.getenv("PROJECT_NODE_ID")
    TOKEN = os.getenv("GIT_HUB_TOKEN")
    owner_name = os.getenv("REPO")

    #project number
    item_list_number = os.getenv("PROJECT")

    #limit to fetch the data by gh command
    limit = os.getenv("LIMIT")

    print(LastDaySprintCronExecuteDate)
    current_iterationID_title = get_current_iteration_id(LastDaySprintCronExecuteDate)
    if current_iterationID_title[3]!=Today_date:
        print("not today")
        # return

    subprocess.run(['gh', 'auth', 'login', '--with-token'], input=TOKEN, text=True, capture_output=True)

    project_data = run_gh_command(owner_name, item_list_number, limit)

    if project_data:
        if current_iterationID_title:
            create_iteration_data(project_data, current_iterationID_title)
        else:
            print("No active iteration found.")
    else:
        print("Error in fetching project data.")


    # Define HTML template for mail
    html_template = """
    <html>
    <head>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 2px solid  #A9A9A9;
                text-align: left;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        {% for status, categories in data.items() %}
            <h1 style="text-align: center;"><u>Task {{ status }}  </u></h1>
            <table>
                <tbody>
                    {% for category, tasks in categories.items() %}
                    {% set category_length = category|length %}
                    <tr>
                        <th colspan="5" >{{ category }}</th>
                    </tr>
                    <tr>
                        <th style="text-align: center;">Task ID</th>
                        <th>Title</th>
                        <th>Assignee</th>
                        <th style="text-align: center;">Original Effort</th>
                        <th style="text-align: center;">Final Effort</th>
                    </tr>
                    {% for task_id, task_details in tasks.items() %}
                    <tr>
                        <td style="text-align: center;" >{{ task_id }}</td>
                        <td>{{ task_details['Title'][category_length+1:] }}</td>
                        <td>{{ ', '.join(task_details['Assignees']) }}</td>
                        <td style="text-align: center;">{{ task_details['Original_Effort'] }}</td>
                        <td style="text-align: center;">{{ task_details['Final_Effort'] }}</td>
                    </tr>
                    {% endfor %}
                    <tr>
                        <th colspan="3" style="text-align: center;"> TOTAL </th>
                        <th style="text-align: center;">  {{ duration[status][category]['Estimate'] }} </th>
                        <th style="text-align: center;">  {{ duration[status][category]['FinalEffort'] }} </th>
                    </tr>
                    <tr style="height: 50px">
                        <td colspan="5">  </td>
                    </tr>                    
                    {% endfor %}
                </tbody>
            </table>
        {% endfor %}

        <h1 style="text-align: center;"><u> Sprint Report by Individual Assignee </u></h1>

        <table>
            <tbody>
                <tr>
                    <th style="text-align: center;">Assignee</th>
                    <th style="text-align: center;">Incomplete Estimated Effort</th>
                    <th style="text-align: center;">Incomplete Tickets</th>
                    <th style="text-align: center;">Completed Estimated Effort</th>
                    <th style="text-align: center;">Completed Final Effort</th>
                    <th style="text-align: center;">Completed Estimated Final drift</th>
                    <th style="text-align: center;">Completed Ticket</th>
                </tr>
                {% for member_name, member_progress in assigneeReport.items() %}
                    <tr>
                        <td style="text-align: center;">{{ member_name }}</td>
                        <td style="text-align: center; background-color: #FFCCCC;"><b>{{ member_progress['IncompleteEstimatedEffort'] }}</b></td>
                        <td style="text-align: center; background-color: #FFCCCC;"> <b>{{ member_progress['IncompleteTickets'] }}</b> </td>
                        <td style="text-align: center;">{{ member_progress['CompletedEstimatedEffort'] }}</td>
                        <td style="text-align: center;">{{ member_progress['CompletedFinalEffort'] }}</td>
                        <td style="text-align: center;">{{ member_progress['CompletedEstimatedFinaldrift'] }} % </td>
                        <td style="text-align: center; ">{{ member_progress['completedTicket'] }}</td>                        
                    <tr>
                {% endfor %}
            </tbody>
        </table>
        
     
    </body>
    </html>
    """

    # Render HTML template with data
    template = Template(html_template)
    body_html = template.render(data=final_data,duration=final_effort,assigneeReport=assigneeReport)

    #call the send mail function
    send_email(body_html)
 

if __name__ == "__main__":
    main()
